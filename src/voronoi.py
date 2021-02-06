from __future__ import absolute_import
import numpy as np
from typing import Optional, List, Tuple
import matplotlib.pyplot as plt
from scipy.spatial import Voronoi, voronoi_plot_2d
from shapely.geometry import Polygon


class VoronoiPolygons:
    """
    TODO
    """

    def __init__(
        self,
        N: Optional[int] = 25,
        points: Optional[np.ndarray] = None,
        centroids: Optional[np.ndarray] = None,
        alpha : Optional[float] = 0.2
    ):
        self._points = points
        self._centroids = centroids

        if self._points is None:
            self.generate_points(N=N, alpha=alpha)

        self._vor = Voronoi(self._points)

        if self._centroids is None:
            self.generate_centroids(N=N)

        self._vor_c = Voronoi(self._centroids)

    @property
    def points(self):
        return self._points

    @property
    def centroids(self):
        return self._centroids

    @property
    def vor(self):
        return self._vor

    @property
    def vor_c(self):
        return self._vor_c

    def generate_points(self, N: int, alpha: float) -> None:
        self._points = np.random.random((int((1-alpha)*N), 2))
        if alpha > 0:
            N_ = N - int((1-alpha)*N)
            new_points = np.random.random((N_, 2))/2
            regions = np.array([[.5,.5],[.5,.0],[.0,.0],[.0,.5]])
            region = regions[np.random.randint(0,4)]
            new_points = new_points + region
        self._points = np.vstack((self._points, new_points))

    def generate_centroids(self, N: int) -> None:
        centroids = np.zeros((N, 2))
        for i, p in enumerate(self._vor.point_region):
            region_vertices = [k for k in self._vor.regions[p] if k > -1]
            region_vertices_coords = self._vor.vertices[region_vertices]
            if np.any(region_vertices_coords > 1) or np.any(region_vertices_coords < 0):
                centroids[i:] = self._vor.points[i]
                continue
            centroid = region_vertices_coords.mean(axis=0)
            centroids[i, :] = centroid
        self._centroids = centroids

    @staticmethod
    def voronoi_finite_polygons_2d(
        vor: Voronoi,
        radius: Optional[float] = None,
    ) -> Tuple[
            List[List[int]],
            List[Tuple[int, int]]
         ]:
        """
        source: https://stackoverflow.com/questions/20515554/colorize-voronoi-diagram/20678647#20678647

        Reconstruct infinite voronoi regions in a 2D diagram to finite
        regions.
        Parameters
        ----------
        vor : Input diagram
        radius : Distance to 'points at infinity'.
        Returns
        -------
        regions : list of tuples
            Indices of vertices in each revised Voronoi regions.
        vertices : list of tuples
            Coordinates for revised Voronoi vertices. Same as coordinates
            of input vertices, with 'points at infinity' appended to the
            end.
        """

        if vor.points.shape[1] != 2:
            raise ValueError("Requires 2D input")

        new_regions = []
        new_vertices = vor.vertices.tolist()

        center = vor.points.mean(axis=0)
        if radius is None:
            radius = vor.points.ptp().max() * 2

        # Construct a map containing all ridges for a given point
        all_ridges = {}
        for (p1, p2), (v1, v2) in zip(vor.ridge_points, vor.ridge_vertices):
            all_ridges.setdefault(p1, []).append((p2, v1, v2))
            all_ridges.setdefault(p2, []).append((p1, v1, v2))

        # Reconstruct infinite regions
        for p1, region in enumerate(vor.point_region):
            vertices = vor.regions[region]

            if all(v >= 0 for v in vertices):
                # finite region
                new_regions.append(vertices)
                continue

            # reconstruct a non-finite region
            ridges = all_ridges[p1]
            new_region = [v for v in vertices if v >= 0]

            for p2, v1, v2 in ridges:
                if v2 < 0:
                    v1, v2 = v2, v1
                if v1 >= 0:
                    # finite ridge: already in the region
                    continue

                # Compute the missing endpoint of an infinite ridge

                t = vor.points[p2] - vor.points[p1]  # tangent
                t /= np.linalg.norm(t)
                n = np.array([-t[1], t[0]])  # normal

                midpoint = vor.points[[p1, p2]].mean(axis=0)
                direction = np.sign(np.dot(midpoint - center, n)) * n
                far_point = vor.vertices[v2] + direction * radius

                new_region.append(len(new_vertices))
                new_vertices.append(far_point.tolist())

            # sort region counterclockwise
            vs = np.asarray([new_vertices[v] for v in new_region])
            c = vs.mean(axis=0)
            angles = np.arctan2(vs[:, 1] - c[1], vs[:, 0] - c[0])
            new_region = np.array(new_region)[np.argsort(angles)]

            # finish
            new_regions.append(new_region.tolist())

        return new_regions, np.asarray(new_vertices)

    @staticmethod
    def find_new_polygons(
        vor: Voronoi = None
    ) -> Tuple[
            List[List[int]],
            List[Tuple[int, int]],
            List[Tuple[int, int]],
         ]:

        regions, vertices = VoronoiPolygons.voronoi_finite_polygons_2d(vor=vor)

        new_regions = []
        new_vertices = list(vertices.copy())

        box = Polygon([[0, 0], [0, 1], [1, 1], [1, 0]])

        for region in regions:
            poly = Polygon(vertices[region])
            poly = poly.intersection(box)
            region_elements = []
            for x, y in poly.exterior.coords[:-1]:
                p = np.array([x, y])
                for i, v in enumerate(new_vertices):
                    if np.sum((v - p) ** 2) <= 1e-14:
                        region_elements.append(i)
                        break
                else:
                    region_elements.append(len(new_vertices))
                    new_vertices.append(p)
            new_regions.append(region_elements)

        new_vertices = np.array(new_vertices)
        new_centroids = np.array([
            new_vertices[region].mean(axis=0) for region in new_regions
        ])
        return new_regions, new_vertices, new_centroids

    @staticmethod
    def generate_neighbours(
        vor: Voronoi,
        regions: List[List[int]],
        vertices: List[Tuple[int, int]],
    ):
        neighbors = [[] for i in range(len(regions))]
        intersecions = [[] for i in range(len(regions))]
        for i, region1 in enumerate(regions):
            for j, region2 in enumerate(regions):
                if i == j:
                    continue
                poly1 = Polygon(vertices[region1])
                poly2 = Polygon(vertices[region2])

                if poly1.intersects(poly2):
                    intersection = np.array(poly1.intersection(poly2).coords)
                    if len(intersection) < 2:
                        continue
                    v1 = ((vertices - intersection[0])**2).sum(axis=1).argmin()
                    v2 = ((vertices - intersection[1])**2).sum(axis=1).argmin()
                    intersecions[i].append([v1,v2])
                    neighbors[i].append(j)

        return neighbors, intersecions

    def generate_Voronoi(
        self,
        iterations: int = 2
    ):
        """
        params:
            N - number of points
            iterations - number of iterations for relaxation process
        returns:
            points - list of final points
            centroids - list of centroids of the regions
            vertices - list of vertices
            regions - indexes of vertices creating each region
            neighbors - indexes of neighbors regions for each region
            intersecions - indexes of vertices creating line separating each two neighbors
        """
        
        for iter in range(iterations + 1):
            self._vor = Voronoi(self._points)
            new_regions, new_vertices, new_centroids = \
                VoronoiPolygons.find_new_polygons(vor=self._vor)
            self._points = new_centroids
        neighbors, intersecions = VoronoiPolygons.generate_neighbours(
            vor=self._vor,
            regions=new_regions,
            vertices=new_vertices,
        )
        return self._vor.points, self._points, new_vertices, new_regions, neighbors, intersecions

    @staticmethod
    def plot_Voronoi_grid(
        points, vertices, regions, neighbors, centroids=None
    ):
        plt.figure(figsize=(10, 10))
        plt.rcParams['axes.facecolor'] = 'grey'
        for region in regions:
            region.append(region[0])
            coords = vertices[region]
            plt.plot(coords[:, 0], coords[:, 1], c='white')
        for i, n_list in enumerate(neighbors):
            p1 = points[i]
            for i2 in n_list:
                p2 = points[i2]
                plt.plot([p1[0], p2[0]], [p1[1], p2[1]], c='black')
        plt.scatter(points[:, 0], points[:, 1], c='red')
        plt.scatter(vertices[:, 0], vertices[:, 1], c='blue')
        if centroids is not None:
            plt.scatter(centroids[:, 0], centroids[:, 1], c='green')
        plt.xlim(0, 1)
        plt.ylim(0, 1)
        plt.show()


if __name__ == '__main__':
    v = VoronoiPolygons()
    # print(v.voronoi_finite_polygons_2d(vor=v.vor))
    print(v.points.shape)
    print(v.centroids.shape)

    # print(v.find_new_polygons(vor=v.vor))
    # print(v.generate_neighbours(vor=v.vor))

    vorpoints, points, new_vertices, new_regions, neighbors, intersecions \
        = v.generate_Voronoi(iterations=4)

    VoronoiPolygons.plot_Voronoi_grid(
        points=points, vertices=new_vertices, regions=new_regions, neighbors=neighbors
    )
