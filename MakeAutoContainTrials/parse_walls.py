import sys
import numpy as np
import pygame as pg
from pygame.constants import *
from physicsTable import *
from trial_generator import get_json_walls, WHITE, BLACK, X, Y

def main(): 
    assert len(sys.argv) == 2, "Need trial"

    # get trial pixel array
    tr = loadTrialFromJSON(sys.argv[1])
    tb = tr.makeTable()
    surface = tb.draw()
    screen = pg.surfarray.array2d(surface)
    # leave only walls on image
    m = np.max(screen)
    screen[screen != BLACK] = m
    # normalize to [BLACK, WHITE] range
    screen[screen == m] = WHITE

    walls = get_json_walls(screen)

    json = '{"Dims": [' + str(screen.shape[X]) + ', ' + str(screen.shape[Y]) + '], "Walls": '
    json += str(walls)
    json += '}'

    with open(sys.argv[1][:-5] + '_walls.json', 'w' ) as f:
        f.write(json)

if __name__ == '__main__':
    main()
    

