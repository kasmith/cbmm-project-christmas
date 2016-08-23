from __future__ import division
from physicsTable import *
from physicsTable.constants import *
    
def extractVelocity(tr, t=0.):
    tb = tr.makeTable()
    if t > 0:
        tb.step(t)
    return tb.balls.getvel()
    
def getGoal(tr):
    tb = tr.makeTable()
    running = True
    while running:
        r = tb.step()
        if r is not None:
            running = False
    if r == GREENGOAL:
        return 'green'
    else:
        return 'red'
