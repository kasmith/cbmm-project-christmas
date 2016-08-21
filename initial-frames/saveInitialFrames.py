from __future__ import division
from physicsTable import *
from physicsTable.constants import *
import os, sys, random
import pygame as pg
from pygame.constants import *

# modified trials directory
#trdir = os.path.join('..','maketrials')
trdir = os.path.join('..','python-trials', 'trials')
modfitdir = os.path.join('..','initial-frames')
pg.init()

trials = dict()
trnames = []
for tr in os.listdir(trdir):
    if tr[-4:] == '.ptr':
        tnm = tr[:-4]
        trnames.append(tnm)
        trials[tnm] = loadTrial(os.path.join(trdir,tr))

def drawFrame(trnm, t = 0.):
    tr = trials[trnm]
    sc = pg.Surface(tr.dims)
    tb = tr.makeTable()
    tb.assignSurface(sc,(0,0))
    
    if t > 0.:
        tb.step(t)
    tb.draw()
    return sc
    
def saveFrame(flnm, trnm, t = 0.):
    sc = drawFrame(trnm, t)
    pg.image.save(sc, flnm)
    
def extractVelocity(trnm, t=0.):
    tr = trials[trnm]
    tb = tr.makeTable()
    if t > 0:
        tb.step(t)
    return tb.balls

if __name__ == '__main__':

    if len(sys.argv) > 1:
        tnm = [sys.argv[1]]
        if tnm[0] not in trnames: raise Exception('Need a proper trial name')
    else:
        tnm = trnames 

    output_dir = 'frames'
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    for name in trnames:
        output_file = os.path.join(output_dir, name + '.bmp')
        saveFrame(output_file, name, 0.)
