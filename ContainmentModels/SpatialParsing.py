from __future__ import division
import os, sys, copy
from physicsTable import *
from physicsTable.constants import *
import numpy as np
import scipy as sp
import pygame as pg

R = -5
G = -10
W = -1
FL = 1
CL = 0

def pointInRect(pt, ul, br):
    wl, wu = ul
    wr, wb = br
    r = pg.Rect(wl,wu,wr-wl,wb-wu)
    return r.collidepoint(pt)

class SpatialParse(object):

    def __init__(self, trial):
        self.tab = trial
        self.dim = self.tab.dims
        # Parse out all of the break points on the table
        xs = []
        ys = []
        for w in self.tab.normwalls:
            l, u = w[0]
            r, b = w[1]
            if l not in xs: xs.append(l)
            if (r+1) not in xs: xs.append(r+1)
            if u not in ys: ys.append(u)
            if (b+1) not in ys: ys.append(b+1)
        for g in self.tab.goals:
            l, u = g[0]
            r, b = g[1]
            if l not in xs: xs.append(l)
            if (r+1) not in xs: xs.append(r+1)
            if u not in ys: ys.append(u)
            if (b+1) not in ys: ys.append(b+1)
        xs.sort()
        ys.sort()
        self.xbrs = [0] + xs + [self.dim[0]]
        self.ybrs = [0] + ys + [self.dim[1]]

        # Cut any breaks that are RIGHT next to each other
        i = 0
        while i < len(self.xbrs)-1:
            if self.xbrs[i] + 1 == self.xbrs[i+1]: self.xbrs.pop(i)
            else: i += 1
        i = 0
        while i < len(self.ybrs)-1:
            if self.ybrs[i] + 1 == self.ybrs[i+1]: self.ybrs.pop(i)
            else: i += 1

        # Build and fill the map
        self.mapdim = (len(self.xbrs)-1,len(self.ybrs)-1)

        self.map = np.zeros(self.mapdim)
        for x in range(self.mapdim[0]):
            for y in range(self.mapdim[1]):
                if x == 6 and y == 7:
                    print 'Here'
                midpt = self.getMapMidpt((x,y))
                self.map[x,y] = CL
                for w in self.tab.normwalls:
                    if pointInRect(midpt,w[0],w[1]): self.map[x,y] = W
                for g in self.tab.goals:
                    if g[2] == REDGOAL:
                        if pointInRect(midpt,g[0],g[1]): self.map[x,y] = R
                    elif g[2] == GREENGOAL:
                        if pointInRect(midpt,g[0],g[1]): self.map[x,y] = G
                    else:
                        raise Exception('Cannot have goals that are not red or green')

        self.steps = 0
        self.rsteps = -1
        self.gsteps = -1
        self.nextpts = [self.getMapLocByPoint(self.tab.ball[0])]


    def getMapLocByPoint(self,pt):
        x,y = pt
        if x < 0 or x > self.dim[0] or y < 0 or y > self.dim[1]: raise Exception('Point out of bounds')
        lx = np.searchsorted(self.xbrs,x)-1
        ly = np.searchsorted(self.ybrs,y)-1
        return (lx,ly)

    def getMapMidpt(self,maploc):
        px,py = maploc
        xmin = self.xbrs[px]
        xmax = self.xbrs[px+1]
        ymin = self.ybrs[py]
        ymax = self.ybrs[py+1]

        return (int((xmax + xmin)/2),int((ymax+ymin)/2))

    def step(self):
        self.steps += 1
        npts = []
        nomore = True
        for pt in self.nextpts:
            for np in [(pt[0]-1,pt[1]),(pt[0],pt[1]-1),(pt[0]+1,pt[1]),(pt[0],pt[1]+1)]:
                if np[0] >= 0 and np[0] < self.mapdim[0] and np[1] >= 0 and np[1] < self.mapdim[1]:
                    m = self.map[np]
                    if m == R and self.rsteps == -1: self.rsteps = self.steps
                    elif m == G and self.gsteps == -1: self.gsteps = self.steps
                    elif m == CL:
                        self.map[np] = FL
                        npts.append(np)
                        nomore = False
        if self.rsteps != -1 and self.gsteps != -1: nomore = True
        self.nextpts = npts
        return nomore

    def run(self):
        r = False
        while not r:
            r = self.step()
        return [self.gsteps, self.rsteps, self.steps]

if __name__ == '__main__':
    tr = loadTrial(os.path.join('..','CriticalTables','SemiOpen1.ptr'))
    SP = SpatialParse(tr)
    #SP.step()
    print np.transpose(SP.map)
    print SP.xbrs
    print SP.ybrs
    print SP.nextpts
    print SP.run()

    if True:
        pg.init()
        sc = pg.display.set_mode((1000,600))
        tab = tr.makeTable()
        tab.demonstrate()