from __future__ import division, print_function
from physicsTable import *
from physicsTable.constants import *
import os, sys, random
from glob import glob
import pygame as pg
from pygame.constants import *

# Directory containing trials
trdir = os.path.join('..','python-trials', 'trials')

def drawFrame(trnm, t = 0.):
    tr = loadTrial(os.path.join(trdir, trnm + '.ptr'))
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
    tr = loadTrial(os.path.join(trdir, trnm + '.ptr'))
    tb = tr.makeTable()
    if t > 0:
        tb.step(t)
    # TODO ???
    return tb.balls

def saveFiles(output_dir, tnm):
    output_path = os.path.join(output_dir, tnm)
    saveFrame(output_path + '_0.png', tnm, 0.)
    saveFrame(output_path + '_1.png', tnm, 0.1)

if __name__ == '__main__':
    pg.init()

    output_dir = 'frames'
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    if len(sys.argv) > 1:
        tnm = sys.argv[1]
        saveFiles(output_dir, tnm)
    else:
        for tr in os.listdir(trdir):
            if tr[-4:] == '.ptr' and (
                not os.path.exists(output_dir + '/' + tr[:-4] + '_0.png')
                or not os.path.exists(output_dir + '/' + tr[:-4] + '_1.png')): 
                print('Trial ' + tr, file=sys.stderr)
                saveFiles(output_dir, tr[:-4])
