from __future__ import division
from physicsTable import *
from physicsTable.constants import *
import pygame as pg
import random, os, sys
import numpy as np
import json

defVel = 300
nTrials = 20
# modified trial folder:
#trialfolder = os.path.join('..','public_html','trials')
trialfolder = os.path.join('..','psiturk-rg','templates', 'trials')

#random.seed(10001)

def makeRect(ul, lr):
    return pg.Rect(ul, (lr[0]-ul[0],lr[1]-ul[1]))

def checkOverlap(trial):
    walls = [makeRect(w[0],w[1]) for w in trial.normwalls]
    goals = [makeRect(g[0],g[1]) for g in trial.goals]
    objs = walls + goals
    b = trial.ball
    if b is not None:
        br = makeRect((b[0][0]-b[2],b[1][0]-b[2]),(b[2]*2,b[2]*2))
        objs.append(br)
        
    for i in range(len(objs) - 1):
        o = objs[i]
        cls = o.collidelist(objs[(i+1):])
        if cls != -1: return True
    return False

def checkCoverage(trial, minsteps = 20, FPS = 40.):
    tb = trial.makeTable()
    notcovered = True
    covered = False
    ncovs = 0
    
    while tb.step(1/FPS) is None:
        if tb.fullyOcc():
            notcovered = False
            ncovs += 1
            if ncovs >= minsteps: covered = True
        else: ncovs = 0
    
    return [notcovered, covered]

def checkSmallVel(v):
    x = abs(v[0])
    y = abs(v[1])
    atan = np.arctan(y/x)
    return (atan < np.pi/40) or (atan > 19*np.pi/40)

def MakeRandTrial(name, blocks, occs, covered = False, blockdims = (50,300), occdims = (150, 400), res = (1000, 620), maxfails = 10000):
    fails = 0
    chk = False
    tr = RedGreenTrial(name, res, def_ball_vel = defVel)
    
    blocksize = (random.randint(blockdims[0],blockdims[1]),random.randint(blockdims[0],blockdims[1]))
    pos = (random.randint(0,res[0]-blocksize[0]),random.randint(0,res[1]-blocksize[1]))
    lr = (pos[0]+blocksize[0],pos[1]+blocksize[1])
    tr.addGoal(pos,lr,REDGOAL,RED)
    
    chk = False
    while not chk:
        blocksize = (random.randint(blockdims[0],blockdims[1]),random.randint(blockdims[0],blockdims[1]))
        pos = (random.randint(0,res[0]-blocksize[0]),random.randint(0,res[1]-blocksize[1]))
        lr = (pos[0]+blocksize[0],pos[1]+blocksize[1])
        tr.addGoal(pos,lr,GREENGOAL,GREEN)
        if checkOverlap(tr):
            fails += 1
            tr.goals = [tr.goals[0]]
        else: chk = True
        if fails > maxfails:
            print "Resetting trial"
            return MakeRandTrial(name,blocks,occs,covered,blockdims,occdims,res,maxfails)
            
    for i in range(blocks):
        chk = False
        while not chk:
            blocksize = (random.randint(blockdims[0],blockdims[1]),random.randint(blockdims[0],blockdims[1]))
            pos = (random.randint(0,res[0]-blocksize[0]),random.randint(0,res[1]-blocksize[1]))
            lr = (pos[0]+blocksize[0],pos[1]+blocksize[1])
            tr.addWall(pos,lr)
            if checkOverlap(tr):
                fails += 1
                tr.normwalls = tr.normwalls[:-1]
            else: chk = True
            if fails > maxfails:
                print "Resetting trial"
                return MakeRandTrial(name,blocks,occs,covered,blockdims,occdims,res,maxfails)
    
    for i in range(occs):
        chk = False
        while not chk:
            blocksize = (random.randint(blockdims[0],blockdims[1]),random.randint(blockdims[0],blockdims[1]))
            pos = (random.randint(0,res[0]-blocksize[0]),random.randint(0,res[1]-blocksize[1]))
            lr = (pos[0]+blocksize[0],pos[1]+blocksize[1])
            noc = pg.Rect(pos,blocksize)
            if noc.collidelist([makeRect(o[0],o[1]) for o in tr.occs]) == -1:
                tr.addOcc(pos,lr)
                chk = True
            else:
                fails += 1
    
    bsize = tr.dbr
    chk = False
    while not chk:
        bpos = (random.randint(bsize, res[0]-bsize), random.randint(bsize,res[1]-bsize))
        
        vchk = False
        while not vchk:
            bvel = (random.random(), random.random())
            if not checkSmallVel(bvel): vchk = True
        
        tr.addBall(bpos, bvel)
        if checkOverlap(tr):
            fails += 1
            tr.ball = None
        else: chk = True
        if fails > maxfails:
            print "Resetting trial"
            return MakeRandTrial(name,blocks,occs,covered,blockdims,occdims,res,maxfails)
            
    tr.normalizeVel()
    
    if not tr.checkConsistency(10000):
        return MakeRandTrial(name,blocks,occs,covered,blockdims,occdims,res,maxfails)
        
    if tr.checkConsistency(3000):
        print "Too short"
        return MakeRandTrial(name,blocks,occs,covered,blockdims,occdims,res,maxfails)
    
    coverage = checkCoverage(tr)
    if covered:
        if not coverage[1]: return MakeRandTrial(name,blocks,occs,covered,blockdims,occdims,res,maxfails)
    else:
        if not coverage[0]: return MakeRandTrial(name,blocks,occs,covered,blockdims,occdims,res,maxfails)
    
    return tr
    
    
if __name__ == '__main__':

    trlist = []

    # Save qualitative trials
    qfiles = os.listdir(os.curdir)
    for f in qfiles:
        if f[-4:] == '.ptr':
            print f
            tr = loadTrial(os.path.join(os.curdir,f))
            tr.jsonify(f[:-4]+'.json',trialfolder,False)
            trlist.append(f[:-4])


    npcd = int(nTrials - len(trlist) / 5)

    # Make random trials
    for b in range(1,6):
        for i in range(npcd):
            nm = "RTr_Bl" + str(b) + "_" + str(i)
            t = MakeRandTrial(nm, b, 0, False)
            t.save(nm+'.ptr',askoverwrite=False)
            t.jsonify(nm+".json",trialfolder,askoverwrite=False)
            trlist.append(nm)

    fllist = open(os.path.join(trialfolder,'TrList.json'),'w')
    fllist.write(json.dumps(trlist))
    fllist.close()
