from physicsTable import *
import pygame as pg
from pygame.constants import *
from operator import itemgetter
import sys

# Constants for ease
L = 101
R = -101
T = 103
B = -103

# Wall class for various operations
class Wall(object):
    def __init__(self, p1, p2):
        self.l = p1[0]
        self.t = p1[1]
        self.r = p2[0]
        self.b = p2[1]
        self.grouped = False
        self.is_touching = []

    # Returns boolean if two walls are touching
    # NOTE: Only works for auto-generated trials where pixels are aligned
    def touches(self, other):
        # Do they touch on the side?
        if self.r == other.l or self.l == other.r:
            # Make sure that there is some overlap (e.g., the bottom of other is not above the top, or top of other not below the bottom)
            return not (self.t > other.b or self.b < other.t)
        # Do they touch on the top or bottom?
        elif self.t == other.b or self.b == other.t:
            # Make sure there is some overlap
            return not (self.r < other.l or self.l > other.r)
        else:
            return False

    # Figures out all touching walls and adds them to internal state
    def get_touch_indices(self, others):
        tidxs = [i for i in range(len(others)) if self.touches(others[i])]
        self.is_touching = [others[i] for i in tidxs]
        return tidxs

    # From a given point, traverses clockwise on the inside to collect points
    def get_next_point_and_wall_and_dir(self, lastpt, dir):
        # Traveling along the bottom wall
        if dir == B:
            # Sort touching walls from left to right
            walls = sort_by_direction(self.is_touching, L)
            for w in walls:
                # Skip anything to the left of the last point
                if w.l > lastpt[0]:
                    # The next wall is under the current one - this wall's top left is new, go down along the left wall
                    if w.t == self.b:
                        return (w.l, w.t), w, L
                    # The next wall is adjacent to this one and continues along the bottom
                    elif (self.r, self.b) == (w.l, w.b):
                        # Check along the bottom of this wall
                        return w.get_next_point_and_wall_and_dir((w.l, w.b), B)
                    # The next wall is to the right of this one
                    elif w.l == self.r:
                        return (self.r, self.b), w, L
            return (self.r, self.b), self, R

        # Traveling along the left wall
        elif dir == L:
            # Sort touching walls from top to bottom
            walls = sort_by_direction(self.is_touching, T)
            for w in walls:
                # Skip anything above the last point
                if w.t > lastpt[1]:
                    # The next wall is to the left of thecurrent one
                    if w.r == self.l:
                        return (w.r, w.t), w, T
                    # The next wall is adjacent and continues along the left
                    elif (self.l, self.b) == (w.l, w.t):
                        return w.get_next_point_and_wall_and_dir((w.l, w.t), L)
                    # The next wall is below the current one
                    elif w.t == self.b:
                        return (self.l, self.b), w, T
            return (self.l, self.b), self, B

        # Traveling along the top wall
        elif dir == T:
            # Sort touching walls from right to left
            walls = sort_by_direction(self.is_touching, R)
            for w in walls:
                # Skip anything to the right of the last point
                if w.r < lastpt[0]:
                    # The next wall is above the current one
                    if w.b == self.t:
                        return (w.r, w.b), w, R
                    # The next wall is adjancent and continues along the top
                    elif (self.l, self.t) == (w.r, w.t):
                        return w.get_next_point_and_wall_and_dir((w.r, w.t), T)
                    # The next wall is to the left of this one
                    elif w.r == self.l:
                        return (self.l, self.t), w, R
            return (self.l, self.t), self, L
        # Traveling along the right wall
        elif dir == R:
            walls = sort_by_direction(self.is_touching, B)
            for w in walls:
                # Skip anything below
                if w.b < lastpt[1]:
                    # The next wall is to the right of the current one
                    if w.l == self.r:
                        return (w.l, w.b), w, B
                    # The next wall is adjancent and continues along the right
                    elif (self.r, self.t) == (w.r, w.b):
                        return w.get_next_point_and_wall_and_dir((w.r, w.b), R)
                    # The next wall is above this one
                    elif w.b == self.t:
                        return (self.r, self.t), w, B
            return (self.r, self.t), self, T

    def get_next_outer_point_and_wall_and_dir(self, lastpt, dir):
        # Traveling along the bottom wall
        if dir == B:
            # Sort touching walls from right to left
            walls = sort_by_outside_direction(self.is_touching, R)
            for w in walls:
                # Skip anything to the right of the last point
                if w.r < lastpt[0]:
                    # The next wall is under the current one - this wall's top left is new, go down along the right wall
                    if w.t == self.b:
                        return (w.r, w.t), w, R
                    # The next wall is adjacent to this one and continues along the bottom
                    elif (self.l, self.b) == (w.r, w.b):
                        # Check along the bottom of this wall
                        return w.get_next_outer_point_and_wall_and_dir((w.r, w.b), B)
                    # The next wall is to the left of this one
                    elif w.r == self.l:
                        return (self.l, self.b), w, R
            return (self.l, self.b), self, L

        # Traveling along the left wall
        elif dir == L:
            # Sort touching walls from bottom to top
            walls = sort_by_outside_direction(self.is_touching, B)
            for w in walls:
                # Skip anything below the last point
                if w.b < lastpt[1]:
                    # The next wall is to the left of thecurrent one
                    if w.r == self.l:
                        return (w.r, w.b), w, B
                    # The next wall is adjacent and continues along the left
                    elif (self.l, self.t) == (w.l, w.b):
                        return w.get_next_outer_point_and_wall_and_dir((w.l, w.b), L)
                    # The next wall is above the current one
                    elif w.b == self.t:
                        return (self.l, self.t), w, B
            return (self.l, self.t), self, T

        # Traveling along the top wall
        elif dir == T:
            # Sort touching walls from left to right
            walls = sort_by_outside_direction(self.is_touching, L)
            for w in walls:
                # Skip anything to the left of the last point
                if w.l > lastpt[0]:
                    # The next wall is above the current one
                    if w.b == self.t:
                        return (w.l, w.b), w, L
                    # The next wall is adjancent and continues along the top
                    elif (self.r, self.t) == (w.l, w.t):
                        return w.get_next_outer_point_and_wall_and_dir((w.l, w.t), T)
                    # The next wall is to the right of this one
                    elif w.l == self.r:
                        return (self.r, self.t), w, L
            return (self.r, self.t), self, R
        # Traveling along the right wall
        elif dir == R:
            walls = sort_by_outside_direction(self.is_touching, T)
            for w in walls:
                # Skip anything above
                if w.t > lastpt[1]:
                    # The next wall is to the right of the current one
                    if w.l == self.r:
                        return (w.l, w.t), w, T
                    # The next wall is adjancent and continues along the right
                    elif (self.r, self.b) == (w.r, w.t):
                        return w.get_next_outer_point_and_wall_and_dir((w.r, w.t), R)
                    # The next wall is below this one
                    elif w.t == self.b:
                        return (self.r, self.b), w, T
            return (self.r, self.b), self, B

    def to_pg_rect(self):
        w = self.r - self.l
        h = self.b - self.t
        return pg.Rect((self.l, self.t), (w,h))

