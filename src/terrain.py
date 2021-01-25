from __future__ import absolute_import
from enum import Enum
import numpy as np


class TerrainType(Enum):
    OCEAN = 1
    LAND = 2
    LAKE = 3
    COAST = 4


# Minimum ratio of the water edges to the total, in order to center become a water.
MIN_WATER_EDGES_RATIO_TO_BE_WATER_CENTER = 0.15


def assign_terrain_types_to_graph(graph, min_water_ratio=MIN_WATER_EDGES_RATIO_TO_BE_WATER_CENTER):
    """
    Sets the corners and centers of the graph to the terrain types.
    Updates the fields of the graph.
    """
    
    edges_to_map_end = [edge for edge in graph.edges if edge.is_edge_to_map_end()]
    
    water_edges = edges_to_map_end
    unexpanded_water_edges = edges_to_map_end
    
    water_to_total_ratio = np.random.rand() / 5 + 0.5  # 50% - 70% of the edges will be the water.
    water_edges_expected = int(len(graph.edges) * water_to_total_ratio) - len(edges_to_map_end)
    
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
    
    # Set all the water centers as an ocean.
    for center in graph.centers:
        if np.mean([border in water_edges for border in center.borders]) >= min_water_ratio:
            center.terrain_type = TerrainType.OCEAN
    
    # Set the water centers surrounded by the land as the lakes and set centers between ocean and the land as a coast.
    for center in graph.centers:
        if center.terrain_type is TerrainType.OCEAN:
            is_lake = all([
                neighbour.terrain_type in [TerrainType.LAND, TerrainType.LAKE] for neighbour in center.neighbors
            ])
            if is_lake:
                center.terrain_type = TerrainType.LAKE
        
        elif center.terrain_type is TerrainType.LAND:
            neighbours_with_ocean = any(
                [neighbour.terrain_type == TerrainType.OCEAN for neighbour in center.neighbors]
            )
            neighbours_with_land = any(
                [neighbour.terrain_type in [TerrainType.LAND, TerrainType.COAST] for neighbour in center.neighbors]
            )
            if neighbours_with_ocean and neighbours_with_land:
                center.terrain_type = TerrainType.COAST
