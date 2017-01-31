from __future__ import division
from physicsTable import *
from physicsTable.constants import *
from GetRRT import *
import os,sys

trpath = os.path.join('..','ContainmentTrials','exp_trials')
trials = []
for tnm in os.listdir(trpath):
    if tnm[-4:] == '.ptr':
        trials.append(os.path.join(trpath, tnm))
trials.sort(reverse=True)

#trials = trials[21:]

if __name__ == '__main__':

    RRT_FAILURE_THRESHOLD = 20

    filename = 'RRTTest_N' + str(RRT_FAILURE_THRESHOLD) + '.csv' 

    f = open(filename,'a')
    f.write('Trial,Type,GReach,GLen,RReach,RLen,TotalSteps,IsContained\n')
    f.close()

    for tr in trials:
        f = open(filename,'a')
        
        t = loadTrial(tr)
        rrt = RRTstar(t)

        # Uncomment lines below to visually display search
        #pg.init()
        #sc = pg.display.set_mode((1000,600))
        def draw():
            #sc.blit(rrt.drawSelf(),(0,0))
            #pg.display.flip()
            return

        rrt.searchTillFailure(RRT_FAILURE_THRESHOLD,draw)
        greach = rrt.gsteps > 0
        rreach = rrt.rsteps > 0
        is_contained = (greach and not rreach) or (rreach and not greach)

        f.write(t.name + ',RRT,' + str(greach) + ',' + str(rrt.gsteps) + ',' + 
                str(rreach) + ',' + str(rrt.rsteps) + ',' + str(rrt.steps) + ',' +
                str(is_contained) + '\n')

        print tr, "done"

        f.close()
