from __future__ import division
from physicsTable import *
from physicsTable.constants import *
import pygame as pg
from pygame.constants import *
import sys

if __name__ == '__main__':
    
    if len(sys.argv) < 2:
        raise Exception('Need to load a trial from file path')
    
    tr = loadTrial(sys.argv[1])
    
    pg.init()
    sc = pg.display.set_mode((1000,620))
    
    tb = tr.makeTable()
    
    tb.demonstrate()
    