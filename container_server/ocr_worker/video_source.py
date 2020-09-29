#  Copyright (C) AI Power - All Rights Reserved
#  Unauthorized copying of this file, via any medium is strictly prohibited
#  Proprietary and confidential
#  Written by AI Power, January 2020

import os
import platform
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from threading import Thread, Lock
from typing import Callable, Optional

import cv2
import imutils
import numpy as np

from config.settings import log

_FrameNumStorage = 32
_OS = platform.system()
_FourCC = cv2.VideoWriter_fourcc(*'DIVX') if _OS == 'Windows' else cv2.VideoWriter_fourcc(*'XVID')
# _FourCC = cv2.VideoWriter_fourcc(*'MP4V')
_WriteVideoExecutor = ThreadPoolExecutor(max_workers=1)


class VideoSource:
    DfConfig = {
        'scale_width': 960,
        'scale_height': -1,
        'auto_retry': True,
        'auto_pass': True,
    }

    def __init__(
            self,
            stream_url,
            video_config=None,
            video_source_id=None,
            event_listener=None,
    ):
        import copy
        log.warn(f'VideoSource init: stream_url={stream_url} video_config={video_config}')
        try:
            stream_url = int(stream_url)
        except ValueError:
            pass
        self.stream_url: str = stream_url
        self.video: Optional[cv2.VideoCapture] = None
        self.src_width = -1
        self.src_height = -1
        self.src_fps = -1
        self.read_lock = Lock()

        self.dest_path = None
        self.dest_video = None
        self.dest_lock = Lock()

        self.cur_frame = None
        self.cur_frame_num = -1
        self.decoded = False

        self.vidconfig: dict = copy.deepcopy(self.DfConfig)
        self.update_conf(video_config)

        self.video_source_id = video_source_id
        self.callback: Callable = event_listener

        self.stt = VideoSourceStt.Init
        self.corrupt = False

        self.scale_width = self.vidconfig['scale_width']
        self.scale_height = self.vidconfig['scale_height']
        self.auto_retry = self.vidconfig['auto_retry']
        self.auto_pass = self.vidconfig['auto_pass']

        self.stream_subscriber_ids = set()
        self.cur_frame_stream_data = None
        self.cur_frame_stream_id = -1

    def check(self):
        if self.stt is VideoSourceStt.Running:
            return True
        video = cv2.VideoCapture(self.stream_url)
        if video.isOpened():
            video.release()
            return True
        return False

    def start(self, first_access_check=True):
        if (
                self.stt is VideoSourceStt.TryingToCapture
                or self.stt is VideoSourceStt.Running
                or self.stt is VideoSourceStt.Retrying
        ):
            return

        if first_access_check and not self.check():
            raise IOError('Access video failed')

        log.warn(f'VideoSource [{self.video_source_id}] - connecting...')
        self.stt = VideoSourceStt.TryingToCapture

        self.video = self._get_video()
        self._get_video_info()
        if self.video is None:
            self._notify_listener(VideoSourceStt.Stopped)
            raise IOError('Access video failed')
        self.corrupt = False
        self.stt = VideoSourceStt.Running
        if self.auto_pass:
            thread = Thread(target=self._stream_loop)
            thread.daemon = True
            thread.start()

    def read(self):
        if self.read_lock.locked():
            return self.cur_frame, self.cur_frame_num

        with self.read_lock:
            while not self.auto_pass and not self.corrupt:
                grabbed = self.video.grab()
                if not grabbed:
                    if self.auto_retry:
                        self.video = self._get_video()
                        self._get_video_info()
                        continue
                    else:
                        self.stop()
                        break
                self.decoded = False

                if sys.getsizeof(self.cur_frame_num) > _FrameNumStorage:
                    self.cur_frame_num = 0
                else:
                    self.cur_frame_num += 1
                break

            self._decode_frame()

        return self.cur_frame, self.cur_frame_num

    def get_stream_data(
            self,
            scale_width=720,
            scale_height=-1,
    ):
        if self.read_lock.locked():
            if (
                    (scale_width != -1 and scale_width != self.cur_frame.shape[1])
                    or (scale_height != -1 and scale_height != self.cur_frame.shape[0])
            ):
                frame = scale_frame(
                    self.cur_frame,
                    scale_width=scale_width, scale_height=scale_height,
                )
            else:
                frame = self.cur_frame
            _, cur_frame_stream_data = cv2.imencode('.jpg', frame)
            self.cur_frame_stream_data = cur_frame_stream_data
            return cur_frame_stream_data

        self.read()

        if self.cur_frame_num != self.cur_frame_stream_id:
            self._decode_frame()
            if (
                    (scale_width != -1 and scale_width != self.cur_frame.shape[1])
                    or (scale_height != -1 and scale_height != self.cur_frame.shape[0])
            ):
                frame = scale_frame(
                    self.cur_frame,
                    scale_width=scale_width, scale_height=scale_height,
                )
            else:
                frame = self.cur_frame
            _, cur_frame_stream_data = cv2.imencode('.jpg', frame)
            self.cur_frame_stream_data = cur_frame_stream_data
            return cur_frame_stream_data

        return self.cur_frame_stream_data

    def stop(self):
        self.corrupt = True
        self._reset_frame_info()
        self.stt = VideoSourceStt.Stopped
        if self.video is not None:
            time.sleep(3)
            if self.video is not None:
                self.video.release()
                self.video = None

    def update_conf(self, vidconf):
        import copy
        if vidconf is not None and isinstance(vidconf, dict):
            for k, v in vidconf.items():
                if self.vidconfig.__contains__(k) and isinstance(v, type(self.vidconfig[k])):
                    self.vidconfig[k] = copy.deepcopy(v)

    def get_stt(self):
        return self.stt

    def change_source(self, stream_url):
        self.stream_url = stream_url
        if self.stt is not VideoSourceStt.Init and self.stt is not VideoSourceStt.Stopped:
            self.stop()
            self.start()

    def record_to(self, dest):
        try:
            self.dest_path = dest
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            self.dest_video = cv2.VideoWriter(
                self.dest_path, _FourCC, self.src_fps,
                (self.src_width, self.src_height)
            )

        except BaseException as exc:
            log.warn(f'VideoSource [{self.video_source_id}] - start record to {dest} failed: {exc}')

    def stop_record(self):
        # noinspection PyBroadException
        try:
            if self.dest_video is None:
                return
            video_writer = self.dest_video
            self.dest_video = None
            self.dest_path = None
            if video_writer is not None:
                with self.dest_lock:
                    video_writer.release()

        except BaseException as exc:
            log.warn(f'VideoSource [{self.video_source_id}] - stop record failed: {exc}')

    def subscribe_to_stream(self, subscriber_id):
        self.stream_subscriber_ids.add(subscriber_id)

    def unsubscribe_from_stream(self, subscriber_id):
        try:
            self.stream_subscriber_ids.remove(subscriber_id)
        except KeyError:
            pass

    def _stream_loop(self):
        self.cur_frame_num = -1
        while not self.corrupt and self.auto_pass:
            grabbed = self.video.grab()
            if not grabbed:
                if self.auto_retry:
                    self.video = self._get_video()
                    self._get_video_info()
                    continue
                else:
                    self.stop()
                    break
            self.decoded = False

            _WriteVideoExecutor.submit(self._write_frame, None)

            if sys.getsizeof(self.cur_frame_num) > _FrameNumStorage:
                self.cur_frame_num = 0
            else:
                self.cur_frame_num += 1

        log.warn(f'VideoSource [{self.video_source_id}] - stopped')
        self.stt = VideoSourceStt.Stopped

    def _get_video(self):
        with self.read_lock:
            video = None
            while not self.corrupt:
                # noinspection PyBroadException
                try:
                    video = cv2.VideoCapture(self.stream_url)
                    if video.isOpened():
                        log.warn(f'VideoSource [{self.video_source_id}] - connect successfully, streaming')
                        self._notify_listener(VideoSourceStt.Running)
                        self.stt = VideoSourceStt.Running
                        break

                except BaseException:
                    pass

                if not self.auto_retry:
                    log.warn(f'VideoSource [{self.video_source_id}] - connect failed, stopped')
                    self._notify_listener(VideoSourceStt.Stopped)
                    self.stt = VideoSourceStt.Stopped
                    break

                if self.stt is not VideoSourceStt.Retrying:
                    self.stt = VideoSourceStt.Retrying

                log.warn(f'VideoSource [{self.video_source_id}] - connect failed')
                self._notify_listener(VideoSourceStt.Stopped)
                time.sleep(3)
                log.warn(f'VideoSource [{self.video_source_id}] - retry connect')

            return video

    def _get_video_info(self):
        self.src_width = int(self.video.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.src_height = int(self.video.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.src_fps = self.video.get(cv2.CAP_PROP_FPS)

    def _reset_frame_info(self):
        self.cur_frame = None
        self.cur_frame_num = -1

    def _notify_listener(self, event):
        if self.callback is not None:
            self.callback(self.video_source_id, event)

    def _write_frame(self, frame: np.ndarray):
        # noinspection PyBroadException
        try:
            if self.dest_video is not None:
                if frame is None:
                    self._decode_frame()
                    frame = self.cur_frame
                with self.dest_lock:
                    self.dest_video.write(frame.astype('uint8'))
        except BaseException as exc:
            log.warn(f'VideoSource [{self.video_source_id}] - write frame failed: {exc}')

    def _decode_frame(self):
        # if self.corrupt or self.decoded or self.read_lock.locked():
        #     return
        # with self.read_lock:
        if self.corrupt or self.decoded:
            return
        grabbed, frame = self.video.retrieve()
        if grabbed and frame is not None:
                self.decoded = True
                self.cur_frame = scale_frame(
                    frame,
                    self.scale_width,
                    self.scale_height,
                )


class VideoSourceStt:
    Init = 'stt.vid.init'
    TryingToCapture = 'stt.vid.try'
    Running = 'stt.vid.run'
    Retrying = 'stt.vid.retry'
    Stopped = 'stt.vid.stop'
    NotFound = 'stt.vid.notFound'


def _try_check(url, return_dict):
    # noinspection PyBroadException
    try:
        import cv2
        video = cv2.VideoCapture(url)
        if not video.isOpened():
            return_dict[url] = False
            return False
        grabbed = video.grab()
        return_dict[url] = grabbed
        return grabbed

    except Exception:
        return_dict[url] = False
        return False


def check(url, timeout=5):
    import multiprocessing

    manager = multiprocessing.Manager()
    return_dict = manager.dict()
    check_process = multiprocessing.Process(target=_try_check, args=(url, return_dict))

    check_process.start()
    check_process.join(timeout=timeout)
    check_process.terminate()

    return return_dict.get(url, False)


def scale_frame(frame, scale_width, scale_height):
    if scale_width != -1:
        if scale_height != -1:
            frame = cv2.resize(frame, (scale_width, scale_height))
        else:
            frame = imutils.resize(frame, width=scale_width)
    elif scale_height != -1:
        frame = imutils.resize(frame, height=scale_height)
    return frame


def crop_frame(frame, lefttop, rightbottom, copy=False):
    (l, t), (r, b) = adjust_inside(lefttop, rightbottom, frame.shape[1], frame.shape[0])

    if copy:
        return frame[t:b, l:r].copy()

    return frame[t:b, l:r]


def adjust_inside(
        lefttop, rightbottom,
        frame_width, frame_height
):
    lefttop = (
        0 if lefttop[0] < 0 else lefttop[0],
        0 if lefttop[1] < 0 else lefttop[1],
    )
    rightbottom = (
        frame_width if rightbottom[0] > frame_width else rightbottom[0],
        frame_height if rightbottom[1] > frame_height else rightbottom[1],
    )

    return lefttop, rightbottom


show_frame_exec = ThreadPoolExecutor(max_workers=1)


def show_frame(title, frame):
    show_frame_exec.submit(cv2.imshow, title, frame)
    show_frame_exec.submit(cv2.waitKey, 1)


def close_frame(title):
    show_frame_exec.submit(cv2.destroyWindow, title)
