from physicsTable import *
import os

PTR_DIR = "reach_trials"
JSON_DIR = "reach_JSON"

for fnm in os.listdir(PTR_DIR):
    if fnm[-4:] == '.ptr':
        tr = loadTrial(os.path.join(PTR_DIR, fnm))
        tr.jsonify(fldir=JSON_DIR, askoverwrite=True)
