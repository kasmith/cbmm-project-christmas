from constants import *
from config import *
from parse_walls import trial_segmentation
from scene_graph import SceneGraph
from physicsTable import *
from physicsTable.constants import *
import geometry
import numpy as np

# Helpers for drawing if this is allowed
if USE_PG:
    import pygame as pg
    from pygame.constants import KEYDOWN
    def wait_4_kp(draw_fn, hz=20):
        clk = pg.time.Clock()
        while True:
            draw_fn()
            pg.display.flip()
            for e in pg.event.get():
                if e.type == KEYDOWN:
                    return
            clk.tick(hz)

class TopologyModel(object):
    # Initializes all of the decompositions and graphs
    # Note: requires the goal in the container to be red!
    def __init__(self, trial, use_all_triangulations=True, acd_convexity_by_ball_rad = [1., 2., 4.]):
        # Load in the trial and break down the walls
        self._trial = trial
        self._brad = self._trial.ball[2]
        self._bpos = self._trial.ball[0]
        self._goal_ul = None
        self._goal_lr = None
        for g in self._trial.goals:
            if g[2] == REDGOAL:
                self._goal_ul = g[0]
                self._goal_lr = g[1]
        if self._goal_ul is None:
            raise Exception("No appropriate goal found in the trial")
        self._acd_convexities = acd_convexity_by_ball_rad
        self._ohull, self._islands = trial_segmentation(self._trial)

        # Ear clipping triangulation
        self._tris, self._wound_hull = geometry.ear_clip_with_holes(self._ohull, self._islands)
        self._has_all_tris = False
        if use_all_triangulations:
            self.make_all_triangulations()
        else:
            self._all_tris = [self._tris]
        self._tri_graphs = [SceneGraph(tri) for tri in self._all_tris]
        self._tri_geosizes = [self._get_max_geodesic(g) for g in self._tri_graphs]
        self._tri_goaldists = [self._get_min_goaldist(g) for g in self._tri_graphs]

        # Approximate convex decomposition
        self._acd = [geometry.approximate_convex_decomposition([self._ohull] + self._islands, cvx*self._brad) \
                     for cvx in self._acd_convexities]
        self._acd_graph = [SceneGraph(acd) for acd in self._acd]
        self._acd_geosize = [self._get_max_geodesic(g) for g in self._acd_graph]
        self._acd_goaldist = [self._get_min_goaldist(g) for g in self._acd_graph]

    def make_all_triangulations(self):
        self._all_tris = []
        if not self._has_all_tris:
            for i in range(len(self._wound_hull)):
                newtri = geometry.ear_clip(self._wound_hull[i:] + self._wound_hull[:i])
                self._all_tris.append(newtri)
            self._has_all_tris = True

    def _get_max_geodesic(self, graph):
        return graph.maximum_geodesic_distance(self._bpos)

    def _get_min_goaldist(self, graph):
        # Find where the goal is in relation to graph parts
        goal_pts = [self._goal_ul]
        goal_ur = [self._goal_lr[0], self._goal_ul[1]]
        goal_ll = [self._goal_ul[0], self._goal_lr[1]]

        if not all([graph.same_segment(g, goal_ur) for g in goal_pts]):
            goal_pts.append(goal_ur)
        if not all([graph.same_segment(g, goal_ll) for g in goal_pts]):
            goal_pts.append(goal_ll)
        if not all([graph.same_segment(g, self._goal_lr) for g in goal_pts]):
            goal_pts.append(self._goal_lr)

        dists = [graph.point_2_point_distance(g, self._bpos) for g in goal_pts]
        return min(dists)

    def get_acd_stats(self):
        rdict = {}
        for cvx, gs, gd, dtg in zip(self._acd_convexities, self._acd_graph, self._acd_geosize, self._acd_goaldist):
            sz = gs.size
            rdict[cvx] = {'size': sz,
                          'max_geodesic_dist': gd,
                          'min_dist_to_goal': dtg}
        return rdict
    acd = property(get_acd_stats)


    def get_tri_stats(self):
        return {'size': np.mean([g.size for g in self._tri_graphs]),
                'max_geodesic_dist': np.mean(self._tri_geosizes),
                'min_dist_to_goal': np.mean(self._tri_goaldists)}
    triangulation = property(get_tri_stats)


    def _draw_edge_and_point(self, polylist, edge_col, pt_col):
        assert USE_PG, "PyGame not loaded!"
        tb = self._trial.makeTable()
        s = tb.draw()
        for poly in polylist:
            pg.draw.polygon(s, edge_col, poly, 2)
            for pt in poly:
                pg.draw.circle(s, pt_col, pt, 4)
        return s

    def draw_acd(self, acd_idx = 0, edge_col = (0,255,0), pt_col = (255,0,0)):
        wait_4_kp(lambda: self._draw_edge_and_point(self._acd[acd_idx], edge_col, pt_col))

    def draw_triangles(self, tri_idx = 0, edge_col = (0,255,0), pt_col = (255,0,0)):
        wait_4_kp(lambda: self._draw_edge_and_point(self._all_tris[tri_idx], edge_col, pt_col))

    def draw_all_triangles(self, edge_col = (0,255,0), pt_col = (255,0,0)):
        for i in range(len(self._all_tris)):
            self.draw_triangles(i, edge_col, pt_col)