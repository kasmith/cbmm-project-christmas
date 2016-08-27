from __future__ import division, print_function, absolute_import

import sys
import h5py
import numpy as np

import tensorflow as tf
import tflearn
from tflearn.layers.core import input_data, dropout, fully_connected
from tflearn.layers.conv import conv_2d, max_pool_2d
from tflearn.layers.normalization import local_response_normalization
from tflearn.layers.estimator import regression

TEST_SET  = '/home/ubuntu/drive/test_frames_b1-5_t10k_f2_s2.h5'
# Load dataset
f = h5py.File(TEST_SET, 'r')
X = f['X']
Y = f['Y']

# Testing
import googlenet
network = googlenet.build_googlenet()
model = tflearn.DNN(network, checkpoint_path='model_googlenet',
                max_checkpoints=1, tensorboard_verbose=2)
model.load(sys.argv[1])
score = model.evaluate(X, Y, batch_size=100)
print(score)
f.close()
