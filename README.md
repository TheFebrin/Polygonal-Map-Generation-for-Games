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

TODO

![image](/images/elevation.png)
![image](/images/heightmap.png)

#### Rivers

TODO

![image](/images/downslope.png)
![image](/images/rivers.png)

#### Moisture

TODO

![image](/images/moisture.png)


#### Biomes

TODO

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
