from __future__ import division
from physicsTable import *
from physicsTable.constants import *
import pygame as pg
from pygame.constants import *
import numpy as np
import scipy as sp
import os,sys,time, random

R = -5
G = -10
W = -1
FL = 1
CL = 0

# Bresenham's line algorithm from http://www.roguebasin.com/index.php?title=Bresenham%27s_Line_Algorithm
def get_line(start, end):
    x1, y1 = start
    x2, y2 = end
    dx = x2 - x1
    dy = y2 - y1
    is_steep = abs(dy) > abs(dx)
    if is_steep:
        x1, y1 = y1, x1
        x2, y2 = y2, x2
    swapped = False
    if x1 > x2:
        x1, x2 = x2, x1
        y1, y2 = y2, y1
        swapped = True
    dx = x2 - x1
    dy = y2 - y1
    error = int(dx / 2.0)
    ystep = 1 if y1 < y2 else -1
    y = y1
    points = []
    for x in range(x1, x2 + 1):
        coord = (y, x) if is_steep else (x, y)
        points.append(coord)
        error -= abs(dy)
        if error < 0:
            y += ystep
            error += dx
    if swapped:
        points.reverse()
    return points

# Algorithm for calculating whether a ball centered on a point with radius R will intersect with a set of walls
def ball_intersect(bcent, rad, wall):
    bleft = bcent[0]-rad
    btop = bcent[1]-rad
    brect = pg.Rect(bleft,btop,rad*2,rad*2)

    wl, wu = wall[0]
    wr, wb = wall[1]
    rect = pg.Rect(wl,wu,wr-wl,wb-wu)

    if rect.colliderect(brect):
        if rect.contains(brect): return True
        if brect.bottom > rect.top or brect.top < rect.bottom:
            if bcent[0] > rect.left and bcent[0] < rect.right: return True
        if brect.right > rect.left or brect.left < rect.right:
            if bcent[1] > rect.top and bcent[1] < rect.bottom: return True

        return any(map(lambda pt: np.linalg.norm(np.array(pt)-np.array(bcent)) <= rad, [rect.topleft,rect.topright,rect.bottomleft,rect.bottomright]))
    else: return False

# Outdated - use node distances
# def euclidDist(p1,p2):
#     xdiff = p2[0]-p1[0]
#     ydiff = p2[1]-p1[1]
#     return np.sqrt(xdiff*xdiff + ydiff*ydiff)

# Directed Tree Graph with associated helper functions for path planning
class DirectedTree(object):

    # Subclass of nodes that form the tree
    class Node(object):
        def __init__(self,pt, parent, addCost = 1):
            self.pt = np.array(pt)
            self.parent = parent
            self.children = []
            self.newcost = addCost
            if self.parent is None: self.cost = 0
            else: self.cost = parent.cost + addCost
            self.goal = False # Marks whether this node is on a goal

        def addChild(self,childNode):
            self.children.append(childNode)

        def distance(self,newpt):
            return np.linalg.norm(self.pt - newpt)

        def getTerminals(self):
            r = []
            for c in self.children: r = r + c.getTerminals()
            return r

        def drawDown(self, surface, color = (196,196,196)):
            sp = map(int, self.pt)
            for c in self.children:
                cp = map(int, c.pt)
                pg.draw.line(surface,color,sp,cp)
                c.drawDown(surface,color)

        # Recalculate travel costs
        def recost(self):
            self.cost = self.parent.cost + self.newcost
            for c in self.children: c.recost()

        # Makes a new parent connection then drives the changed costs down to all children
        def reParent(self, newparent, newcost = 1):
            self.parent.children.remove(self)
            self.parent = newparent
            newparent.children.append(self)
            self.newcost = newcost
            self.recost()

        def markGoal(self, goal):
            self.goal = goal

    def __init__(self, initPt):
        headnode = self.Node(initPt,None)
        self.head = headnode
        self.nodes = [headnode]

    def addNode(self, parent, childpt, addCost = 1):
        child = self.Node(childpt,parent, addCost)
        parent.addChild(child)
        self.nodes.append(child)
        return child

    def getNode(self, position):
        for n in self.nodes:
            if np.all(n.pt == np.array(position)): return n
        raise Exception('Node with that position not found: ' + str(position))

    # Get only nodes that aren't touching any goal
    def freeNodes(self):
        return [n for n in self.nodes if n.goal == False]

    def nearest(self, newpt):
        frees = self.freeNodes()
        dists = np.array(map(lambda n: n.distance(newpt), frees))
        return frees[np.argmin(dists)]

    def near(self, newpt, radius):
        frees = self.freeNodes()
        dists = map(lambda n: n.distance(newpt) <= radius, frees)
        rets = []
        for i in range(len(dists)):
            if dists[i]: rets.append(frees[i])
        return rets

    def pathDown(self,endNode):
        revpath = [endNode]
        curnode = endNode
        while curnode.parent is not None:
            revpath.append(curnode.parent)
            curnode = curnode.parent
        revpath.reverse()
        return revpath

    def getTerminals(self):
        return self.head.getTerminals()

    def draw(self,surface,color = (196,196,196)):
        self.head.drawDown(surface,color)

    def nVertices(self): return len(self.nodes)

    def getAllPoints(self):
        return [np.array(n.pt) for n in self.nodes]

