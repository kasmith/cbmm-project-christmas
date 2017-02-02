import json, os
from physicsTable import *
import pygame as pg
import numpy as np

TRIALDIR = "exp_trials"
IMGDIR = "Trial_Images"
LINELEN = 60

def drawMotion(tr, type = "fwd"):
    assert type in ['fwd','bkwd','none'], "Incorrect motion type"

    tab = tr.makeTable()
    sc = pg.Surface(tab.dim)

    # Draw the table on the new surface
    tab.assignSurface(sc)
    tab.draw()

    # Draw a border
    pg.draw.line(sc, (0,0,0), (0,0), (0,tab.dim[1]),2)
    pg.draw.line(sc, (0,0,0), (0,0), (tab.dim[0],0),2)
    pg.draw.line(sc, (0,0,0), (tab.dim[0]-1,0), (tab.dim[0]-1, tab.dim[1]),2)
    pg.draw.line(sc, (0, 0, 0), (0, tab.dim[1]-1), (tab.dim[0], tab.dim[1]-1), 2)

    if type == "none":
        return sc

    vel = np.array(tab.balls.getvel())
    ipos = np.array(tab.balls.getpos())
    if type == 'bkwd':
        vel *= -1

    vnorm = vel / np.linalg.norm(vel)
    epos = ipos + vnorm*LINELEN
    pg.draw.line(sc, (0,0,255), map(int, ipos), map(int, epos), 5)
    return sc


for fnm in os.listdir(TRIALDIR):
    if fnm[-4:] == '.ptr':
        tr = loadTrial(os.path.join(TRIALDIR, fnm))
        basenm = fnm[:-4]
        for tp in ['fwd','bkwd','none']:
            pg.image.save(drawMotion(tr,tp), os.path.join(IMGDIR,basenm+"_"+tp+".png"))
        print basenm

