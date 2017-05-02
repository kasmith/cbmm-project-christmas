from __future__ import division, print_function
import sys
import random, math
import numpy as np
from scipy.misc import imsave, imshow

ENLARGE_FACTOR = 25

# Close to 25 (enlarge factor), and keeps dims multiples of 4
X_PAD = 26
Y_PAD = 24

SCREEN_X = 1000 - X_PAD
SCREEN_Y = 620 - Y_PAD

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

def draw_rectangle(screen, rectangle, color=BLACK, fill=False):
    if not fill:
        screen[rectangle[TOP_LEFT][X]:rectangle[BOTTOM_RIGHT][X], rectangle[TOP_LEFT][Y]] = color
        screen[rectangle[TOP_LEFT][X]:rectangle[BOTTOM_RIGHT][X]+1, rectangle[BOTTOM_RIGHT][Y]] = color
        screen[rectangle[TOP_LEFT][X], rectangle[TOP_LEFT][Y]:rectangle[BOTTOM_RIGHT][Y]] = color
        screen[rectangle[BOTTOM_RIGHT][X], rectangle[TOP_LEFT][Y]:rectangle[BOTTOM_RIGHT][Y]] = color
    else:
        screen[rectangle[TOP_LEFT][X]:rectangle[BOTTOM_RIGHT][X], rectangle[TOP_LEFT][Y]:rectangle[BOTTOM_RIGHT][Y]] = color

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

def check_overlap(screen, r1, r2):
    screen = np.zeros(screen.shape)
    draw_rectangle(screen, r1, color=1)
    draw_rectangle(screen, r2, color=1)
    
    if np.sum(screen[r1[TOP_LEFT][X]+1:r1[BOTTOM_RIGHT][X], r1[TOP_LEFT][Y]+1:r1[BOTTOM_RIGHT][Y]]) != 0 or np.sum(screen[r2[TOP_LEFT][X]+1:r2[BOTTOM_RIGHT][X], r2[TOP_LEFT][Y]+1:r2[BOTTOM_RIGHT][Y]]) != 0:
        return True
    else:
        return False

def enlarge_walls(screen, enlarge_factor=25):
    shift = new_screen = np.copy(screen)
    #print(new_screen)
    for _ in range(enlarge_factor):
        shift = np.roll(shift, 1, axis=0)
        shift[0] = WHITE
        np.logical_and(new_screen, shift, out=new_screen)
        new_screen *= WHITE
    shift = new_screen
    for _ in range(enlarge_factor):
        shift = np.roll(shift, 1, axis=1)
        shift[:,0] = WHITE
        np.logical_and(new_screen, shift, out=new_screen)
        new_screen *= WHITE
    
    return new_screen

def get_distance(r1, r2):
    r1_center = [(r1[TOP_LEFT][X]+r1[BOTTOM_RIGHT][X])/2, (r1[TOP_LEFT][Y]+r1[BOTTOM_RIGHT][Y])/2]
    r2_center = [(r2[TOP_LEFT][X]+r2[BOTTOM_RIGHT][X])/2, (r2[TOP_LEFT][Y]+r2[BOTTOM_RIGHT][Y])/2]
    r1_r2 = [r1_center[X]-r2_center[X], r1_center[Y]-r2_center[Y]]
    print(np.linalg.norm(r1_r2))
    return np.linalg.norm(r1_r2)

def get_json_walls(screen):
    s = np.copy(screen)
    json_walls = []
    for x in xrange(s.shape[X]):
        y = 0
        while y < s.shape[Y]:
            #print(str(x) + '/1000')
            if s[x,y] == 0:
                bottom_x = x
                bottom_y = y
                i_flag = j_flag = True
                while i_flag or j_flag:
                    if j_flag:
                        bottom_y += 1
                        if bottom_y > s.shape[Y] or np.sum(s[x:bottom_x,y:bottom_y]) > 0:
                            bottom_y -= 1
                            j_flag = False
                    if i_flag:
                        bottom_x += 1
                        if bottom_x > s.shape[X] or np.sum(s[x:bottom_x,y:bottom_y]) > 0:
                            bottom_x -= 1
                            i_flag = False
                json_walls.append([[x, y], [min(bottom_x,SCREEN_X+X_PAD), min(bottom_y, SCREEN_Y+Y_PAD)], [0, 0, 0], 1.0])
                s[x:bottom_x,y:bottom_y] = WHITE
                y = bottom_y
            else:
                y += 1

    return json_walls