# A planning algorithm base that has many of the primitive functions from Karaman & Frazzoli (2011)
class PlanningBase(object):
    # Initialize the trial & a map of the screen
    def __init__(self, tr, steersize = None):
        self.tr = tr
        self.dims = tr.dims
        self.map = np.zeros(self.dims, dtype = np.int)
        self.tree = DirectedTree(tr.ball[0])
        self.steps = 0
        self.rsteps = -1;
        self.gsteps = -1;
        self.brad = tr.ball[2]
        self.bpos = tr.ball[0]
        if steersize is None: steersize = self.brad
        if steersize < 1: raise Exception('Need to move by at least 1px')
        self.ssize = steersize
        self.walls = tr.normwalls
        # Add walls around the edges
        self.walls.append([(-self.brad,-self.brad),(0,self.dims[1]+self.brad),(0,0,0,255),1.])
        self.walls.append([(-self.brad,-self.brad),(self.dims[0]+self.brad,0),(0,0,0,255),1.])
        self.walls.append([(-self.brad,self.dims[1]),(self.dims[0]+self.brad,self.dims[1]+self.brad),(0,0,0,255),1.])
        self.walls.append([(self.dims[0],-self.brad),(self.dims[0]+self.brad,self.dims[1]+self.brad),(0,0,0,255),1.])

        for g in tr.goals:
            ul = g[0]
            lr = g[1]
            if g[3] == RED: self.redgoal = [ul,lr]
            elif g[3] == GREEN: self.greengoal = [ul,lr]

        map = np.zeros(self.dims, dtype = np.int)
        for w in self.walls:
            ul = w[0]
            lr = w[1]
            for x in range(max(ul[0],0), min(lr[0],self.dims[0])):
                for y in range(max(ul[1],0), min(lr[1],self.dims[1])):
                    map[x,y] = W

        self.free = []
        for i in range(self.dims[0]):
            for j in range(self.dims[1]):
                if map[i,j] != W: self.free.append( (i,j) )



    def pointWallCollide(self,pt):
        for w in self.walls:
            if ball_intersect(pt,self.brad,w): return True
        return False

    def pointWallAdj(self,pt):
        for w in self.walls:
            if ball_intersect(pt,self.brad+1,w): return True
        if ball_intersect(pt,self.brad+1,self.redgoal): return True
        if ball_intersect(pt,self.brad+1,self.greengoal): return True
        return False

    def hitsGoal(self,pt):
        if ball_intersect(pt,self.brad,self.greengoal): return GREENGOAL
        elif ball_intersect(pt,self.brad,self.redgoal): return REDGOAL
        else: return False

    def sampleFree(self):
        if len(self.free)==0: return False
        idx = int(np.floor(random.random()*len(self.free)))
        return self.free[idx]

    def clearFree(self, pos):
        self.free.remove(pos)

    def steer(self, pFrom, pTo):
        # Find the angle between the vectors
        pFrom = np.array(pFrom)
        pTo = np.array(pTo)
        vdiff = pTo - pFrom

        # Test whether pTo is within the step size - if so just go there
        vlen = np.linalg.norm(vdiff)
        if vlen < self.ssize: return pTo

        # Otherwise step ssize in the direction of pTo
        vdiff = vdiff / np.linalg.norm(vdiff)
        c = np.dot(np.array([1,0]),vdiff)
        s = np.sqrt(1-c*c)
        oset = np.array([self.ssize * c, self.ssize * s])
        # Trig corrections for offset
        if(pFrom[1] > pTo[1]): oset = oset*np.array([1,-1])
        # Make sure there is some movement
        if np.abs(oset[0]) < 1 and np.abs(oset[1]) < 1: oset = oset / max(np.abs(oset))
        z = pFrom + oset
        z = map(int,z)
        return z

    # Modified version - returns True if it's good, but the last good point if not
    def collisionFree(self, pFrom, pTo):
        lpts = get_line(pFrom,pTo)
        lastpt = pFrom
        for lp in lpts:
            if self.pointWallCollide(lp): return lastpt
            lastpt = lp
        return True

    def drawSelf(self, mark = True):
        sc = pg.Surface(self.dims)
        sc.fill((255,255,255))
        tb = self.tr.makeTable()
        tb.draw()
        sc.blit(tb.surface,(0,0))
        self.tree.draw(sc)
        if mark:
            self.markGoals()
            if self.greenpath: pg.draw.lines(sc, (0,255,0), False, self.greenpath, 2)
            if self.redpath: pg.draw.lines(sc, (255,0,0), False, self.redpath, 2)
        return sc

    def markGoals(self):
        nodes = self.tree.nodes
        hits = [self.hitsGoal(n.pt) for n in nodes]
        greens = [nodes[i] for i in range(len(hits)) if hits[i]==GREEN]
        reds = [nodes[i] for i in range(len(hits)) if hits[i]==RED]

        if len(greens) == 0:
            self.greenpath = False
            self.greendist = -1
        else:
            gcost = [n.cost for n in greens]
            bestgreen = greens[np.argmin(gcost)]
            self.greenpath = [n.pt for n in self.tree.pathDown(bestgreen)]
            self.greendist = bestgreen.cost

        if len(reds) == 0:
            self.redpath = False
            self.reddist = -1
        else:
            rcost = [n.cost for n in reds]
            bestred = reds[np.argmin(rcost)]
            self.redpath = [n.pt for n in self.tree.pathDown(bestred)]
            self.reddist = bestred.cost



# Some testing
if __name__ == "__main__":
    pb = PlanningBase(loadTrial('../CriticalTables/SemiOpen1.ptr'))
    for i in range(10):
        sf = pb.sampleFree()
        st = pb.steer(pb.bpos,sf)
        cf = pb.collisionFree(pb.bpos,st)
        print sf, st, cf
        p = pb.tree.getNode(pb.bpos)
        pb.tree.addNode(p,st)

    for n in pb.tree.nodes: print n.pt

    pg.init()
    sc = pg.display.set_mode((1000,600))
    sc.blit(pb.drawSelf(),(0,0))
    pg.display.flip()
    while True:
        for e in pg.event.get():
            if e.type == MOUSEBUTTONDOWN: sys.exit(0)