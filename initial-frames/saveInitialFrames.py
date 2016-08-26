from __future__ import division, print_function
from physicsTable import *
from physicsTable.constants import *
import os, sys, random
import threading
from glob import glob
import pygame as pg
from pygame.constants import *

FORMAT = '.png'
NUM_FRAMES = 2
STEP_SIZE = 0.1

output_dir = '/home/ubuntu/frames-new'
# Directory containing trials
trdir = os.path.join('..','python-trials', 'trials')

def drawFrame(trnm, t = 0.):
    tr = loadTrial(os.path.join(trdir + '/' + trnm + '.ptr'))
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

def threadSaveFiles(b):
    for full_path in glob(trdir + '/*Bl' + str(b) + '*.ptr'):
        tr = full_path.rsplit('/', 1)[-1]
        if (
                not os.path.exists(output_dir + '/' + tr[:-4] + '_0' + FORMAT) 
                or not os.path.exists(output_dir + '/' + tr[:-4] + '_1' + FORMAT)
                #or not os.path.exists(output_dir + '/' + tr[:-4] + '_2' + FORMAT) 
                #or not os.path.exists(output_dir + '/' + tr[:-4] + '_3' + FORMAT)
            ): 
            print('Thread ' + str(b) + ': Trial ' + tr, file=sys.stderr)
            saveFiles(output_dir, tr[:-4])

def saveFiles(output_dir, tnm):
    output_path = os.path.join(output_dir, tnm)
    for i in range(NUM_FRAMES):
        saveFrame(output_path + '_' + str(i) + FORMAT, tnm, STEP_SIZE * i)

if __name__ == '__main__':
    pg.init()

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    threads = []
    if len(sys.argv) > 1:
        tnm = sys.argv[1]
        saveFiles(output_dir, tnm)
    else:
        for b in range(1,6):
            thr = threading.Thread(target=threadSaveFiles, args=(b,))
            thr.start()
            threads.append(thr)

        for thread in threads:
            thread.join()