# Converts trial into a set of wall rectangles [right, top, left, bottom]
def convert_trial_2_wallrects(trial):
    return [Wall(w[0],w[1]) for w in trial.normwalls]

def get_topleft_wall(walls):
    best_idx = 0
    most_top = walls[0].t
    most_left = walls[0].l
    for i in range(1,len(walls)):
        w = walls[i]
        if w.t < most_top or \
                (w.t == most_top and w.l < most_left):
            best_idx = i
            most_top = w.t
            most_left = w.l
    return best_idx, walls[best_idx]

def sort_by_direction(walls, dir):
    if dir == L:
        pfnc = lambda x: (x.l, -x.b)
    elif dir == R:
        pfnc = lambda x: (-x.r, x.t)
    elif dir == T:
        pfnc = lambda x: (x.t, x.l)
    elif dir == B:
        pfnc = lambda x: (-x.b, -x.r)

    vals = zip(map(pfnc, walls), walls)
    vsort = sorted(vals, key=itemgetter(0))
    return [w for _, w in vsort]

def sort_by_outside_direction(walls, dir):
    if dir == L:
        pfnc = lambda x: (x.l, x.t)
    elif dir == R:
        pfnc = lambda x: (-x.r, -x.b)
    elif dir == T:
        pfnc = lambda x: (x.t, -x.r)
    elif dir == B:
        pfnc = lambda x: (-x.b, x.l)

    vals = zip(map(pfnc, walls), walls)
    vsort = sorted(vals, key=itemgetter(0))
    return [w for _, w in vsort]

def draw_wall_outlines(surf, walls, color = (255,0,0)):
    for w in walls:
        r = w.to_pg_rect()
        pg.draw.rect(surf, color, r, 2)
    return surf

def draw_everything(table, wall_list = [], ptlist = [], ptcol = (0,255,0)):
    s = table.draw()
    draw_wall_outlines(s, wall_list)
    for p in ptlist:
        pg.draw.circle(s, ptcol, p, 3)

def wait_4_kp(draw_fn, hz):
    clk = pg.time.Clock()
    while True:
        draw_fn()
        pg.display.flip()
        for e in pg.event.get():
            if e.type == KEYDOWN:
                return
        clk.tick(hz)


