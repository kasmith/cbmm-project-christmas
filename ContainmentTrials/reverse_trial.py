from physicsTable import *
import sys

if __name__ == '__main__':
    assert len(sys.argv) == 3, "Must provide two names -- to reverse and new file"
    tr = loadTrial(sys.argv[1])
    b = tr.ball
    tr.ball = (b[0], (-b[1][0], -b[1][1]), b[2], b[3], b[4])
    tr.save(sys.argv[2], askoverwrite = True)