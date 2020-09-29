#  Copyright (C) AI Power - All Rights Reserved
#  Unauthorized copying of this file, via any medium is strictly prohibited
#  Proprietary and confidential
#  Written by AI Power, January 2020

import datetime
import os
import time
from collections import Counter
from threading import Lock, Thread

import cv2
import numpy as np
import tensorflow as tf
from PIL import Image

from config.settings import log
from ocr_worker.utils.common import get_max_bbox_area, load_graph
from ocr_worker.utils.crnn_recognizer import decoder_output_to_text, get_input_boxes_recognition, preprcess_data
from ocr_worker.utils.yolov3_detector import (
    convert_to_original_size, get_boxes_and_inputs_detection, letter_box_image,
    non_max_suppression,
)
from ocr_worker.video_source import close_frame, show_frame, VideoSource
from utils.container_code_util import ContainerCodeUtil
from utils.static_util import StaticUtil

from ocr_worker.utils.tesseract_recognizer import tesseract_text_recognize
SIZE = 416, 416
CONF_THRESHOLD = 0.5
IOU_THRESHOLD = 0.4

# Thời gian tối đa trong 1 lượt container
# (từ lúc bắt đầu xuất hiện container tới lúc không còn container đó trong frame hình nữa)
TIME_PER_TURN = 10
MAX_FRAME_PER_TURN = 25

# Thời gian tối đa được phép không detect ra mà vẫn được tính cùng 1 lượt container
TRACKING_TIME = 1


def detect(
        ocr_frame_rgb, boxes, inputs,
        detector_sess, detector_sess_lock,
):
    ocr_frame_rgb = Image.fromarray(ocr_frame_rgb)
    img_resized = letter_box_image(ocr_frame_rgb, *SIZE, 128)
    img_resized = img_resized.astype(np.float32)

    with detector_sess_lock:
        detected_boxes = detector_sess.run(
            boxes, feed_dict={inputs: [img_resized]},
        )

    filtered_boxes = non_max_suppression(
        detected_boxes,
        confidence_threshold=CONF_THRESHOLD,
        iou_threshold=IOU_THRESHOLD,
    )
    final_box = []
    for cls, bboxs in filtered_boxes.items():
        for box, score in bboxs:
            final_box.append(convert_to_original_size(box, SIZE, np.array(ocr_frame_rgb.size), True))

    return final_box


def recognize(
        ocr_frame_rgb):
    ocr_frame_rgb = cv2.cvtColor(ocr_frame_rgb, cv2.COLOR_RGB2BGR)
    tess = tesseract_text_recognize()
    text = tess.recognize_image(tess.preprocess_image(ocr_frame_rgb))
    return text

def recognize_images(
        ocr_frames_rgb, positions, feature_inputs,
        feature_sess, feature_sess_lock,
        ctc_graph, ctc_sess, ctc_sess_lock,
):
    texts = []
    inout = 0

    try:
        first_center = positions[0]
        last_center = positions[-1]
        if first_center[1] < last_center[1]:
            inout = -1
        elif first_center[1] > last_center[1]:
            inout = 1
    except Exception as exc:
        log.exception(f'OCR::rec_images - check if in or out failed: {exc}')

    # loc bot hinh
    n_frame = len(ocr_frames_rgb)
    if n_frame > MAX_FRAME_PER_TURN:
        step = float(n_frame) / MAX_FRAME_PER_TURN
        used_frames = [
            ocr_frames_rgb[int(round(i * step))]
            for i in range(0, MAX_FRAME_PER_TURN)
        ]
    else:
        used_frames = ocr_frames_rgb

    recognized_frames_rgb = []
    for index, ocr_frame_rgb in enumerate(used_frames):
        try:
            text_label = recognize(ocr_frame_rgb)
            texts.append(text_label)
            recognized_frames_rgb.append(ocr_frame_rgb)
        except Exception as exc:
            log.exception(
                f'OCR::rec_images - '
                f'recognize image with shape {ocr_frame_rgb.shape} failed: {exc}'
            )
    counter =  Counter(texts)
    text = max(counter, key=counter.get)
    id_from_array = texts.index(text)
    return text, recognized_frames_rgb[id_from_array], id_from_array, inout