# Takes in a list of Walls, returns a list including:
# [
#   A list of points that form the inner hull,
#   The walls used to form that hull
# ]
def get_inner_hull(walllist):
    # Start with the upper-left wall
    tl_idx, tl_wall = get_topleft_wall(walls)
    tl_wall.grouped = True
    inc_walls = [tl_wall]
    def add_walls(w1, others):
        tidxs = w1.get_touch_indices(others)
        for i in tidxs:
            ow = others[i]
            if not ow.grouped:
                inc_walls.append(ow)
                ow.grouped = True
                add_walls(ow, others)
        return

    add_walls(tl_wall, walls)

    _, cur_wall = get_topleft_wall(tl_wall.is_touching)
    cur_pt = (cur_wall.l, cur_wall.b)
    cur_traverse = B
    inner_pts = [cur_pt]

    running = True
    while running:
        cur_pt, cur_wall, cur_traverse = cur_wall.get_next_point_and_wall_and_dir(cur_pt, cur_traverse)
        if cur_pt == inner_pts[0]:
            running = False
        else:
            inner_pts.append(cur_pt)

    return inner_pts, inc_walls

def get_outer_hull(wall_list):
    _, cur_wall = get_topleft_wall(wall_list)
    cur_pt = (cur_wall.l, cur_wall.t)
    cur_traverse = T
    outer_pts = [cur_pt]
    while True:
        cur_pt, cur_wall, cur_traverse = cur_wall.get_next_outer_point_and_wall_and_dir(cur_pt, cur_traverse)
        if cur_pt == outer_pts[0]:
            return outer_pts
        else:
            outer_pts.append(cur_pt)

def get_islands(rem_walls):
    islands = []
    while len(rem_walls) > 0:
        tl_idx, tl_wall = get_topleft_wall(rem_walls)
        tl_wall.grouped = True
        this_island = [tl_wall]
        def add_walls(w1, others):
            tidxs = w1.get_touch_indices(others)
            for i in tidxs:
                ow = others[i]
                if not ow.grouped:
                    this_island.append(ow)
                    ow.grouped = True
                    add_walls(ow, others)
            return
        add_walls(tl_wall, rem_walls)
        islands.append(this_island)
        rem_walls = [w for w in rem_walls if w not in this_island]

    island_pts = [get_outer_hull(wl) for wl in islands]
    return island_pts, islands


if __name__ == '__main__':
    if len(sys.argv) == 1:
        tr = loadTrial('automatic_generator/samp.ptr')
    else:
        tr = loadTrialFromJSON(sys.argv[1])
    walls = convert_trial_2_wallrects(tr)

    pg.init()
    s = pg.display.set_mode((1000, 620))
    tb = tr.makeTable()

    wait_4_kp(lambda: draw_everything(tb, []), 20)

    '''
    tl_idx, tl_wall = get_topleft_wall(walls)
    tl_wall.grouped = True
    inc_walls = [tl_wall]

    def add_walls(w1, others):
        tidxs = w1.get_touch_indices(others)
        for i in tidxs:
            ow = others[i]
            if not ow.grouped:
                inc_walls.append(ow)
                ow.grouped = True
                add_walls(ow, others)
        return

    add_walls(tl_wall, walls)

    _, cur_wall = get_topleft_wall(tl_wall.is_touching)
    cur_pt = (cur_wall.l, cur_wall.b)
    cur_traverse = B
    inner_pts = [cur_pt]
    #wait_4_kp(lambda: draw_everything(tb, inc_walls, inner_pts), 20)

    running = True
    while running:
        cur_pt, cur_wall, cur_traverse = cur_wall.get_next_point_and_wall_and_dir(cur_pt, cur_traverse)
        if cur_pt == inner_pts[0]:
            running = False
        else:
            inner_pts.append(cur_pt)
        wait_4_kp(lambda: draw_everything(tb, inc_walls, inner_pts), 20)



    wait_4_kp(lambda: draw_everything(tb, inc_walls, []), 20)
    cur_wall = tl_wall
    cur_pt = (cur_wall.l, cur_wall.t)
    cur_traverse = T
    outer_pts = [cur_pt]
    running = True
    wait_4_kp(lambda: draw_everything(tb, inc_walls, outer_pts), 20)
    while running:
        cur_pt, cur_wall, cur_traverse = cur_wall.get_next_outer_point_and_wall_and_dir(cur_pt, cur_traverse)
        if cur_pt == outer_pts[0]:
            running = False
        else:
            outer_pts.append(cur_pt)
        wait_4_kp(lambda: draw_everything(tb, inc_walls, outer_pts), 20)
    '''

    inner_pts, inc_walls = get_inner_hull(walls)
    wait_4_kp(lambda: draw_everything(tb, inc_walls, inner_pts), 20)

    rem_walls = [w for w in walls if w not in inc_walls]
    #wait_4_kp(lambda: draw_everything(tb, rem_walls, inner_pts), 20)

    islands = get_islands(rem_walls)
    print islands
    for ipt, iwalls in zip(*islands):
        wait_4_kp(lambda: draw_everything(tb, iwalls, ipt), 20)