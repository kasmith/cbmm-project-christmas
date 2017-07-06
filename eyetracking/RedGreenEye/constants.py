# Get the participant ID
subjID = raw_input("Please enter participant ID: ")

import pygaze

# Change this when the eyetracker is attached
DUMMYMODE = False

# Display constants
DISPTYPE = "pygame"
DISPSIZE = (1024, 768)
SCREENSIZE = (38.4, 28.8)
MOUSEVISIBLE = False
BGC = (255,255,255,255)
FULLSCREEN = not DUMMYMODE

# Input constants (SKIP - need to use pygame events not
KEYLIST = ['shift','esc','z','m','space']
KEYTIMEOUT = None

# Tracker constants
TRACKERTYPE = "eyelink"

# For the experiment
FPS = 40 # Rate of frame display / s
SHOWTIME = 500 # Amount of time to display ball motion (or until no motion entry) in ms
SCORE_MIN = 300 # RT below which pps get full points
SCORE_MAX = 2000 # RT above which pps get no points
TIME_MAX = 2500 # Time at which trial ends with no response
SHOWSPEEDUP = 4.0 # How much faster should the end motion be

# Colors
WHITE = (255,255,255)
BLACK = (0,0,0)
RED = (255,0,0)
GREEN = (0,255,0)