import numpy as np
import geometry

__all__ = ['SceneGraph', 'SceneNode']

# A node in the graph -- remembers the shape of the scene segment and which nodes it's attached to
class SceneNode(object):
    def __init__(self, scene_poly, parent_graph, index=0):
        self._poly = scene_poly
        self._parent = parent_graph
        self._connections = []
        self._index = index
        self._data = {}

    def point_in(self, point):
        return geometry.point_in_convex_poly(point, self._poly)

    def get_poly(self):
        return self._poly
    poly = property(get_poly)

    def get_connections(self):
        return self._connections
    connections = property(get_connections)

    def get_parent(self):
        return self._parent
    parent = property(get_parent)

    def get_index(self):
        return self._index
    index = property(get_index)

    def set_data(self, key, value):
        self._data[key] = value

    def get_data(self, key):
        return self._data[key]

    def clear_data(self):
        self._data = {}

    # Discovers whether there is a connection between two polygons (they share an edge)
    def find_connection(self, node):
        if self in node.connections and node not in self.connections:
            self._connections.append(node)
        for i, v1 in enumerate(self._poly):
            for j, v2 in enumerate(node.poly):
                if all(v1 == v2):
                    if all(self._poly[(i+1) % len(self._poly)] == node.poly[(j+1) % len(node.poly)]) or \
                            all(self._poly[(i+1) % len(self._poly)] == node.poly[(j-1) % len(node.poly)]):
                        self._connections.append(node)
                        node._connections.append(self)

# The overall graph
class SceneGraph(object):
    def __init__(self, polylist):
        self._raw_polys = polylist
        self._nodes = []
        self._size = 0
        # Initialize nodes
        for poly in polylist:
            self._nodes.append(SceneNode(poly, self, self._size))
            self._size += 1
        # Find connections
        for i in range(self._size-1):
            n = self._nodes[i]
            for j in range(i+1, self._size):
                n.find_connection(self._nodes[j])

    def get_size(self):
        return self._size
    size = property(get_size)

    def _get_node_by_point(self, pt):
        for n in self._nodes:
            if n.point_in(pt):
                return n
        raise Exception("Point not in any polygon: " + str(pt))

    # Finds the largest distance between the node with a point and any other node
    def maximum_geodesic_distance(self, init_point):
        dists = np.empty(self.size)
        dists.fill(-1)
        init_node = self._get_node_by_point(init_point)
        search_nodes = [init_node]
        cur_dist = 0
        # Breadth-first search through the nodes
        while len(search_nodes) > 0:
            # Skip anything already marked
            search_nodes = [s for s in search_nodes if dists[s.index] == -1]
            next_search = []
            for s in search_nodes:
                dists[s.index] = cur_dist
                next_search += s.connections
            # Go to the next step
            search_nodes = list(set(next_search))
            cur_dist += 1
        return max(dists)

    # Finds the graph distance between two points
    def point_2_point_distance(self, p1, p2):
        n1 = self._get_node_by_point(p1)
        n2 = self._get_node_by_point(p2)
        # Are they in the same segment?
        if n1 == n2:
            return 0
        # Otherwise, search from n1 until n2 is found
        unsearched = [True for _ in range(self.size)]
        search_nodes = [n1]
        cur_dist = 0
        while len(search_nodes) > 0:
            search_nodes = [s for s in search_nodes if unsearched[s.index]]
            next_search = []
            if n2 in search_nodes:
                return cur_dist
            for s in search_nodes:
                unsearched[s.index] = False
                next_search += s.connections
            search_nodes = list(set(next_search))
            cur_dist += 1

    # Returns whether two points are in the same segment
    def same_segment(self, p1, p2):
        n1 = self._get_node_by_point(p1)
        n2 = self._get_node_by_point(p2)
        return n1 == n2