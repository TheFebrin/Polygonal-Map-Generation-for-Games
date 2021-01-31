from __future__ import absolute_import
import queue
import numpy as np
import math
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon
from matplotlib.collections import PatchCollection
from scipy.spatial import ConvexHull
import plotly.graph_objs as go

from src.terrain import TerrainType, lighten_color
from src.voronoi import VoronoiPolygons


class Center:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.neighbors = []
        self.borders = []
        self.corners = []
        self.terrain_type = TerrainType.LAND
        self.height = 0

class Corner:
    def __init__(self, x, y):
        """
        :param x:
        :param y:
        :param:
        :param:
        :param:
        :param:
        :param:
        :param height: height of the corner
        :param downslope: index of the neighbour with the lowest height
        """
        self.x = x
        self.y = y
        self.touches = []
        self.protrudes = []
        self.adjacent = []
        self.terrain_type = TerrainType.LAND
        self.height = 0
        self.downslope = None


class Edge:
    def __init__(self, center1, center2, corner1, corner2):
        self.d0 = center1
        self.d1 = center2
        self.v0 = corner1
        self.v1 = corner2

    def is_edge_to_map_end(self):
        """
        Function defining, whether the edge is connected to the end of the map.
        """
        corner_coordinates = [self.v0.x, self.v0.y, self.v1.x, self.v1.y]
        return any([corner_coordinate in [0, 1] for corner_coordinate in corner_coordinates])


