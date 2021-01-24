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
        centroids: Optional[np.ndarray] = None
    ):
        if points is None:
            self._points = np.random.random((N, 2))
        else:
            self._points = points

        self._vor = Voronoi(self._points)

        if centroids is None:
            self._centroids = self.generate_centroids(N=N)
        else:
            self._centroids = centroids

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

    def generate_points(self, N: int) -> None:
        self._points = np.random.random((N, 2))

    def generate_centroids(self, N: int) -> np.ndarray:
        centroids = np.zeros((N, 2))
        for i, p in enumerate(self._vor.point_region):
            region_vertices = [k for k in self._vor.regions[p] if k > -1]
            region_vertices_coords = self._vor.vertices[region_vertices]
            if np.any(region_vertices_coords > 1) or np.any(region_vertices_coords < 0):
                centroids[i:] = self._vor.points[i]
                continue
            centroid = region_vertices_coords.mean(axis=0)
            centroids[i, :] = centroid
        return centroids

    @staticmethod
    def voronoi_finite_polygons_2d(
        vor: Voronoi,
        radius: Optional[float] = None,
    ) -> Tuple[List[Tuple[int, int]], List[Tuple[int, int]]]:
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
            radius = vor.points.ptp().max()*2

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
            angles = np.arctan2(vs[:,1] - c[1], vs[:,0] - c[0])
            new_region = np.array(new_region)[np.argsort(angles)]

            # finish
            new_regions.append(new_region.tolist())

        return new_regions, np.asarray(new_vertices)
