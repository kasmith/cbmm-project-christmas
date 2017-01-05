from physicsTable import *
from copy import deepcopy
import sys

if __name__ == '__main__':
    assert len(sys.argv) == 3, "Must provide two trials -- copier and copyee"
    tr1 = loadTrial(sys.argv[1])
    tr2 = loadTrial(sys.argv[2])
    tr2.ball = deepcopy(tr1.ball)
    tr2.save(sys.argv[2], askoverwrite=False)