def get_json(walls, goals, ball):
    json = '{"Dims": [1000, 620], "Walls": '
    
    print(str(len(walls)) + ' walls')

    json += str(walls)
    json += ', "Ball": '
    json += str(ball)
    json += ', "Name": "size_1_a", "Occluders": [], "AbnormWalls": [], "ClosedEnds": [1, 3, 2, 4], "Goals": '
    json += str(goals)
    json += ', "Paddle": null, "BKColor": [255, 255, 255]}'

    return json

def get_trial(name='auto_trial', num_rects=10):
    screen = np.zeros((SCREEN_X+1, SCREEN_Y+1)) + WHITE

    # make walls
    new = get_random_rectangle(screen_size=(SCREEN_X // 2, SCREEN_Y // 2), min_size=(75, 75))
    draw_rectangle(screen, new)
    num_rects -= 1
    rectangles = [new]
    while num_rects > 0:
        new = get_random_rectangle(min_size=(50, 50))
        has_overlap = False
        for r in rectangles:
            has_overlap = has_overlap or check_overlap(screen, new, r)
            if has_overlap:
                draw_rectangle(screen, new)
                rectangles.append(new)
                num_rects -= 1
                break

    merge_rectangles(screen, rectangles)
    screen = np.pad(screen, ((0, X_PAD), (0, Y_PAD)), 'constant', constant_values=WHITE)
    screen = enlarge_walls(screen)
    walls = get_json_walls(screen)

    # make goals
    goals = []
    for color in range(201, 202+1):
        has_overlap = True
        while has_overlap:
            has_overlap = False
            goal = get_random_rectangle(min_size=(30, 20), max_size=(80, 70))
            for w in walls:
                has_overlap = has_overlap or check_overlap(screen, goal, w)
                if has_overlap:
                    break
            if not has_overlap:
                for g in goals:
                    has_overlap = has_overlap or check_overlap(screen, goal, g)
                    if has_overlap:
                        break
            if not has_overlap:
                if color == 201:
                    has_overlap = True
                    for r in rectangles:
                        if check_overlap(screen, goal, r):
                            has_overlap = False
                            break
                if color == 202:
                    for r in rectangles:
                        has_overlap = has_overlap or check_overlap(screen, goal, r)
                        if has_overlap:
                            break
                
        goal += [color, [-255*(color-202), 255*(color-201), 0]]
        goals.append(goal)

    # place ball
    has_overlap = True
    while has_overlap:
        has_overlap = False
        ball_rect = get_random_rectangle(min_size=(45, 45), max_size=(45, 45))
        for w in walls:
            has_overlap = has_overlap or check_overlap(screen, ball_rect, w)
            if has_overlap:
                break
        if not has_overlap:
            for g in goals:
                has_overlap = has_overlap or check_overlap(screen, ball_rect, g)
                if has_overlap:
                    break
        if not has_overlap:
            has_overlap = True
            for r in rectangles:
                if check_overlap(screen, ball_rect, r):
                    has_overlap = False
                    break
        if not has_overlap:
            has_overlap = (get_distance(ball_rect, goals[0]) < 350)
    # TODO Get ball direction by pointing it towards goal
    ball = [[(ball_rect[TOP_LEFT][X]+ball_rect[BOTTOM_RIGHT][X])//2, (ball_rect[TOP_LEFT][Y]+ball_rect[BOTTOM_RIGHT][Y])//2], [132.8662569668213, -268.9731543474675], 20, [0, 0, 255], 1.0]

    draw_rectangle(screen, goals[0], color=3*WHITE//4, fill=True)
    draw_rectangle(screen, goals[1], color=3*WHITE//4, fill=True)
    draw_rectangle(screen, ball_rect, color=WHITE//4, fill=True)
    imsave('trial_images/' + name + '.png', np.transpose(screen))
    
    return get_json(walls, goals, ball)

if __name__ == '__main__':
    if len(sys.argv) > 1:
        num_rects = int(sys.argv[1])
    else:
        num_rects = 10
        
    trials_dir = 'auto_trials'
    
    for i in range(10):
        with open(trials_dir + '/auto_trial_' + str(i) + '.json', 'w') as f:
            f.write(get_trial('auto_trial_' + str(i), num_rects=num_rects))
            print('Trial ' + str(i) + ' done.')