class OCRWorker:
    detector_graph = None
    detector_graph_params = None
    detector_sess = None
    detector_sess_lock = None

    feature_graph = None
    feature_graph_params = None
    feature_sess = None
    feature_sess_lock = None

    ctc_graph = None
    ctc_sess = None
    ctc_sess_lock = None

    graph_config = None

    def __init__(
            self,
            worker_config,
            ocr_vidsrc,
            left_vidsrc=None,
            right_vidsrc=None,
            front_vidsrc=None,
    ):
        self.worker_config = worker_config
        self.ocr_camera_source: VideoSource = ocr_vidsrc
        self.left_camera_source: VideoSource = left_vidsrc
        self.right_camera_source: VideoSource = right_vidsrc
        self.front_camera_source: VideoSource = front_vidsrc

        self.enable = True

        self.__class__.prepare()

    def start(self):
        # Khởi động ocr camera lên
        try:
            self.ocr_camera_source.start()
        except Exception as exc:
            from container.models import Camera
            ocr_camera = Camera.objects.get(camera_id=self.worker_config.ocr_camera.camera_id)
            ocr_camera.status = 0
            ocr_camera.save()
            raise IOError(
                f'OCRWorker::start error'
                f' - could not access ocr camera [{ocr_camera}] - {exc}'
            )

        # Khởi động các camera các hướng lên
        # noinspection PyBroadException
        try:
            if self.left_camera_source is not None:
                self.left_camera_source.start()
        except Exception:
            pass
        # noinspection PyBroadException
        try:
            if self.right_camera_source is not None:
                self.right_camera_source.start()
        except Exception:
            pass
        # noinspection PyBroadException
        try:
            if self.front_camera_source is not None:
                self.front_camera_source.start()
        except Exception:
            pass

        # Tạo thread chạy
        worker_thread = Thread(target=self._worker_loop)
        worker_thread.daemon = True
        worker_thread.start()

    def stop(self):
        self.enable = False

    def _worker_loop(self):
        log.debug(f'OCRWorker for camera [{self.worker_config.ocr_camera}] starting...')
        frame_title = f'{self.worker_config.ocr_camera.camera_id}'

        io_turn_trace_ocr_imgs = []
        io_turn_trace_back_imgs = []
        io_turn_trace_front_imgs = []
        io_turn_trace_left_imgs = []
        io_turn_trace_right_imgs = []
        io_turn_trace_positions = []
        first_appear_time = 0
        first_appear_datetime = None
        last_appear_time = 0

        cur_fnum = -1

        while self.enable:
            try:
                t0 = time.time()
                log.debug(
                    f'- OCRWorker [{self.worker_config.ocr_camera.camera_id}] - '
                    f'Lần {t0:.1f}:'
                )
                ocr_frame, fnum = self.ocr_camera_source.read()
                if ocr_frame is None or cur_fnum == fnum:
                    log.debug(
                        f'  + OCRWorker [{self.worker_config.ocr_camera.camera_id}] - '
                        f'Read camera frame = None, continue'
                    )
                    time.sleep(0.1)
                    continue
                cur_fnum = fnum
                front_frame, _ = self.front_camera_source.read() if self.front_camera_source is not None else None, -1
                left_frame, _ = self.left_camera_source.read() if self.left_camera_source is not None else None, -1
                right_frame, _ = self.right_camera_source.read() if self.right_camera_source is not None else None, -1

                ocr_frame_rgb = cv2.cvtColor(ocr_frame, cv2.COLOR_BGR2RGB)

                # Detect container trong frame hình
                bboxes = detect(
                    ocr_frame_rgb, *self.__class__.detector_graph_params,
                    self.__class__.detector_sess, self.__class__.detector_sess_lock,
                )

                # Chọn container bbox phù hợp để xử lý
                id_bbox, _ = get_max_bbox_area(bboxes)
                accepted_bbox = bboxes[id_bbox] if id_bbox != -1 else None

                # Nếu không có container bbox nào phù hợp để xử lý
                if accepted_bbox is None:
                    # Nếu không có container bbox nào phù hợp để xử lý
                    # mà tracking_list rỗng thì bỏ qua
                    if first_appear_time == 0:
                        log.debug(
                            f'  + OCRWorker [{self.worker_config.ocr_camera.camera_id}] - '
                            f'Detect không ra, bỏ qua'
                        )
                        fps = _calc_fps(t0)
                        _draw_fps(ocr_frame, fps)
                        show_frame(frame_title, ocr_frame)
                        continue

                    # Nếu không có container bbox nào phù hợp để xử lý
                    # mà đang track và vẫn nằm trong thời gian track cho phép thì chờ xuất hiện lại
                    if t0 - last_appear_time < TRACKING_TIME and t0 - first_appear_time < TIME_PER_TURN:
                        log.debug(
                            f'  + OCRWorker [{self.worker_config.ocr_camera.camera_id}] - '
                            f'Detect không ra, vẫn còn trong thời gian track cho phép, bỏ qua'
                        )
                        fps = _calc_fps(t0)
                        _draw_fps(ocr_frame, fps)
                        show_frame(frame_title, ocr_frame)
                        continue

                    # Nếu không có container bbox nào phù hợp để xử lý
                    # mà đang track và đã quá thời gian track cho phép thì xử lý lượt track này
                    log.debug(
                        f'  + OCRWorker [{self.worker_config.ocr_camera.camera_id}] - '
                        f'Detect không ra, hết thời gian track cho phép, '
                        f'xử lý list {len(io_turn_trace_ocr_imgs)} hình track'
                    )
                    Thread(
                        target=self._process_turn,
                        args=(
                            io_turn_trace_ocr_imgs, io_turn_trace_positions, datetime.datetime.now(),
                        ),
                        kwargs={
                            'back_frames': io_turn_trace_back_imgs,
                            'front_frames': io_turn_trace_front_imgs,
                            'left_frames': io_turn_trace_left_imgs,
                            'right_frames': io_turn_trace_right_imgs,
                        },
                    ).start()

                    first_appear_time = 0
                    first_appear_datetime = None
                    last_appear_time = 0
                    io_turn_trace_ocr_imgs = []
                    io_turn_trace_back_imgs = []
                    io_turn_trace_front_imgs = []
                    io_turn_trace_left_imgs = []
                    io_turn_trace_right_imgs = []
                    io_turn_trace_positions = []

                    fps = _calc_fps(t0)
                    _draw_fps(ocr_frame, fps)
                    show_frame(frame_title, ocr_frame)
                    continue

                # Crop frame hình, chỉ lấy phần bbox của container sẽ xử lý thôi
                x1, y1, x2, y2 = int(accepted_bbox[0]), int(accepted_bbox[1]), int(accepted_bbox[2]), int(
                    accepted_bbox[3])
                x1 = x1 - 20
                center = x1 + (x2 - x1) / 2, y1 + (y2 - y1) / 2
                cropped_image = ocr_frame_rgb.copy()[y1:y2, x1:x2]

                # Kiểm tra nếu đây là lần đầu xuất hiện của lượt
                if first_appear_time == 0:
                    log.debug(
                        f'  + OCRWorker [{self.worker_config.ocr_camera.camera_id}] - '
                        f'Lần đầu xuất hiện, set biến first_appear và last_appear'
                    )
                    first_appear_time = t0
                    first_appear_datetime = datetime.datetime.now()
                    last_appear_time = t0
                    io_turn_trace_ocr_imgs.append(cropped_image)
                    io_turn_trace_back_imgs.append(np.array(ocr_frame, copy=True))
                    io_turn_trace_front_imgs.append(front_frame)
                    io_turn_trace_left_imgs.append(left_frame)
                    io_turn_trace_right_imgs.append(right_frame)
                    io_turn_trace_positions.append(center)

                    fps = _calc_fps(t0)
                    _draw_fps(ocr_frame, fps)
                    show_frame(frame_title, ocr_frame)
                    continue

                # Kiểm tra có còn đủ điều kiện nằm trong lượt track hay không
                if t0 - last_appear_time < TRACKING_TIME and t0 - first_appear_time < TIME_PER_TURN:
                    log.debug(
                        f'  + OCRWorker [{self.worker_config.ocr_camera.camera_id}] - '
                        f'Phát hiện, còn trong track time, add frame vào'
                    )
                    io_turn_trace_ocr_imgs.append(cropped_image)
                    io_turn_trace_back_imgs.append(np.array(ocr_frame, copy=True))
                    io_turn_trace_front_imgs.append(front_frame)
                    io_turn_trace_left_imgs.append(left_frame)
                    io_turn_trace_right_imgs.append(right_frame)
                    io_turn_trace_positions.append(center)
                    last_appear_time = t0

                    fps = _calc_fps(t0)
                    _draw_fps(ocr_frame, fps)
                    show_frame(frame_title, ocr_frame)
                    continue

                log.debug(
                    f'  + OCRWorker [{self.worker_config.ocr_camera.camera_id}] - '
                    f'Detect không ra, hết thời gian track cho phép, '
                    f'xử lý list {len(io_turn_trace_ocr_imgs)} hình track'
                )
                Thread(
                    target=self._process_turn,
                    args=(
                        io_turn_trace_ocr_imgs, io_turn_trace_positions, first_appear_datetime,
                    ),
                    kwargs={
                        'back_frames': io_turn_trace_back_imgs,
                        'front_frames': io_turn_trace_front_imgs,
                        'left_frames': io_turn_trace_left_imgs,
                        'right_frames': io_turn_trace_right_imgs,
                    },
                ).start()

                first_appear_time = 0
                first_appear_datetime = None
                last_appear_time = 0
                io_turn_trace_ocr_imgs = []
                io_turn_trace_back_imgs = []
                io_turn_trace_front_imgs = []
                io_turn_trace_left_imgs = []
                io_turn_trace_right_imgs = []
                io_turn_trace_positions = []

                fps = _calc_fps(t0)
                _draw_fps(ocr_frame, fps)
                show_frame(frame_title, ocr_frame)
                continue

            except Exception as exc:
                import traceback
                log.debug(
                    f'  + OCRWorker [{self.worker_config.ocr_camera.camera_id}] - '
                    f'worker loop bị lỗi: {traceback.format_tb(exc.__traceback__)}',
                )
                continue

        close_frame(frame_title)

    def _process_turn(
            self, turn_imgs, positions, io_time,
            back_frames=None, front_frames=None, left_frames=None, right_frames=None,
    ):
        # tesseract_text_recognize.preprocess_image()


        text_label, label_image, img_index, inout = recognize_images(
            turn_imgs, positions, self.__class__.feature_graph_params,
            self.__class__.feature_sess, self.__class__.feature_sess_lock,
            self.__class__.ctc_graph, self.__class__.ctc_sess, self.__class__.ctc_sess_lock,
        )
        label_image = label_image[:, :, ::-1].copy()
        self.save_db(
            label_image, text_label, inout=inout, io_time=io_time,
            back_frame=back_frames[img_index] if back_frames is not None else None,
            front_frame=front_frames[img_index] if front_frames is not None else None,
            left_frame=left_frames[img_index] if left_frames is not None else None,
            right_frame=right_frames[img_index] if right_frames is not None else None,
        )
        log.debug(
            f'  + OCRWorker [{self.worker_config.ocr_camera.camera_id}] - '
            f'xử lý xong ({text_label}), '
            f'lưu db thành công'
        )

    def save_db(
            self, ocr_frame, text_labels, inout=0, io_time=None,
            back_frame=None, front_frame=None, left_frame=None, right_frame=None,
    ):
        from container.models import InOutHistory

        container_code, container_length, container_height = ContainerCodeUtil.extract_info(
            text_labels,
        )

        io_history = InOutHistory(
            history_datetime=io_time if io_time is not None else datetime.datetime.now(),
            inout=inout,
            container_code=container_code,
            container_length=container_length,
            container_height=container_height,
            container_str=text_labels,
            captured_images={},
            ocr_camera=self.worker_config.ocr_camera,
            front_camera=self.worker_config.front_camera,
            left_camera=self.worker_config.left_camera,
            right_camera=self.worker_config.right_camera,
        )
        io_history.save()
        _, ocr_image_name = StaticUtil.save_image(
            ocr_frame,
            io_history.history_id,
            name_prefix='ocr_',
        )
        _, back_image_name = StaticUtil.save_image(
            back_frame,
            io_history.history_id,
            name_prefix='back_',
        )
        _, front_image_name = StaticUtil.save_image(
            front_frame,
            io_history.history_id,
            name_prefix='front_',
        ) if front_frame is not None else None, None
        _, left_image_name = StaticUtil.save_image(
            left_frame,
            io_history.history_id,
            name_prefix='left_',
        ) if left_frame is not None else None, None
        _, right_image_name = StaticUtil.save_image(
            right_frame,
            io_history.history_id,
            name_prefix='right_',
        ) if right_frame is not None else None, None
        io_history.captured_images = {
            'ocr_image': ocr_image_name,
            'back_image': back_image_name,
            'front_image': front_image_name,
            'left_image': left_image_name,
            'right_image': right_image_name,
        }
        io_history.save()

    @classmethod
    def prepare(cls):
        if cls.detector_graph is not None:
            return

        # Tạo config chung cho các session
        cls.graph_config = tf.compat.v1.ConfigProto(
            gpu_options=tf.compat.v1.GPUOptions(per_process_gpu_memory_fraction=0.25),
            log_device_placement=False,
        )

        # Chuẩn bị detector
        cls.detector_graph = load_graph(
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'models', 'detector.pb'),
        )
        cls.detector_graph_params = get_boxes_and_inputs_detection(cls.detector_graph)
        cls.detector_sess = tf.compat.v1.Session(
            graph=cls.detector_graph,
            config=cls.graph_config,
        )
        cls.detector_sess_lock = Lock()

        # Chuẩn bị feature graph cho recognizer
        cls.feature_graph = load_graph(
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'models', 'recognizer.pb'),
        )
        cls.feature_graph_params = list(get_input_boxes_recognition(cls.feature_graph))
        cls.feature_sess = tf.compat.v1.Session(
            graph=cls.feature_graph,
            config=cls.graph_config,
        )
        cls.feature_sess_lock = Lock()

        # Chuẩn bị ctc graph cho recognizer
        cls.ctc_graph = tf.compat.v1.Graph()
        cls.ctc_sess = tf.compat.v1.Session(
            graph=cls.ctc_graph,
            config=cls.graph_config,
        )
        cls.ctc_sess_lock = Lock()


