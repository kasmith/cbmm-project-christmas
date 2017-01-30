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

if __name__ == '__main__':

    RRT_FAILURE_THRESHOLD = 15

    f = open('RRTTest.csv','w')
    f.write('Trial,Type,GReach,GLen,RReach,RLen,TotalSteps,IsContained\n')

    for tr in trials:
        t = loadTrial(tr)

        rrt = RRTstar(t)

        # Uncomment lines below to visually display search
        #pg.init()
        #sc = pg.display.set_mode((1000,600))
        def draw():
            #sc.blit(rrt.drawSelf(),(0,0))
            #pg.display.flip()
            return

        result = rrt.searchTillFailure(REDGOAL,RRT_FAILURE_THRESHOLD,draw)
        greach = result[0] == GREENGOAL
        rreach = result[0] == REDGOAL
        is_contained = (greach and not rreach) or (rreach and not greach)

        f.write(t.name + ',RRT,' + str(greach) + ',' + str(rrt.gsteps) + ',' + 
                str(rreach) + ',' + str(rrt.rsteps) + ',' + str(result[1]) + ',' +
                str(is_contained) + '\n')

        print tr, "done"

    f.close()
