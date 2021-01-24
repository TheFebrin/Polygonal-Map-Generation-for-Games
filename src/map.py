from __future__ import absolute_import
from voronoi import VoronoiPolygons


class Center:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.neighbors = []
        self.borders = []
        self.corners = []


class Corner:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.touches = []
        self.protrudes = []
        self.adjacent = []


class Edge:
    def __init__(self, center1, center2, corner1, corner2):
        self.d0 = center1
        self.d1 = center2
        self.v0 = corner1
        self.v1 = corner2


class Graph:
    def __init__(self, N: int = 25, iterations: int = 2):
        voronoi_polygons = VoronoiPolygons(N=N)
        self._points, self._centroids, self._vertices, self._regions, \
            self._neighbors, self._intersecions \
            = voronoi_polygons.generate_Voronoi(iterations=iterations)

        self._centers, self._corners, self._edges = self.initialize_graph()

    def initialize_graph(self):
        # creating center object for each point
        centers = []
        for p in self._points:
            center = Center(p[0], p[1])
            centers.append(center)

        # creating corner object for each vertex
        corners = []
        for v in self._vertices:
            corner = Corner(v[0], v[1])
            corners.append(corner)

        # setting neighbors and corners lists for each center
        for i, c in enumerate(centers):
            c.neighbors = [centers[k] for k in self._neighbors[i]]
            c.corners = [corners[k] for k in self._regions[i]]

        for i, corners_list in enumerate(self._regions):
            for cor in corners_list:
                corners[cor].touches.append(i)

        edges = {}
        for c1, neighbours_list in enumerate(self._neighbors):
            for i, c2 in enumerate(neighbours_list):
                if (c1, c2) in edges:
                    continue

                cor1, cor2 = self._intersecions[c1][i]
                print(c1, c2, cor1, cor2)
                # TODO: FIX TypeError: only integer scalar arrays can be converted to a scalar index

                edge = Edge(centers[c1], centers[c2], corners[cor1], corners[cor2])
                centers[c1].borders.append(edge)
                centers[c2].borders.append(edge)
                corners[cor1].protrudes.append(edge)
                corners[cor2].protrudes.append(edge)
                corners[cor1].adjacent.append(cor2)
                corners[cor2].adjacent.append(cor1)

                edges[(c1, c2)] = edge

        return centers, corners, edges


if __name__ == '__main__':
    g = Graph(N=25, iterations=2)
