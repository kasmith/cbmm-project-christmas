from __future__ import division
from physicsTable import *
from physicsTable.constants import *
#import pygame as pg
#rom pygame.constants import *
import numpy as np
import os,sys,time

R = -5
G = -10
W = -1
FL = 1
CL = 0

class Flooder(object):
    def __init__(self,tr,useBallSize = True):
        self.tr = tr
        self.dims = tr.dims
        self.map = np.zeros(self.dims, dtype = np.int)
        self.steps = 0
        self.size = 0
        self.rsteps = -1;
        self.gsteps = -1;
        brad = tr.ball[2]
        for g in tr.goals:
            ul = g[0]
            lr = g[1]
            for x in range(ul[0],lr[0]):
                for y in range(ul[1],lr[1]):
                    if g[3] == RED: self.map[x,y] = R
                    else: self.map[x,y] = G
        for w in tr.normwalls:
            ul = w[0]
            lr = w[1]
            if(useBallSize):
                for x in range(max(ul[0]-brad,0), min(lr[0]+brad,self.dims[0])):
                    for y in range(max(ul[1]-brad,0), min(lr[1]+brad, self.dims[1])):
                        self.map[x,y] = W
            else:
                for x in range(max(ul[0],0), min(lr[0],self.dims[0])):
                    for y in range(max(ul[1],0), min(lr[1],self.dims[1])):
                        self.map[x,y] = W
        self.nextpts = [tr.ball[0]]

    '''
    def makeScreen(self):
        sc = pg.Surface(self.dims)

        for x in range(self.dims[0]):
            if x % 100 == 0: print x
            for y in range(self.dims[1]):
                m = self.map[x,y]
                if m == R: c = RED
                elif m == G: c = GREEN
                elif m == W: c = BLACK
                elif m == FL: c = GREY
                else: c = WHITE
                sc.set_at((x,y),c)
        return sc
    '''

    def step(self):
        self.steps += 1
        npts = []
        nomore = True
        for pt in self.nextpts:
            for np in [(pt[0]-1,pt[1]),(pt[0],pt[1]-1),(pt[0]+1,pt[1]),(pt[0],pt[1]+1)]:
                if np[0] >= 0 and np[0] < self.dims[0] and np[1] >= 0 and np[1] < self.dims[1]:
                    m = self.map[np]
                    if m == R and self.rsteps == -1: self.rsteps = self.steps
                    elif m == G and self.gsteps == -1: self.gsteps = self.steps
                    elif m == CL:
                        self.size += 1
                        self.map[np] = FL
                        npts.append(np)
                        nomore = False
        # Stop if both goals are hit
        if self.rsteps != -1 and self.gsteps != -1: nomore = True

        self.nextpts = npts
        return nomore

    def run(self):
        r = False
        while r is False:
            r = self.step()
        return {'size': self.size,
                'max_geodesic_dist': self.steps,
                'min_dist_to_goal': self.gsteps}
