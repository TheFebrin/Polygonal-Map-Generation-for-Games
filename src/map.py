from __future__ import absolute_import
import queue
import numpy as np
import math
import matplotlib.pyplot as plt
import matplotlib
from typing import *
from matplotlib.patches import Polygon
from matplotlib.collections import PatchCollection
from scipy.spatial import ConvexHull
import plotly.graph_objs as go

from src.terrain import TerrainType, BiomeType
from src.voronoi import VoronoiPolygons


class Center:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.neighbors = []
        self.borders = []
        self.corners = []
        self.terrain_type = TerrainType.LAND
        self.biome = BiomeType.OCEAN
        self.height = 0
        self.moisture = 0

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
        :param downslope: index of the adjacent corner with the lowest height
        :param:
        :param:
        """
        self.x = x
        self.y = y
        self.touches = []
        self.protrudes = []
        self.adjacent = []
        self.terrain_type = TerrainType.LAND
        self.height = 0
        self.downslope = None
        self.river = 0
        self.moisture = 0

    def get_cords(self) -> Tuple[float, float]:
        return self.x, self.y


class Edge:
    def __init__(self, center1, center2, corner1, corner2):
        self.d0 = center1
        self.d1 = center2
        self.v0 = corner1
        self.v1 = corner2
        self.river = 0

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

        self.centers, self.corners, self.edges, self.corners_to_edge = self.initialize_graph()
        # Notice that corners_to_edge.values() and edges are the same objects

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
        edges_values = list(edges.values())

        return centers, corners, edges_values, edges

    def find_edge_using_corners(self, c1: Corner, c2: Corner) -> Edge:
        """
        Finds Edge object represented by the given corners.
        """
        def same_corner(c1, c2):
            return c1.x == c2.x and c1.y == c2.y

        for edge in self.edges:
            if (same_corner(edge.v0, c1) and same_corner(edge.v1, c2)) \
                or (same_corner(edge.v0, c2) and same_corner(edge.v1, c1)):
                return edge

        raise ValueError('Edge with given corners doesnt exist.')


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

    def plot_full_map(
        self, 
        plot_type='terrain',
        debug_height=False,
        debug_moisture=False,
        downslope_arrows=False,
        rivers=True,
    ):
        """
        Here the next adjustments will be added to create a complete map.
        """
        fig, ax = plt.subplots(figsize=(10, 10))

        polygons = [self._center_to_polygon(center, plot_type) for center in self.centers]
        p = PatchCollection(polygons, match_original=True)
        ax.add_collection(p)

        # PLOT HEIGHT LABELS
        if debug_height:
            for corner in self.corners:
                plt.annotate(
                    f"{round(corner.height, 1)}", (corner.x, corner.y), 
                    color='white', backgroundcolor='black'
                )
        
        # PLOT MOISTURE LABELS
        if debug_moisture:
            for center in self.centers:
                plt.annotate(
                    f"{round(center.moisture, 1)}", (center.x, center.y), 
                    color='white', backgroundcolor='black'
                )

        def drawArrow(A, B, color='darkblue'):
            plt.arrow(
                A[0], A[1], B[0] - A[0], B[1] - A[1],
                head_width=0.015, length_includes_head=True, color=color
            )

        # PLOT DOWNSLOPE ARROWS
        if downslope_arrows:
            for corner in self.corners:
                if corner.downslope is not None:
                    adjacent = corner.adjacent[corner.downslope]
                    drawArrow(A=corner.get_cords(), B=adjacent.get_cords())

        # PLOT RIVERS
        if rivers:
            for edge in self.edges:
                if edge.river > 0:
                    beg_x, beg_y = edge.v0.get_cords()
                    end_x, end_y = edge.v1.get_cords()
                    X = (beg_x, end_x)
                    Y = (beg_y, end_y)
                    plt.plot(X, Y, linewidth=2+2*np.sqrt(edge.river), color='blue')
                    
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


    def _center_to_terrain_color(self, center):
        if center.terrain_type is TerrainType.LAND:
            cmap = matplotlib.cm.get_cmap('Greens')
            color = cmap(1.0 - center.height)
        elif center.terrain_type is TerrainType.OCEAN:
            color = 'deepskyblue'
        elif center.terrain_type is TerrainType.COAST:
            color = 'khaki'
        elif center.terrain_type is TerrainType.LAKE:
            color = 'royalblue'
        else:
            raise AttributeError(f'Unexpected terrain type: {center.terrain_type}')
        return color
    
    def _center_to_height_color(self, center):
        if center.terrain_type is TerrainType.LAND or center.terrain_type is TerrainType.COAST:
            cmap = matplotlib.cm.get_cmap('Greens')
            color = cmap(1.0 - center.height)
        elif center.terrain_type is TerrainType.OCEAN:
            color = 'deepskyblue'
        elif center.terrain_type is TerrainType.LAKE:
            color = 'royalblue'
        else:
            raise AttributeError(f'Unexpected terrain type: {center.terrain_type}')
        return color
    
    def _center_to_moisture_color(self, center):
        if center.terrain_type is TerrainType.LAND or center.terrain_type is TerrainType.COAST:
            cmap = matplotlib.cm.get_cmap('YlGn')
            color = cmap(center.moisture)
        elif center.terrain_type is TerrainType.OCEAN:
            color = 'deepskyblue'
        elif center.terrain_type is TerrainType.LAKE:
            color = 'royalblue'
        else:
            raise AttributeError(f'Unexpected terrain type: {center.terrain_type}')
        return color
    
    def _center_to_biome_color(self, center):
        if center.biome == BiomeType.OCEAN: color = 'deepskyblue'
        elif center.biome == BiomeType.LAKE: color = 'royalblue'
        elif center.biome == BiomeType.COAST: color = 'khaki'
        elif center.biome == BiomeType.SNOW: color = (248/255, 248/255, 248/255)
        elif center.biome == BiomeType.TUNDRA: color = (227/255, 228/255, 224/255)
        elif center.biome == BiomeType.BARE: color = (200/255, 198/255, 195/255)
        elif center.biome == BiomeType.SCORCHED: color = (123/255, 123/255, 123/255)
        elif center.biome == BiomeType.TAIGA: color = (173/255, 190/255, 167/255)
        elif center.biome == BiomeType.SHRUBLAND: color = (173/255, 182/255, 165/255)
        elif center.biome == BiomeType.TEMPERATE_DESERT: color = (208/255, 203/255, 165/255)
        elif center.biome == BiomeType.TEMPERATE_RAIN_FOREST: color = (55/255, 111/255, 44/255)
        elif center.biome == BiomeType.TEMPERATE_DECIDOUS_FOREST: color = (123/255, 164/255, 91/255)
        elif center.biome == BiomeType.GRASSLAND: color = (160/255, 195/255, 121/255)
        elif center.biome == BiomeType.TROPICAL_RAIN_FOREST: color = (32/255, 78/255, 23/255)
        elif center.biome == BiomeType.TROPICAL_SEASONAL_FOREST: color = (91/255, 124/255, 64/255)
        elif center.biome == BiomeType.SUBTROPICAL_DESERT: color = (237/255, 226/255, 142/255)
        elif center.biome == BiomeType.MARSH: color = 'darkseagreen'
        elif center.biome == BiomeType.ICE: color = 'lightcyan'
        elif center.biome == BiomeType.DEEPOCEAN: color = 'dodgerblue'
        else:
            raise AttributeError(f'Unexpected biome type: {center.biome}')
        return color
        
    def _center_to_polygon(self, center, plot_type):
        """
        Helper function for plotting, which takes the center and returns a polygon which can be plotted.
        """
        if plot_type == 'terrain':
            color = self._center_to_terrain_color(center)
        elif plot_type == 'moisture':
            color = self._center_to_moisture_color(center)
        elif plot_type == 'height':
            color = self._center_to_height_color(center)
        elif plot_type == 'biome':
            color = self._center_to_biome_color(center)
        else:
            raise AttributeError(f'Unexpected plot type: {plot_type}')
        
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
            if center.terrain_type == TerrainType.LAKE:
                center.height = min(corners_heights)
            else:
                center.height = sum(corners_heights) / len(corners_heights)
            
    def redistribute_elevations(self, scale_factor = 1.1):
        sorted_corners = sorted(self.corners, key = lambda c: c.height)
        for i, corner in enumerate(sorted_corners):
            y = i / len(sorted_corners)
            x = math.sqrt(scale_factor) - math.sqrt(scale_factor * (1 - y))
            corner.height = x
            
    def _assign_corner_river(self):
        for edge in self.edges:
            if edge.river > 0:
                edge.v0.river = max(edge.v0.river, edge.river)
                edge.v1.river = max(edge.v0.river, edge.river)
        
    def create_rivers(self, n, min_height):
        """
        Rivers flow from high elevations down to the coast.
        Having elevations that always increase away from the coast means
        that there’s no local minima that complicate river generation

        This function creates `n` rivers. It draws a random start position for
        each river that is >= min_height.
        Rivers are saved in Edge.

        :param n: number of rivers
        :param min_height: minimum height of the begining of the river
        """

        # reset previous rivers
        for edge in self.edges:
            edge.river = 0

        def suitable_for_river(c: Corner):
            good_tile = c.terrain_type == TerrainType.LAND or c.terrain_type == TerrainType.COAST
            neighbour_tiles = [nei.terrain_type for nei in c.adjacent]
            good_neighbours = [
                nt == TerrainType.LAND or nt == TerrainType.COAST
                for nt in neighbour_tiles
            ]
            touches_tiles = [center.terrain_type for center in c.touches]
            good_touches = [
                tt == TerrainType.LAND or tt == TerrainType.COAST
                for tt in touches_tiles
            ]

            return good_tile and all(good_neighbours) and all(good_touches)
  
        for corner in self.corners:
            if corner.terrain_type == TerrainType.LAND or corner.terrain_type == TerrainType.COAST:
                neighbors_heights = [nei.height for nei in corner.adjacent]
                lowest = min(neighbors_heights)
                lowest_id = neighbors_heights.index(lowest)
                corner.downslope = lowest_id

        good_beginnings = [
            c for c in self.corners
            if (c.terrain_type == TerrainType.LAND or c.terrain_type == TerrainType.COAST) \
                and c.height >= min_height
        ]

        if len(good_beginnings) < n:
            heighest = max([
                c.height for c in self.corners 
                if c.terrain_type == TerrainType.LAND or c.terrain_type == TerrainType.COAST
            ])
            print(f'Found only {len(good_beginnings)} river beginnings. Lower min_height.')
            print(f'min_height={min_height} | Heighest mountain has height={heighest}')
            return

        start_corners = np.random.choice(good_beginnings, n, replace=False)
        for corner in start_corners:
            while True:
                if corner.downslope is None or not suitable_for_river(corner):
                    break
                
                next_corner = corner.adjacent[corner.downslope]
                if next_corner.terrain_type != TerrainType.LAND and next_corner.terrain_type != TerrainType.COAST:
                    break

                mutable_edge = self.find_edge_using_corners(corner, next_corner)

                # Notice that this line will modify this object in self.edges
                mutable_edge.river += 1
                corner = next_corner
                
        self._assign_corner_river()
        
    def _assign_corner_moisture(self, distance_decay, river_weight, lake_value, ocean_value):
    
        q = queue.Queue()
        for corner in self.corners:
            if corner.river > 0:
                corner.moisture = max(1.0, min(3.0, river_weight*corner.river))
            if any([center.terrain_type == TerrainType.LAKE for center in corner.touches]):
                corner.moisture = max(lake_value, corner.moisture)
            if corner.moisture > 0:
                q.put(corner)

        while not q.empty():
            corner = q.get()

            new_moisture = distance_decay*corner.moisture
            for nei_corner in corner.adjacent:
                if new_moisture > nei_corner.moisture:
                    nei_corner.moisture = new_moisture
                    q.put(nei_corner)

        for corner in self.corners:
            if any([center.terrain_type == TerrainType.OCEAN for center in corner.touches]):
                corner.moisture = max(ocean_value, corner.moisture)
    
    def redistribute_moisture(self):
        sorted_centers = sorted(self.centers, key = lambda c: c.moisture)
        for i, center in enumerate(sorted_centers):
            center.moisture = i / (len(sorted_centers)-1)
    
    def assign_moisture(self, 
        redistribute=True,
        distance_decay=0.9, 
        river_weight=0.25,
        lake_value=1.0,
        ocean_value=1.0,
        ):
        self._assign_corner_moisture(distance_decay, river_weight, lake_value, ocean_value)
        
        for center in self.centers:
            if center.terrain_type == TerrainType.LAND or center.terrain_type == TerrainType.COAST:
                center.moisture = np.mean(np.array([min(1.0, corner.moisture) for corner in center.corners]))
                
        if redistribute:
            self.redistribute_moisture()
            
    def assign_biomes(self):
        for center in self.centers:
            if center.terrain_type == TerrainType.COAST:
                center.biome = BiomeType.COAST
            elif center.terrain_type == TerrainType.OCEAN:
                if any([n.terrain_type == TerrainType.COAST for n in center.neighbors]):
                    center.biome = BiomeType.OCEAN
                else:
                    center.biome = BiomeType.DEEPOCEAN
            elif center.terrain_type == TerrainType.LAKE:
                if center.height < 0.2:
                    center.biome = BiomeType.MARSH
                elif center.height > 0.8:
                    center.biome = BiomeType.ICE
                else:
                    center.biome = BiomeType.LAKE
            else:
                if center.height > 0.85:
                    if center.moisture > 0.5:
                        center.biome = BiomeType.SNOW
                    elif center.moisture > 0.33:
                        center.biome = BiomeType.TUNDRA
                    elif center.moisture > 0.16:
                        center.biome = BiomeType.BARE
                    else:
                        center.biome = BiomeType.SCORCHED
                elif center.height > 0.65:
                    if center.moisture > 0.66:
                        center.biome = BiomeType.TAIGA
                    elif center.moisture > 0.33:
                        center.biome = BiomeType.SHRUBLAND
                    else:
                        center.biome = BiomeType.TEMPERATE_DESERT
                elif center.height > 0.35:
                    if center.moisture > 0.83:
                        center.biome = BiomeType.TEMPERATE_RAIN_FOREST
                    elif center.moisture > 0.50:
                        center.biome = BiomeType.TEMPERATE_DECIDOUS_FOREST
                    elif center.moisture > 0.16:
                        center.biome = BiomeType.GRASSLAND
                    else:
                        center.biome = BiomeType.TEMPERATE_DESERT
                else:
                    if center.moisture > 0.66:
                        center.biome = BiomeType.TROPICAL_RAIN_FOREST
                    elif center.moisture > 0.33:
                        center.biome = BiomeType.TROPICAL_SEASONAL_FOREST
                    elif center.moisture > 0.16:
                        center.biome = BiomeType.GRASSLAND
                    else:
                        center.biome = BiomeType.SUBTROPICAL_DESERT
    

if __name__ == '__main__':
    g = Graph(N=25, iterations=2)
    g.plot_map()
