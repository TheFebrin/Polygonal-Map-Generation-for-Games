from __future__ import absolute_import
from src.voronoi import VoronoiPolygons
import matplotlib.pyplot as plt


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

        self.centers, self.corners, self.edges = self.initialize_graph()

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

        corners_inside = [
                (0 <= corner.x <= 1) and 
                (0 <= corner.y <= 1) and 
                ((0 != corner.x and 1 != corner.x) or 
                (0 != corner.y and 1 != corner.y)) 
            for corner in corners]

        # setting neighbors and corners lists for each center
        for i, c in enumerate(centers):
            c.neighbors = [centers[k] for k in self._neighbors[i]]
            c.corners = [corners[k] for k in self._regions[i] if corners_inside[k]]

        for i, corners_list in enumerate(self._regions):
            for cor in corners_list:
                corners[cor].touches.append(i)

        edges = {}
        for c1, neighbours_list in enumerate(self._neighbors):
            for i, c2 in enumerate(neighbours_list):
                if (c1, c2) in edges:
                    continue

                cor1, cor2 = self._intersecions[c1][i]
                edge = Edge(centers[c1], centers[c2], corners[cor1], corners[cor2])
                centers[c1].borders.append(edge)
                centers[c2].borders.append(edge)
                corners[cor1].protrudes.append(edge)
                corners[cor2].protrudes.append(edge)
                corners[cor1].adjacent.append(cor2)
                corners[cor2].adjacent.append(cor1)

                edges[(c1, c2)] = edge

        corners = [corner for i,corner in enumerate(corners) if corners_inside[i]]
        edges = list(edges.values())

        return centers, corners, edges

    def plot_map(self):
        plt.figure(figsize=(10,10))
        plt.rcParams['axes.facecolor'] = 'grey'
        
        plt.scatter(
            [center.x for center in self.centers], 
            [center.y for center in self.centers], c='red')
        plt.scatter(
            [corner.x for corner in self.corners], 
            [corner.y for corner in self.corners], c='blue')
        for edge in self.edges:
            plt.plot([edge.v0.x, edge.v1.x], [edge.v0.y, edge.v1.y], c='white')
            plt.plot([edge.d0.x, edge.d1.x], [edge.d0.y, edge.d1.y], c='black')

        plt.xlim(0,1)
        plt.ylim(0,1)
        plt.show()


if __name__ == '__main__':
    g = Graph(N=25, iterations=2)
    g.plot_map()
