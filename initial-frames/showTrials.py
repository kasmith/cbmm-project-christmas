from __future__ import division
from physicsTable import *
from physicsTable.constants import *
import os, sys, random
import pygame as pg
from pygame.constants import *

trdir = os.path.join('..','maketrials')
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
    return tb.balls.

if __name__ == '__main__':

    if len(sys.argv) > 1:
        tnm = sys.argv[1]
        if tnm not in trnames: raise Exception('Need a proper trial name')
    else:
        tnm = random.sample(trnames,1)[0]
        print tnm

    sc = pg.display.set_mode((1006,626))
    pscr = drawFrame(tnm, 0.)
    sc.blit(pscr,(0,0))
    pg.display.flip()
    running = True
    while running:
        for e in pg.event.get():
            if e.type == MOUSEBUTTONDOWN: running = False