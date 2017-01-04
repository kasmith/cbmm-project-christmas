from physicsTable import *
import sys

def resize_trial(tr, pct = .75):
    midpt = [tr.dims[0]/2., tr.dims[1]/2.]
    def shrink_pt(p):
        newp = [p[0]-midpt[0], p[1]-midpt[1]]
        newp = map(lambda x: x*pct, newp)
        newp = [newp[0]+midpt[0], newp[1]+midpt[1]]
        newp = map(int, newp)
        return newp
    newtr = RedGreenTrial(tr.name+"_"+str(int(pct*100)), tr.dims, tr.ce,
                          tr.bkc, tr.dbv, tr.dbr, tr.dbc, tr.dpl, tr.dwc,
                          tr.doc, tr.dpc)
    b = tr.ball
    newtr.addBall(shrink_pt(b[0]), b[1],b[2],b[3],b[4])
    for w in tr.normwalls:
        newtr.addWall(shrink_pt(w[0]), shrink_pt(w[1]), w[2], w[3])
    for g in tr.goals:
        newtr.addGoal(shrink_pt(g[0]), shrink_pt(g[1]), g[2], g[3])
    newtr.normalizeVel()
    return newtr


if __name__ == '__main__':
    assert len(sys.argv) > 1, "Must provide at least one trial to resize"
    for a in sys.argv[1:]:
        tr = loadTrial(a)
        ntr75 = resize_trial(tr,.75)
        ntr75.save()
        ntr50 = resize_trial(tr, .5)
        ntr50.save()