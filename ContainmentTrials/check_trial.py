from physicsTable import *
from physicsTable.constants import *
import os, sys

MAXTIME = 15.

def reverse_ball(tr):
    tr.ball = (tr.ball[0], [-tr.ball[1][0], -tr.ball[1][1]], tr.ball[2], tr.ball[3], tr.ball[4])
    return tr

def check_timing(tr, full_max = 100.):
    tab = tr.makeTable()
    running = True
    while running:
        r = tab.step(maxtime = full_max)
        if r is not None:
            running = False
    return r, tab.tm


if __name__ == '__main__':

    assert len(sys.argv) > 1, "Must provide at least one file to test"

    for a in sys.argv[1:]:
        try:
            tr = loadTrial(a)
        except:
            assert False, "Must provide a valid file path to test"

        g, tm = check_timing(tr)
        if g == TIMEUP:
            print "Ball took WAAAY to long to hit the goal (>100s)", a
        elif g != GREENGOAL:
            print "Ball hits the red goal normally; must hit green;", a
        elif tm >= MAXTIME:
            print "Hitting the goal takes over", MAXTIME, "seconds normally;", a
        else:
            tr = reverse_ball(tr)
            g, tm = check_timing(tr)
            if g == TIMEUP:
                print "Ball took WAAAY to long to hit the goal in reverse (>100s)", a
            elif g != GREENGOAL:
                print "Ball hits the red goal in reverse; must hit green;", a
            elif tm >= MAXTIME:
                print "Hitting the goal takes over", MAXTIME, "seconds in reverse;", a
            else:
                print "All checks clear:", a