class Graph:
    def __init__(self, N: int = 25, iterations: int = 2):
        voronoi_polygons = VoronoiPolygons(N=N)
        self._points, self._centroids, self._vertices, self._regions, \
            self._neighbors, self._intersecions \
            = voronoi_polygons.generate_Voronoi(iterations=iterations)

        self.centers, self.corners, self.edges = self.initialize_graph()
        self.rivers = []  # type: List[List[int]]

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
                corners[cor].touches.append(centers[i])

        edges = {}
        for c1, neighbours_list in enumerate(self._neighbors):
            for i, c2 in enumerate(neighbours_list):
                if (c1, c2) in edges or (c2, c1) in edges:
                    continue

                cor1, cor2 = self._intersecions[c1][i]
                edge = Edge(centers[c1], centers[c2], corners[cor1], corners[cor2])
                centers[c1].borders.append(edge)
                centers[c2].borders.append(edge)
                corners[cor1].protrudes.append(edge)
                corners[cor2].protrudes.append(edge)
                corners[cor1].adjacent.append(corners[cor2])
                corners[cor2].adjacent.append(corners[cor1])

                edges[(c1, c2)] = edge

        corners = [corner for i, corner in enumerate(corners) if corners_inside[i]]
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

    def plot_full_map(self, debug_height=False, river_arrows=False):
        """
        Here the next adjustments will be added to create a complete map.
        """
        fig, ax = plt.subplots(figsize=(10, 10))

        polygons = [self._center_to_polygon(center) for center in self.centers]
        p = PatchCollection(polygons, match_original=True)
        ax.add_collection(p)
        if debug_height:
            for corner in self.corners:
                plt.annotate(
                    f"{round(corner.height, 1)}", (corner.x, corner.y), 
                    color='white', backgroundcolor='black'
                )

        def drawArrow(A, B):
            plt.arrow(
                A[0], A[1], B[0] - A[0], B[1] - A[1],
                head_width=0.015, length_includes_head=True
            )

        for corner in self.corners:
            if corner.downslope is not None:
                adjacent = corner.adjacent[corner.downslope]
                drawArrow(A=(corner.x, corner.y), B=(adjacent.x, adjacent.y))

        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        plt.show()

    def plot_3d_height_map(self):
        """
        Function for plotting terrain height
        (based on the height of the corners), as a plotly wireframe
        """
        lines = []
        line_marker = dict(color='#0066FF', width=2)

        for e in self.edges:
            lines.append(go.Scatter3d(
                x=np.array([e.v0.x, e.v1.x]),
                y=np.array([e.v0.y, e.v1.y]),
                z=np.array([e.v0.height, e.v1.height]),
                mode='lines',
                line=line_marker,
            ))

        layout = go.Layout(
            title='Height Map',
            scene=dict(
                xaxis=dict(
                    gridcolor='rgb(255, 255, 255)',
                    zerolinecolor='rgb(255, 255, 255)',
                    showbackground=True,
                    backgroundcolor='rgb(230, 230,230)'
                ),
                yaxis=dict(
                    gridcolor='rgb(255, 255, 255)',
                    zerolinecolor='rgb(255, 255, 255)',
                    showbackground=True,
                    backgroundcolor='rgb(230, 230,230)'
                ),
                zaxis=dict(
                    gridcolor='rgb(255, 255, 255)',
                    zerolinecolor='rgb(255, 255, 255)',
                    showbackground=True,
                    backgroundcolor='rgb(230, 230,230)'
                ),
                aspectratio=dict(
                    x=1,
                    y=1,
                    z=0.2
                )
            ),
            showlegend=False,
        )

        fig = go.Figure(data=lines, layout=layout)
        fig.show()


    def _center_to_polygon(self, center):
        """
        Helper function for plotting, which takes the center and returns a polygon which can be plotted.
        """
        if center.terrain_type is TerrainType.LAND:
            color = lighten_color('green', amount = 1 + center.height)
        elif center.terrain_type is TerrainType.OCEAN:
            color = 'blue'
        elif center.terrain_type is TerrainType.COAST:
            color = 'yellow'
        elif center.terrain_type is TerrainType.LAKE:
            color = 'lightblue'
        else:
            raise AttributeError(f'Unexpected terrain type: {center.terrain_type}')

        corner_coordinates = np.array([[corner.x, corner.y] for corner in center.corners])
        if self._is_center_a_map_corner(center):
            corner_coordinates = np.append(corner_coordinates, self._nearest_map_corner(corner_coordinates))
            corner_coordinates = corner_coordinates.reshape(-1, 2)
        hull = ConvexHull(corner_coordinates)
        vertices = hull.vertices
        vertices = np.append(vertices, vertices[0])
        xs, ys = corner_coordinates[vertices, 0], corner_coordinates[vertices, 1]
        return Polygon(np.c_[xs, ys], facecolor=color, edgecolor='black', linewidth=2)

    def _is_center_a_map_corner(self, center):
        """
        Function returns True only when a center is in a one of 4 corners of the [0, 1]^2.
        """
        corner_coordinates = np.array([[corner.x, corner.y] for corner in center.corners])
        xs, ys = corner_coordinates.T
        return (np.any(xs == 0) or np.any(xs == 1)) and (np.any(ys == 0) or np.any(ys == 1))

    def _nearest_map_corner(self, corner_coordinates):
        """
        Assumes that a coordinates belong to the corner being in the corner of the map.
        """
        if np.any(corner_coordinates[:, 0] == 0):
            if np.any(corner_coordinates[:, 1] == 0):
                return [0, 0]
            else:
                return [0, 1]
        else:
            if np.any(corner_coordinates[:, 1] == 0):
                return [1, 0]
            else:
                return [1, 1]
            
    def assign_corner_elevations(self, borders=None):
        '''
        Runs BFS from every border corner to calculate height of every corner. 
        '''
        for corner in self.corners:
            corner.height = float('inf')
        border_corners = [
            corner for corner in self.corners 
            if corner.x == 0 or corner.x == 1 or corner.y == 0 or corner.y == 1
        ]
        for border in border_corners:
            q = queue.Queue()
            border.height = 0
            q.put(border)
            while not q.empty():
                current_corner = q.get()
                for adjacent_corner in current_corner.adjacent:
                    new_elevation = current_corner.height + 0.01
                    if (current_corner.terrain_type != TerrainType.OCEAN and
                        current_corner.terrain_type != TerrainType.LAKE and
                        adjacent_corner.terrain_type != TerrainType.OCEAN and
                        adjacent_corner.terrain_type != TerrainType.LAKE):
                        new_elevation += 1
                    if adjacent_corner.height > new_elevation:
                        adjacent_corner.height= new_elevation
                        q.put(adjacent_corner)
        for corner in self.corners:
            if corner.terrain_type == TerrainType.LAKE:
                corner.height -= 1
                
    def assign_center_elevations(self):
        '''
        Calculates height for every center by taking the mean height of corners that surround it.
        '''
        for center in self.centers:
            corners_heights = [corner.height for corner in center.corners]
            center.height = sum(corners_heights) / len(corners_heights)
            if center.terrain_type == TerrainType.LAKE:
                center.height -= 1
            
    def redistribute_elevations(self, scale_factor = 1.1):
        sorted_corners = sorted(self.corners, key = lambda c: c.height)
        for i, corner in enumerate(sorted_corners):
            y = i / len(sorted_corners)
            x = math.sqrt(scale_factor) - math.sqrt(scale_factor * (1 - y))
            corner.height = x
        
    def create_rivers(self, n, min_height):
        """
        Rivers flow from high elevations down to the coast.
        Having elevations that always increase away from the coast means
        that there’s no local minima that complicate river generation

        This function creates `n` rivers. It draws a random start position for
        each river that is >= min_height.

        :param n: number of rivers
        :param min_height: minimum height of the begining of the river
        """
        self.rivers = []  # type: List[List[int]]

        for corner in self.corners:
            if corner.terrain_type == TerrainType.LAND:
                neighbors_heights = [n.height for n in corner.adjacent]
                lowest = min(neighbors_heights)
                lowest_id = neighbors_heights.index(lowest)
                corner.downslope = lowest_id

        good_beginnings = [
            i for i, c in enumerate(self.corners)
            if c.terrain_type == TerrainType.LAND and c.height >= min_height
        ]

        if len(good_beginnings) == 0:
            heighest = max([c.height for c in self.corners])
            print(f'min_height={min_height} was to big. Heighest height={heighest}')
            return

        for i in range(n):
            random_corner: int = np.random.choice(good_beginnings)
            new_river = []

            while random_corner is not None:
                if random_corner in new_river:
                    break
                new_river.append(random_corner)
                random_corner = self.corners[random_corner].downslope

            self.rivers.append(new_river)


if __name__ == '__main__':
    g = Graph(N=25, iterations=2)
    g.plot_map()
