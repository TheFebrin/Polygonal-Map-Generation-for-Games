# Polygonal Map Generation for Games
> Generating game maps based on: http://www-cs-students.stanford.edu/~amitp/game-programming/polygon-map-generation/

## Table of contents
* [General info](#general-info)
* [Polygons](#polygons)
* [Map Representation](#map-representation)
* [Islands](#islands)
* [Elevation](#elevation)
* [Rivers](#rivers)
* [Moisture](#moisture)
* [Biomes](#biomes)
* [Final Map](#final-map)
* [Libraries](#libraries)
* [Status](#status)
* [Credits](#credits)

## General info
![image](/images/overview.png)

#### Polygons:

The first step was to create a grid of polygons. We did that by generating random points which created Voronoi polygons. Then we replaced each point by the centroid of the polygon region related to this point.

![image](/images/voronoi_polygons.png)


The polygons weren't evenly distributed, so we used a technique called *Lloyd relaxation*, which replaces each point by the centroid of this polygon. <br>
Here we also plotted edges to the neighbouring polygons.

![image](/images/voronoi_polygons_finished2.png)

#### Map representation

Map is built from two graphs, *Nodes* and *Edges*.
*Nodes* graph has edges between every neighbouring polygons. *Edges* graph has edges between every neighbouring corners.

<details><summary>Terrain types:</summary>
<p>

```python
class TerrainType(Enum):
    OCEAN = 1
    LAND = 2
    LAKE = 3
    COAST = 4
```
</p>
</details>


![image](/images/edge-duality.png)

<details><summary>class Graph:</summary>
<p>

```python
class Graph:
    Centers
	Corners
	Edges
```
</p>
</details>

<details><summary>class Center:</summary>
<p>

```python
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
```
* `Center.neighbors` is a set of adjacent polygons
* `Center.borders` is a set of bordering edges
* `Center.corners` is a set of polygon corners
</p>
</details>

<details><summary>class Corner:</summary>
<p>

```python
class Corner:
    def __init__(self, x, y):
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
```

* `Corner.touches` is a set of polygons touching this corner
* `Corner.protrudes` is a set of edges touching the corner
* `Corner.adjacent` is a set of corners connected to this one

</p>
</details>

<details><summary>class Edge:</summary>
<p>

```python
class Edge:
    def __init__(self, center1, center2, corner1, corner2):
        self.d0 = center1
        self.d1 = center2
        self.v0 = corner1
        self.v1 = corner2
        self.river = 0
```

* `Edge.d0` and `Edge.d1` are the polygons connected by the Delaunay edge
* `Edge.v0` and `Edge.v1` are the corners connected by the Voronoi edge

</p>
</details>

#### Islands

TODO

![image](/images/islands.png)

#### Elevation

The main rule we followed is the more polygons there are between a point and the closest edge of the map, the higher is the elevation of this point. We calculate the elevation of corners first and then proceed with the polygons (centers).

##### Height of corners

We run BFS from every corner which is on the edge of a map. For every *neighbor* of the *current_corner* we update the *neighbor.height* with *current_corner.height + epsilon* if *current_corner.height + epsilon < neighbor.height*. 
If *current_corner* or *neighbor* is of type Ocean or Lake, the epsilon is equal to 0.01. Otherwise (when both of them are Land/Coast) it's 1.0. This way lakes will be more or less flat, oceans will be deep on the edges of the map and a little bit more shallow near the coast and land will become more and more elevated the closer it is to the map's center of mass. 

##### Height redistribution

Before assigning elevation for centers we redistribute elevation of corners so that they will take values from 0 to 1.0 and there will be less higher points on a map than the lower ones. It also smooths out the terrain.  

##### Height of centers (polygons)

Elevation of centers is simply the average of the elevation of all neighboring corners. 


Elevation is very important for:
* Biomes types:
	* high elevations: get snow, rock, tundra
	* medium elevations: get shrubs, deserts, forests, and grassland
	* low elevations: get rain forests, grassland, and beaches
* Rivers flow from high elevations down to the coast. Having elevations that always increase away from the coast means that there’s no local minima that complicate river generation.

![image](/images/elevation.png)

![image](/images/heightmap.png)

#### Rivers

First we defined *downslope*. From each *Corner* it is an arrow that points towards its lowest neighbouring corner.

We say that rivers flow from the highest points downwards following the *downslopes*.

We chose a random point in the mountains and we follow *downslopes* until we reach a lake or the ocean.

If more than one river is flowing through a given edge the river becomes visually thicker. The formula for width of an edge with *k* rivers is:

```python
river_width(k) = 2 + 2 * sqrt(k)
```

![image](/images/downslope.png)
![image](/images/rivers.png)

#### Moisture

Instead of the standard approach, where the localization of rivers and lakes depends on the moisture, we decided to first create water sources and then define the moisture of the terrain based on the distance from the freshwater.

First, we assigned starting moisture of corners. If the corner is a port of the river the moisture is equal to `max(1.0, min(3.0, 0.25*corner.river))`. If the corner touches the lake then the moisture is equal to `1.0`.

Then we run BFS from every corner with nonzero stating moisture. The moisture of a corner is equal to:
`max(corner.moisture, 0.9*max(moisture of neighbors))`.

After the moisture-spreading process, we set moisture of corners touches the ocean as 1.0.

The next step was to assign centers moisture. It's given by:
`mean(min(1.0, corner.moisture) for corner in center.corners)`

We decided to redistribute those values to get equal distribution of dry and wet tiles. Finally, the moisture of the tile is equal to the position on the sorted list of moistures given by the previous step.

![image](/images/moisture.png)


#### Biomes

TODO

![image](/images/moisture_diagram.png)

<details><summary>All biomes:</summary>
<p>

```python
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
```
</p>
</details>

![image](/images/biomes.png)


#### Final Map

TODO

![image](/images/final_small.png)
![image](/images/final_big.png)



## Libraries
* Python - version 3.7.3
* numpy
* scipy
* shapely
* matplotlib
* plotly

## Status
Project: _finished_

## Credits
* [@MatMarkiewicz](https://github.com/MatMarkiewicz)
* [@jgrodzicki](https://github.com/jgrodzicki)
* [@SWi98](https://github.com/SWi98)
* [@TheFebrin](https://github.com/TheFebrin)
