from __future__ import absolute_import
from collections import deque
from enum import Enum
import numpy as np


class TerrainType(Enum):
    OCEAN = 1
    LAND = 2
    LAKE = 3
    COAST = 4


# Minimum ratio of the water edges to the total, in order to center become a water.
MIN_WATER_EDGES_RATIO_TO_BE_WATER_CENTER = 0.25

CHANCE_OF_WATER_EDGE_IN_MIDDLE = 0.1


def assign_terrain_types_to_graph(
    graph,
    min_water_ratio=MIN_WATER_EDGES_RATIO_TO_BE_WATER_CENTER,
    chance_of_water_edge_in_middle=CHANCE_OF_WATER_EDGE_IN_MIDDLE,
):
    """
    Sets the corners and centers of the graph to the terrain types.
    Updates the fields of the graph.
    """
    
    water_edges = [edge for edge in graph.edges
                   if edge.is_edge_to_map_end() or np.random.rand() < chance_of_water_edge_in_middle]
    unexpanded_water_edges = water_edges
    
    water_to_total_ratio = np.random.rand() / 5 + 0.5  # 50% - 70% of the edges will be the water.
    water_edges_expected = int(len(graph.edges) * water_to_total_ratio)
    
    while len(water_edges) < water_edges_expected:
        selected_edge_idx = np.random.randint(len(unexpanded_water_edges))
        selected_edge = unexpanded_water_edges[selected_edge_idx]
        unexpanded_water_edges.remove(selected_edge)
        
        # Set all the edges adjacent to the selected one as the ocean.
        for corner in [selected_edge.v0, selected_edge.v1]:
            for edge in corner.protrudes:
                if edge is not water_edges:
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
            touches_water = any([center.terrain_type in [TerrainType.OCEAN, TerrainType.LAKE] for center in corner.touches])
            touches_land = any([center.terrain_type in [TerrainType.LAND, TerrainType.COAST] for center in corner.touches])
            
            if touches_water and touches_land:
                corner.terrain_type = TerrainType.COAST
            else:
                corner.terrain_type = TerrainType.LAND