def _calc_fps(t0):
    try:
        return 1000 / ((time.time() - t0) * 1000)
    except ZeroDivisionError:
        return float(-1)


def _draw_fps(frame, fps):
    cv2.putText(
        frame,
        f'{fps:.1f} fps',
        (10, 20),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.5,
        (0, 255, 0),
    )


# Dữ liệu test
detect_i = -1
recognize_i = -1
detect_results = [
    [], [], [], [], [], [], [], [], [],
    [[13, 40, 50, 87]], [[13, 40, 50, 87]],
    [[13, 40, 50, 87]], [[13, 40, 50, 87]],
    [[13, 40, 50, 87]], [[13, 40, 50, 87]],
    [[13, 40, 50, 87]], [[13, 40, 50, 87]],
    [], [], [], [], [], [], [], [], [],
    [], [], [], [], [], [], [], [], [],
    [], [], [], [], [], [], [], [], [],
    [], [], [], [], [], [], [], [], [],
    [[13, 40, 50, 87]], [[13, 40, 50, 87]],
    [[13, 40, 50, 87]], [[13, 40, 50, 87]],
    [[13, 40, 50, 87]], [[13, 40, 50, 87]],
    [[13, 40, 50, 87]], [[13, 40, 50, 87]],
    [], [], [], [], [], [], [], [], [],
    [], [], [], [], [], [], [], [], [],
    [], [], [], [], [], [], [], [], [],
    [], [], [], [], [], [], [], [], [],
    [[13, 40, 50, 87]], [[13, 40, 50, 87]],
    [[13, 40, 50, 87]], [[13, 40, 50, 87]],
    [[13, 40, 50, 87]], [[13, 40, 50, 87]],
    [[13, 40, 50, 87]], [[13, 40, 50, 87]],
    [[13, 40, 50, 87]], [[13, 40, 50, 87]],
    [[13, 40, 50, 87]], [[13, 40, 50, 87]],
    [[13, 40, 50, 87]], [[13, 40, 50, 87]],
    [[13, 40, 50, 87]], [[13, 40, 50, 87]],
    [[13, 40, 50, 87]], [[13, 40, 50, 87]],
    [[13, 40, 50, 87]], [[13, 40, 50, 87]],
    [[13, 40, 50, 87]], [[13, 40, 50, 87]],
    [[13, 40, 50, 87]], [[13, 40, 50, 87]],
    [[13, 40, 50, 87]], [[13, 40, 50, 87]],
    [[13, 40, 50, 87]], [[13, 40, 50, 87]],
    [[13, 40, 50, 87]], [[13, 40, 50, 87]],
    [[13, 40, 50, 87]], [[13, 40, 50, 87]],
    [[13, 40, 50, 87]], [[13, 40, 50, 87]],
    [[13, 40, 50, 87]], [[13, 40, 50, 87]],
    [[13, 40, 50, 87]], [[13, 40, 50, 87]],
    [[13, 40, 50, 87]], [[13, 40, 50, 87]],
    [], [], [], [], [], [], [], [], [],
]
recognize_results = [
    ('1Abcd983261', cv2.imread('1.jpg')),
    ('1Abcd983261', cv2.imread('1.jpg')),
    ('', cv2.imread('1.jpg')),
    ('', cv2.imread('1.jpg')),
]


def fake_time():
    return 1000000 + detect_i * 0.25


def fake_detect(image, sess, inputs, boxes):
    global detect_i
    detect_i += 1
    time.sleep(0.1)
    return detect_results[detect_i % len(detect_results)]


def fake_recognize_images(images, sess, arr_leng):
    global recognize_i
    recognize_i += 1
    return recognize_results[recognize_i % len(recognize_results)]
