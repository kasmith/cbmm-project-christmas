from __future__ import division
import numpy as np
import scipy as sp
import pygame as pg
from sklearn import neighbors
from matplotlib import path
import copy

# Algorithm from Moreira & Santos (2007) Concave Hull: A K-nearest neighbors...
# http://repositorium.sdum.uminho.pt/bitstream/1822/6429/1/ConcaveHull_ACM_MYS.pdf

# Converts all members of a list to array
def arrayify(ptlist):
    return map(lambda x: np.array(x), ptlist)

# Finds point with min y, or min x of min ys if multiple
def findMinY(ptlist):
    ys = [p[1] for p in ptlist]
    miny = min(ys)
    minpts = [p for p in ptlist if p[1] == miny]
    if len(minpts) == 1: return minpts[0]
    else:
        minxs = [p[0] for p in minpts]
        minx = min(minxs)
        idx = minxs.index(minx)
        return minpts[idx]

# Returns k nearest points to 'point'
def nearestPoints(ptlist, point, k, maxdist = 2000):
    NN = neighbors.NearestNeighbors(k, maxdist, metric = 'euclidean')
    NN.fit(ptlist)
    point = np.array([point]) # f-ing kneighbors not playing nice w/ 1-d arrays
    knidx = NN.kneighbors(point,k,False)
    return [ptlist[i] for i in knidx[0]]

# Returns the rightward angle between vectors v1 and v2
# From http://stackoverflow.com/questions/2827393/angles-between-two-n-dimensional-vectors-in-python
def angleBetween(v1, v2):
    uv1 = v1 / np.linalg.norm(v1)
    uv2 = v2 / np.linalg.norm(v2)
    ang = np.arccos(np.dot(uv1,uv2))
    if np.isnan(ang):
        if (uv1 == uv2).all():
            return 0
        else:
            return np.pi
    # Test for going to the right or left
    if np.cross(v1,v2) < 0: return ang
    else: return 2*np.pi - ang

# Sorts points by order of angles between previous connection and potential connections (descending)
def sortByAngle(ptlist, point, prevpoint):
    prevvect = prevpoint - point
    angles = []
    for i in range(len(ptlist)):
        p = ptlist[i]
        curvect = p - point
        angles.append( (angleBetween(curvect,prevvect),i) )
    sangles = sorted(angles, key = lambda x: x[0], reverse = False)
    return [ptlist[sangles[i][1]] for i in range(len(sangles))]

# Find whether two line segments intersect - return True if they do
def findIntersection(seg1, seg2):
    p1,p2 = seg1
    p3,p4 = seg2

    I1x = (min(p1[0],p2[0]),max(p1[0],p2[0]))
    I2x = (min(p3[0],p4[0]),max(p3[0],p4[0]))

    # Quick check - are they even in the same space
    if I1x[1] <= I2x[0] or I2x[1] <= I1x[0]: return False

    Ia = (max(I1x[0],I2x[0])+.000001,min(I1x[1],I2x[1])-.000001)

    # Special case: one of the lines is vertical
    if p1[0] - p2[0] == 0:
        # Both parallel
        if p3[0] - p4[0] == 0:
            # Note: I think this is good but if things go wrong with vertical stuff, double check
            if min(p1[1],p2[1]) > max(p3[1],p4[1]) or min(p3[1],p4[1]) > max(p1[1],p2[1]): return False
            else: return True
        xcross = p1[0]
        a2 = (p3[1]-p4[1])/(p3[0]-p4[0])
        b2 = p3[1] - a2*p3[0]
        ycross = a2*xcross + b2
        if ycross < max(p1[1],p2[1]) and ycross > min(p1[1],p2[1]): return True
        else: return False
    if p3[0] - p4[0] == 0:
        xcross = p3[0]
        a1 = (p1[1]-p2[1])/(p1[0]-p2[0])
        b1 = p1[1] - a1*p1[0]
        ycross = a1*xcross + b1
        if ycross < max(p3[1],p4[1]) and ycross > min(p3[1],p4[1]): return True
        else: return False

    a1 = (p1[1]-p2[1])/(p1[0]-p2[0])
    a2 = (p3[1]-p4[1])/(p3[0]-p4[0])
    b1 = p1[1] - a1*p1[0]
    b2 = p3[1] - a2*p3[0]

    # Parallel lines
    if a1 == a2:
        # They may have different intercepts
        if b1 != b2: return False
        else: return True
    xi = (b2-b1) / (a1-a2)
    # Make sure intesection is within the relevant x range
    if xi > Ia[0] and xi < Ia[1]: return True
    else: return False

def pointInPoly(poly, point):
    pgn = path.Path(poly)
    return pgn.contains_point(point) == 1

def removearray(L,arr):
    ind = 0
    size = len(L)
    while ind != size and not np.array_equal(L[ind],arr):
        ind += 1
    if ind != size:
        L.pop(ind)
    else:
        raise ValueError('array not found in list.')

def concaveHull(pointlist, k = 5, maxdist = 100):
    pl = copy.deepcopy(pointlist)
    k = max(k,3)
    if len(pl) < 3: raise Exception('No hull possible with < 3 points')
    if len(pl) == 3: return pl # This is the hull
    k = min(k,len(pl)-1)
    firstpt = findMinY(pl)
    hull = [firstpt]
    curpt = firstpt
    removearray(pl,firstpt)
    prevpt = np.array([curpt[0]-1,curpt[1]])
    step = 2
    while ((curpt != firstpt).any() or step ==2) and len(pl) != 0:
        if step == 5: pl.append(firstpt)
        knear = nearestPoints(pl, curpt, min(k,len(pl)), maxdist)
        cpts = sortByAngle(knear,curpt,prevpt)
        running = True
        i = 0
        while running and i < len(cpts):
            cp = cpts[i]
            i += 1
            #if (cp == firstpt).all(): lastpt = 2
            #else: lastpt = 1
            j = 2
            running = False
            while not running and j < step:  #(len(hull)-lastpt):
                existseg = (hull[step-j-1],hull[step-j])
                curseg = (hull[step-2],cp)
                running = findIntersection(existseg,curseg)
                j += 1
        if running:
            return concaveHull(pointlist,k+1) # Didn't find a good point
        prevpt = curpt
        curpt = cp
        hull.append(cp)
        removearray(pl,cp)
        step += 1
    allIn = True
    i = len(pl) - 1
    while allIn and i > 0:
        allIn = pointInPoly(hull,pl[i])
        i -= 1
    if not allIn:
        return concaveHull(pointlist, k+1)
    return hull
