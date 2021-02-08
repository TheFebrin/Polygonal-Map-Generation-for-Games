from __future__ import absolute_import
from collections import deque
from enum import Enum
import numpy as np

class TerrainType(Enum):
    OCEAN = 1
    LAND = 2
    LAKE = 3
    COAST = 4

class BiomeType(Enum):
    OCEAN = 1
    LAKE = 2
    COAST = 3
    SNOW = 4
    TUNDRA = 5
    BARE = 6
    SCORCHED = 7
    TAIGA = 8
    SHRUBLAND = 9
    TEMPERATE_DESERT = 10
    TEMPERATE_RAIN_FOREST = 11
    TEMPERATE_DECIDOUS_FOREST = 12
    GRASSLAND = 13
    TROPICAL_RAIN_FOREST = 14
    TROPICAL_SEASONAL_FOREST = 15
    SUBTROPICAL_DESERT = 16
    MARSH = 17
    ICE = 18
    DEEPOCEAN = 19

# Minimum ratio of the water edges to the total, in order to center become a water.
MIN_WATER_EDGES_RATIO_TO_BE_WATER_CENTER = 0.25

CHANCE_OF_WATER_EDGE_IN_MIDDLE = 0.01

OCEAN_TO_TOTAL_RATIO = 0.4

LAKE_TO_TOTAL_RATIO = 0.025

def assign_terrain_types_to_graph(
    graph,
    min_water_ratio=MIN_WATER_EDGES_RATIO_TO_BE_WATER_CENTER,
    chance_of_water_edge_in_middle=CHANCE_OF_WATER_EDGE_IN_MIDDLE,
    ocean_to_total_ratio=OCEAN_TO_TOTAL_RATIO,
    lake_to_total_ratio=LAKE_TO_TOTAL_RATIO,
):
    """
    :param graph: Mutable graph
    
    Sets the corners and centers of the graph to the terrain types.
    Updates the fields of the graph.
    """
    
    regions = np.array([[0.2, 0.2],
                       [0.2, 0.4],
                       [0.2, 0.6],
                       [0.2, 0.8],
                       [0.2, 1. ],
                       [0.4, 0.2],
                       [0.4, 1. ],
                       [0.6, 0.2],
                       [0.6, 1. ],
                       [0.8, 0.2],
                       [0.8, 1. ],
                       [1. , 0.2],
                       [1. , 0.4],
                       [1. , 0.6],
                       [1. , 0.8],
                       [1. , 1. ]])
    
    actual_regions_ids = np.random.randint(0,len(regions), 3)
    
    def is_good_beginner(edge):
        if edge.is_edge_to_map_end():
            return True
        for region_id in actual_regions_ids:
            region = regions[region_id]
            if region[0]-0.2 <= edge.v0.x <= region[0] \
              and  region[1]-0.2 <= edge.v0.y <= region[1] \
              and np.random.random() < 0.5:
                return True
        return False
        
    def is_good_lake_beginner(edge):
#         return max(edge.v0.x, edge.v0.y, 1.0-edge.v0.x, 1.0-edge.v0.y)**2 \
#                * chance_of_water_edge_in_middle > np.random.random()
        return chance_of_water_edge_in_middle > np.random.random()
       
    water_edges = [edge for edge in graph.edges if is_good_beginner(edge)]
    unexpanded_water_edges = water_edges
    
    ocean_to_total_ratio += (np.random.rand() - 0.5) / 10
    ocean_edges_expected = int(len(graph.edges) * ocean_to_total_ratio)
    
    while len(water_edges) < ocean_edges_expected:
        selected_edge_idx = np.random.randint(len(unexpanded_water_edges))
        selected_edge = unexpanded_water_edges[selected_edge_idx]
        unexpanded_water_edges.remove(selected_edge)
        
        # Set all the edges adjacent to the selected one as the ocean.
        for corner in [selected_edge.v0, selected_edge.v1]:
            for edge in corner.protrudes:
                if edge not in water_edges:
                    water_edges.append(edge)
                    unexpanded_water_edges.append(edge)
    
    lake_edges_expected = ocean_edges_expected + int(len(graph.edges) * lake_to_total_ratio)
    unexpanded_water_edges = [edge for edge in graph.edges
                                      if edge not in water_edges and is_good_lake_beginner(edge)]
    
    while len(water_edges) < lake_edges_expected:
        selected_edge_idx = np.random.randint(len(unexpanded_water_edges))
        selected_edge = unexpanded_water_edges[selected_edge_idx]
        unexpanded_water_edges.remove(selected_edge)
        
        # Set all the edges adjacent to the selected one as the ocean.
        for corner in [selected_edge.v0, selected_edge.v1]:
            for edge in corner.protrudes:
                if edge not in water_edges:
                    water_edges.append(edge)
                    unexpanded_water_edges.append(edge)
    
    # First set all the water centers which have an edge leading the to end of the map as an oceans. Then mark all of
    # the water centers around them as oceans.
    unexpanded_ocean_centers = deque()
    
    # Set all the water centers as the lake.
    for center in graph.centers:
        if np.mean([border in water_edges for border in center.borders]) >= min_water_ratio:
            center.terrain_type = TerrainType.LAKE
            end_map_center = any([edge.is_edge_to_map_end() for edge in center.borders])
            if end_map_center:
                unexpanded_ocean_centers.append(center)
    
    while len(unexpanded_ocean_centers) > 0:
        center = unexpanded_ocean_centers.popleft()
        center.terrain_type = TerrainType.OCEAN
        
        for neighbor in center.neighbors:
            if neighbor.terrain_type is TerrainType.LAKE:  # Water center, neighbors with ocean -> it's an ocean.
                unexpanded_ocean_centers.append(neighbor)
    
    for center in graph.centers:
        if center.terrain_type is TerrainType.LAND:
            neighbors_with_ocean = any(
                [neighbor.terrain_type is TerrainType.OCEAN for neighbor in center.neighbors]
            )
            if neighbors_with_ocean:
                center.terrain_type = TerrainType.COAST
    
    for corner in graph.corners:
        # If the corner is surrounded by polygons of the same type, it has their type too.
        is_surrounded_by_ocean = all([center.terrain_type is TerrainType.OCEAN for center in corner.touches])
        is_surrounded_by_lake = all([center.terrain_type is TerrainType.LAKE for center in corner.touches])
        is_surrounded_by_land = all([center.terrain_type is TerrainType.LAND for center in corner.touches])
        is_surrounded_by_coast = all([center.terrain_type is TerrainType.COAST for center in corner.touches])
        
        if is_surrounded_by_ocean:
            corner.terrain_type = TerrainType.OCEAN
        elif is_surrounded_by_land:
            corner.terrain_type = TerrainType.LAND
        elif is_surrounded_by_lake:
            corner.terrain_type = TerrainType.LAKE
        elif is_surrounded_by_coast:
            corner.terrain_type = TerrainType.COAST
        else:
            # Check which type of polygons it touches. If it touches water and land polygons - it's a coast, otherwise
            # it's a land.
            touches_ocean = any([center.terrain_type is TerrainType.OCEAN for center in corner.touches])
            touches_land = any([center.terrain_type in [TerrainType.LAND, TerrainType.COAST] for center in corner.touches])
            
            if touches_ocean and touches_land:
                corner.terrain_type = TerrainType.COAST
            else:
                corner.terrain_type = TerrainType.LAND
                
    # Reset height of every corner and center to 0
    for corner in graph.corners:
        corner.height = 0
    for center in graph.centers:
        center.height = 0