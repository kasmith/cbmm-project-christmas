from __future__ import division
import sys,os,random,glob
from physicsTable import *
import pygaze
from pygaze import libscreen, libinput, liblog, libtime
from constants import *
from setup import *
from runTrial import drawTable, run
from textParse import *

# Load in the trials
trialdir = os.path.join(os.path.dirname(__file__),'Trials')
trials = []
for trfl in glob.glob(os.path.join(trialdir,"*.json")):
    trials.append(loadTrialFromJSON(trfl, "redgreen"))



# Calibrate the eye-tracker
tracker.calibrate()

displayInstructions("Start!", pygaze.expdisplay, True, False)

# Set up the output files - outdir comes from setup
with open(os.path.join(outdir, subjID+"_summary.csv"),'w') as sumfl, \
    open(os.path.join(outdir, subjID+"_track.csv"), 'w') as trackfl:
    sumfl.write("SubjID,Trial,Order,Motion,Switched,RT,RawResponse,RawGoal,Score,Response,Goal,Correct\n")
    trackfl.write("SubjID,Trial,PythonTime,TrackerTime,Steps,EyeX,EyeY,PupilSize,AtResponseOkay,AtShowTrial\n")

    tr = trials[0]
    score = 0
    score += run(tr, display, pygaze.expdisplay, tracker, sumfl, trackfl, 'Fwd', True, score, subjID)
    score += run(tr, display, pygaze.expdisplay, tracker, sumfl, trackfl, 'Rev', True, score, subjID)
    score += run(tr, display, pygaze.expdisplay, tracker, sumfl, trackfl, 'None', True, score, subjID)

displayInstructions("Done!", pygaze.expdisplay, True, False)
