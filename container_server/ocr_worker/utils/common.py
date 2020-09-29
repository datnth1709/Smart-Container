#  Copyright (C) AI Power - All Rights Reserved
#  Unauthorized copying of this file, via any medium is strictly prohibited
#  Proprietary and confidential
#  Written by AI Power, January 2020

import tensorflow as tf


def load_graph(frozen_graph_filename):
    with tf.io.gfile.GFile(frozen_graph_filename, 'rb') as f:
        graph_def = tf.compat.v1.GraphDef()
        graph_def.ParseFromString(f.read())

    with tf.Graph().as_default() as graph:
        tf.import_graph_def(graph_def, name='')

    return graph


def get_box_area(bbox):
    x1, y1, x2, y2 = int(bbox[0]), int(bbox[1]), int(bbox[2]), int(bbox[3])
    width = abs(x2 - x1)
    height = abs(y2 - y1)
    return width * height


def get_max_bbox_area(bboxes):
    max_box_area = 0
    index_max_box_area = -1
    for i, bbox in enumerate(bboxes):
        area = get_box_area(bbox)
        if max_box_area < area:
            max_box_area = area
            index_max_box_area = i
    return index_max_box_area, max_box_area
