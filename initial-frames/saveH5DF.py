from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import os
from sys import argv

import h5py
import pickle
import numpy as np
from scipy.misc import imread
from scipy.misc import imresize

# TODO Change parameters to different file, or take them as input to functions
IMAGE_FORMAT = '.png'
IMAGE_SIZE = 250 #TODO Change this
PIXEL_DEPTH = 255
DOWN_SAMPLE = 4 # Down sampling factor for input images.
NUM_FRAMES = 2 # Number of initial frames provided as input.
NUM_CHANNELS = 3
TYPE = 'uint8'


def extract_data(filename, images_dir, output_dir, trials_idx, block_nums, goal_dict):
  """Extract the images into a 4D tensor 
        [image index, y, x, channels * frames] in h5df file.
  """
  num_images = len(trials_idx) * len(block_nums)
  f = h5py.File(os.path.join(output_dir, filename), 'w')
  X = f.create_dataset('X', (num_images, IMAGE_SIZE, IMAGE_SIZE, NUM_CHANNELS*NUM_FRAMES), dtype=TYPE)
  Y = f.create_dataset('Y', (num_images, 2), dtype=TYPE)

  image_count = 0
  for trial_num in trials_idx:
      for block_num in block_nums:
          print('Blocks ' + str(block_num) + ' Trial ' + str(trial_num))
          for frame_num in xrange(0, NUM_FRAMES):
              temp = imread(images_dir+'RTr_Bl'+str(block_num)+'_'+str(trial_num)+'_'+str(frame_num)+IMAGE_FORMAT)
              temp = imresize(temp, [temp.shape[0]//DOWN_SAMPLE, temp.shape[1]//DOWN_SAMPLE, temp.shape[2]])
              X[image_count, 0:temp.shape[0], 0:temp.shape[1], frame_num*NUM_CHANNELS:(frame_num+1)*NUM_CHANNELS] = temp
          label = goal_dict['RTr_Bl'+str(block_num)+'_'+str(trial_num)]
          Y[image_count, :] = [label, 1-label]
          image_count += 1

  f.close()

  # TODO Use pixel depth normalization???
  #data = (data - (PIXEL_DEPTH / 2.0)) / PIXEL_DEPTH

if __name__ == '__main__':
    if not os.path.exists('/home/ubuntu/drive/' + argv[1]):
        with open('goal_dict.pickle', 'rb') as goal_dict:
            extract_data(argv[1], 'frames/', '/home/ubuntu/drive', np.random.permutation(10000), xrange(1,6), pickle.load(goal_dict))
