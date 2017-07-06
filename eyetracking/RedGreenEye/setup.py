from __future__ import division
import sys,os,random
from physicsTable import *
import pygaze
from pygaze import libscreen, libtime, liblog, eyetracker
import constants

# Set up the screen
display = libscreen.Display()
screen = libscreen.Screen()

# Get the tracker
outdir = os.path.join(os.path.dirname(__file__), 'Output')
tracker = eyetracker.EyeTracker(display, logfile = os.path.join(outdir, constants.subjID+"_log"))