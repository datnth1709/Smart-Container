#  Copyright (C) AI Power - All Rights Reserved
#  Unauthorized copying of this file, via any medium is strictly prohibited
#  Proprietary and confidential
#  Written by AI Power, January 2020

import os
from random import random

import cv2
import numpy as np
import tensorflow as tf

char_list_dataset = []
with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'char_list.txt'), 'r') as f:
    lines = f.read()

for line in lines:
    char_list_dataset.append(line)


def decoder_output_to_text(ctc_output, batch_size):
    """extract texts from output of CTC decoder"""
    # contains string of labels for each batch element
    encoded_label_strs = [[] for i in range(batch_size)]

    # ctc returns tuple, first element is SparseTensor
    decoded = ctc_output[0][0]

    # go over all indices and save mapping: batch -> values
    for (idx, idx2d) in enumerate(decoded.indices):
        label = decoded.values[idx]
        batch_element = idx2d[0]  # index according to [b,t]
        encoded_label_strs[batch_element].append(label)

    # map labels to chars for all batch elements
    return [str().join([char_list_dataset[c] for c in labelStr]) for labelStr in encoded_label_strs]


def get_input_boxes_recognition(graph_frozen):
    with graph_frozen.as_default():
        images_placeholder = tf.compat.v1.get_default_graph().get_tensor_by_name('CREATE_INPUT/input_image_model:0')
        labelsequence_placeholder = tf.compat.v1.get_default_graph().get_tensor_by_name('CREATE_INPUT/max_length_prediction:0')
        istraining_placeholder = tf.compat.v1.get_default_graph().get_tensor_by_name('CREATE_INPUT/is_training_model:0')
        output_model = tf.compat.v1.get_default_graph().get_tensor_by_name('ARCHITECTURE_MODEL/transpose:0')
    return images_placeholder, labelsequence_placeholder, istraining_placeholder, output_model


def preprcess_data(img, img_size, data_augmentation=True):
    """put img into target img of size imgSize, transpose for TF and normalize gray-values"""

    # there are damaged files in IAM dataset - just use black image instead
    if img is None:
        img = np.zeros([img_size[1], img_size[0]])

    # increase dataset size by applying random stretches to the images
    if data_augmentation:
        stretch = (random.random() - 0.5)  # -0.5 .. +0.5
        w_stretched = max(int(img.shape[1] * (1 + stretch)), 1)  # random width, but at least 1
        img = cv2.resize(img, (w_stretched, img.shape[0]))  # stretch horizontally by factor 0.5 .. 1.5

    # create target image and copy sample image into it

    (wt, ht) = img_size

    (h, w) = img.shape
    fx = w / wt
    fy = h / ht
    f = max(fx, fy)
    new_size = (
        max(min(wt, int(w / f)), 1),
        max(min(ht, int(h / f)), 1),
    )  # scale according to f (result at least 1 and at most wt or ht)
    img = cv2.resize(img, new_size)
    target = np.ones([ht, wt]) * 255
    target[0:new_size[1], 0:new_size[0]] = img

    # transpose for TF
    img = cv2.transpose(target)

    # normalize
    (m, s) = cv2.meanStdDev(img)
    m = m[0][0]
    s = s[0][0]
    img = img - m
    img = img / s if s > 0 else img
    img = np.expand_dims(img, axis=2)

    return img
