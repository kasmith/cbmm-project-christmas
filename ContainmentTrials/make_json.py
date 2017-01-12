from physicsTable import *
import os

PTR_DIR = "exp_trials"
JSON_DIR = "JSON"

for fnm in os.listdir(PTR_DIR):
    if fnm[-4:] == '.ptr':
        tr = loadTrial(os.path.join(PTR_DIR, fnm))
        tr.jsonify(fldir=JSON_DIR, askoverwrite=True)
