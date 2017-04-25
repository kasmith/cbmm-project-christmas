from __future__ import division, print_function
import random
import numpy as np
from scipy.misc import toimage, imshow

SCREEN_X = 1000
SCREEN_Y = 620

TOP_LEFT = 0
BOTTOM_RIGHT = 1
X = 0
Y = 1

WHITE = 255
BLACK = 0

def get_random_rectangle(screen_size=(SCREEN_X, SCREEN_Y), min_size=(SCREEN_X // 4, SCREEN_Y // 4), max_size=(SCREEN_X // 2, SCREEN_Y // 2)):
    top_left_x = random.randint(0, screen_size[X] - min_size[X])
    top_left_y = random.randint(0, screen_size[Y] - min_size[Y])

    bottom_right_x = random.randint(top_left_x + min_size[X], top_left_x + max_size[X])
    bottom_right_x = min(bottom_right_x, screen_size[X])
    bottom_right_y = random.randint(top_left_y + min_size[Y], top_left_y + max_size[Y])
    bottom_right_y = min(bottom_right_y, screen_size[Y])
    return [[top_left_x, top_left_y], [bottom_right_x, bottom_right_y]]

def draw_rectangle(screen, rectangle, color=BLACK):
    screen[rectangle[TOP_LEFT][X]:rectangle[BOTTOM_RIGHT][X], rectangle[TOP_LEFT][Y]] = color
    screen[rectangle[TOP_LEFT][X]:rectangle[BOTTOM_RIGHT][X]+1, rectangle[BOTTOM_RIGHT][Y]] = color
    screen[rectangle[TOP_LEFT][X], rectangle[TOP_LEFT][Y]:rectangle[BOTTOM_RIGHT][Y]] = color
    screen[rectangle[BOTTOM_RIGHT][X], rectangle[TOP_LEFT][Y]:rectangle[BOTTOM_RIGHT][Y]] = color

def merge_rectangles(screen, rectangles):
    for r in rectangles:
        screen[r[TOP_LEFT][X]+1:r[BOTTOM_RIGHT][X], r[TOP_LEFT][Y]+1:r[BOTTOM_RIGHT][Y]] = WHITE

def remove_lonely_rectangles(screen, rectangles):
    zero_white_screen = screen - WHITE
    connected_rectangles = []
    for r in rectangles:
        if np.sum(zero_white_screen[r[TOP_LEFT][X]+1:r[BOTTOM_RIGHT][X], r[TOP_LEFT][Y]+1:r[BOTTOM_RIGHT][Y]]) != 0:
            connected_rectangles.append(r)

    return connected_rectangles

def check_overlap(r1, r2):
    screen = np.zeros((SCREEN_X+1, SCREEN_Y+1))
    draw_rectangle(screen, r1, color=1)
    draw_rectangle(screen, r2, color=1)
    
    if np.sum(screen[r1[TOP_LEFT][X]+1:r1[BOTTOM_RIGHT][X], r1[TOP_LEFT][Y]+1:r1[BOTTOM_RIGHT][Y]]) != 0 or np.sum(screen[r2[TOP_LEFT][X]+1:r2[BOTTOM_RIGHT][X], r2[TOP_LEFT][Y]+1:r2[BOTTOM_RIGHT][Y]]) != 0:
        return True
    else:
        return False


def main():
    screen = np.zeros((SCREEN_X+1, SCREEN_Y+1)) + WHITE

    num_rects = 10

    new = get_random_rectangle(screen_size=(SCREEN_X // 2, SCREEN_Y // 2), min_size=(50, 50))
    draw_rectangle(screen, new)
    num_rects -= 1
    rectangles = [new]
    while num_rects > 0:
        new = get_random_rectangle(min_size=(50, 50))
        has_overlap = False
        for r in rectangles:
            has_overlap = has_overlap or check_overlap(new, r)
            if has_overlap:
                draw_rectangle(screen, new)
                rectangles.append(new)
                num_rects -= 1
                break

    merge_rectangles(screen, rectangles)
    imshow(np.transpose(screen))

if __name__ == '__main__':
    main()
