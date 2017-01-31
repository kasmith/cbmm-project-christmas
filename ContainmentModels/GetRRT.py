from __future__ import division
from PlanningBase import *
from hulls import *
import sys

class RRTstar(PlanningBase):
    # Initialize with some constants calculated
    def __init__(self, tr, steersize = None):
        super(RRTstar,self).__init__(tr, steersize)
        freesize = len(self.free)
        self.gamma = 2*np.sqrt(1.5)*np.sqrt(freesize/np.pi)

    def addNode(self):
        randpos = self.sampleFree()
        nearest = self.tree.nearest(randpos)
        newpt = self.steer(nearest.pt,randpos)

        if self.collisionFree(nearest.pt,newpt) is True:
            # Find all near nodes within a predefined ball (shrinks with more vertices)
            V = self.tree.nVertices()
            ballsize = min(self.ssize,self.gamma * np.sqrt(np.log(V)/V))
            nearnodes = self.tree.near(newpt, ballsize)
            xmin = nearest
            cmin = nearest.cost + nearest.distance(newpt)

            # Find the closest, least costly node
            for xnear in nearnodes:
                newcost = xnear.cost + xnear.distance(newpt)
                if self.collisionFree(xnear.pt,newpt) and newcost < cmin:
                    xmin = xnear
                    cmin = newcost
            newnode = self.tree.addNode(xmin,newpt,xmin.distance(newpt))
            try:
                self.clearFree( (newpt[0],newpt[1]) )
            except:
                print newpt

            h = self.hitsGoal(newpt)
            if h:
                newnode.markGoal(h)
                self.storeStepsToGoal(h)
                return h
            else:
                # Rewire the tree
                for xnear in nearnodes:
                    newcost = newnode.cost + newnode.distance(xnear.pt)
                    if self.collisionFree(newpt, xnear.pt) and newcost < xnear.cost:
                        xnear.reParent(newnode,newnode.distance(xnear.pt))

            return True
        else: return False

    def sureAdd(self):
        running = True
        while running:
            r = self.addNode()
            if r is not False: return r

    def addTillFailure(self, N = 20):
        ctr = 0
        while ctr < N:
            r = self.addNode()
            if r:
                #print ctr
                return r
            else: ctr += 1
        print 'done'
        return False

    def searchTillFailure(self, N = 20, callback = None):
        running = True
        ctr = 0
        while running:
            ctr += 1
            self.incrSteps()
            r = self.addTillFailure(N)
            if callback: callback()
            #if r == goal: return (r, ctr)
            if self.gsteps > 0 and self.rsteps > 0: 
                return (True, ctr)
            if r is False or ctr > 3000: 
                return (False, ctr)
            if ctr % 500 == 0:
                print str(ctr) + '/ 3000 steps'

    def storeStepsToGoal(self, goal):
        if goal == GREENGOAL and self.gsteps == -1:
            self.gsteps = self.steps
        elif goal == REDGOAL and self.rsteps == -1:
            self.rsteps = self.steps

    def incrSteps(self):
        self.steps += 1

class RRThull(RRTstar):
    def __init__(self, tr, steersize = None, hullK = 5, hullDist = 100):
        super(RRThull,self).__init__(tr, steersize)
        self.hull = None
        self.k = hullK
        self.hdist = hullDist

    # Recalculates the hull when a node is added (with > 5 nodes)
    def addNode(self):
        an = super(RRThull,self).addNode()
        pts = self.tree.getAllPoints()
        if self.tree.nVertices() >= 5: self.hull = concaveHull(pts,self.k,self.hdist)
        return an

    # Draw the hull as well
    def drawSelf(self, mark = True):
        sc = super(RRThull,self).drawSelf(mark)
        if self.hull is not None:
            newsc = pg.Surface(self.dims)
            newsc.set_alpha(128)
            newsc.blit(sc,(0,0))
            color = (128,128,128)
            pg.draw.polygon(newsc, color, self.hull)
            for n in self.tree.nodes:
                if self.pointWallAdj(n.pt):
                    pg.draw.circle(newsc,(255,0,0),n.pt,3)
            sc.blit(newsc,(0,0))
        return sc

    # Check whether all hull nodes are against a wall
    def searchTillFailure(self, goal, callback = None):
        ctr = 0
        while True:
            ctr += 1
            r = self.sureAdd()
            if callback: callback()
            if r == goal: return (r, ctr)
            if self.hull is not None:
                stop = True
                hidx = 0
                # End if all of the hull nodes are adjacent to a wall
                while stop and hidx < len(self.hull):
                    if not self.pointWallAdj(self.hull[hidx]): stop = False
                    hidx += 1
                if stop: return (False, ctr)


if __name__ == '__main__':
    #rrt = RRTstar(loadTrial(os.path.join('..','ContainmentTrials','exp_trials', 'size_2_c.ptr')))
    if len(sys.argv) > 1:
        trial = sys.argv[1]
        if sys.argv[1][:-4] != '.ptr':
            trial = trial + '.ptr'
    else:
        trial = 'size_1_a.ptr'
    rrt = RRTstar(loadTrial(os.path.join('..','ContainmentTrials','exp_trials', trial)))

    #for i in range(1000):
    #    rrt.sureAdd()

    #print rrt.searchTillFailure(GREENGOAL,20)

    pg.init()
    sc = pg.display.set_mode((1000,600))
    #def dr():
    #    sc.blit(rrt.drawSelf(),(0,0))
    #    pg.display.flip()
    #print rrt.searchTillFailure(REDGOAL,dr)
    #for i in range(2000):
    #    if i % 100 == 0:
    #        print str(i) + ' / 2000'
    #    rrt.sureAdd()
    #    sc.blit(rrt.drawSelf(),(0,0))
    #    pg.display.flip()


    #while rrt.addTillFailure(25):
    #    sc.blit(rrt.drawSelf(),(0,0))
    #    pg.display.flip()
    def draw():
        sc.blit(rrt.drawSelf(),(0,0))
        pg.display.flip()
    rrt.searchTillFailure(15,draw)

    print rrt.greendist, rrt.reddist
    print rrt.gsteps, rrt.rsteps
    while True:
       for e in pg.event.get():
            if e.type == MOUSEBUTTONDOWN: sys.exit(0)
