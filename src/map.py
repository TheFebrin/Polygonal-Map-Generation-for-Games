from __future__ import absolute_import
import queue
import numpy as np
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
        self.x = x
        self.y = y
        self.touches = []
        self.protrudes = []
        self.adjacent = []
        self.terrain_type = TerrainType.LAND
        self.height = 0


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
                if (c1, c2) in edges:
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
    
    def plot_map_with_terrain_types(self, debug_height = False):
        fig, ax = plt.subplots(figsize=(10, 10))
        
        polygons = [self._center_to_polygon(center) for center in self.centers]
        p = PatchCollection(polygons, match_original=True)
        ax.add_collection(p)
        if debug_height:
            for center in self.centers:
                if center.terrain_type == TerrainType.LAND:
                    plt.annotate(f"{round(center.height, 1)}", (center.x, center.y), color = 'white', 
                                backgroundcolor = 'black')
            for corner in self.corners:
                if corner.terrain_type == TerrainType.LAND:
                    plt.annotate(f"{round(corner.height, 1)}", (corner.x, corner.y), color = 'white', 
                                backgroundcolor = 'black')
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        plt.show()
        
    def plot_3d_height_map(self):
        """Function for plotting terrain height (based on the height of the corners), as a plotly wireframe"""
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
            color = lighten_color('green', amount = 1 + (center.height - 1) / 10)
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
            
    def assign_corner_elevations(self):
        '''
        For every LAND corner, calculates its distance from the nearest corner of type COAST.
        Runs BFS from every COAST corner. 
        '''
        for corner in self.corners:
            if corner.terrain_type == TerrainType.LAND:
                corner.height = float('inf')
        border_corners = [corner for corner in self.corners if corner.terrain_type == TerrainType.COAST]
        for border in border_corners:
            q = queue.Queue()
            q.put(border)
            while not q.empty():
                current_corner = q.get()
                current_height = current_corner.height
                for adjacent_corner in current_corner.adjacent:
                    if (adjacent_corner.terrain_type == TerrainType.LAND and 
                        current_height + 1 < adjacent_corner.height):
                        adjacent_corner.height = current_height + 1
                        q.put(adjacent_corner)
        # Fixing heights of LAND corners to their default values in case there is a LAND surrounded by water.
        for corner in self.corners:
            if corner.terrain_type == TerrainType.LAND and corner.height == float('inf'):
                corner.height = 1.0
    
    def assign_center_elevations(self):
        '''
        Calculates height for every center of type LAND by taking the mean height of corners that surround it.
        '''
        for center in self.centers:
            if center.terrain_type == TerrainType.LAND:
                corners_heights = [corner.height for corner in center.corners]
                center.height = sum(corners_heights) / len(corners_heights)
        

if __name__ == '__main__':
    g = Graph(N=25, iterations=2)
    g.plot_map()
