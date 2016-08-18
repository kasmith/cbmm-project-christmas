from __future__ import division
from physicsTable import *
from physicsTable.constants import *
import os, sys
import pygame as pg
from showTrials import *

# Open screenshot
pg.init()
scshot = pg.image.load('RGScShot_Arrow.png')

# Make trial plot
trsc = drawPath('RTr_Bl3_8',40)

# Transform together
trdims = trsc.get_size()
scdims = scshot.get_size()
hgt = trdims[1] - 6

new_wid = int((hgt / scdims[1]) * scdims[0])

scalesc = pg.transform.scale(scshot, (new_wid,hgt))

newdims = (trdims[0]+new_wid+3, trdims[1])
newsc = pg.Surface(newdims)

newsc.blit(scalesc,(3,3))
newsc.blit(trsc,(new_wid+3,0))

pg.image.save(newsc,'Fig1_Exp.png')