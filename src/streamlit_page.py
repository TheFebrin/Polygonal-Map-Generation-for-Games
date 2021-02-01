from __future__ import absolute_import

import streamlit as st
import numpy as np
import pandas as pd
from scipy.spatial import Voronoi, voronoi_plot_2d
import matplotlib.pyplot as plt
import matplotlib

matplotlib.use('TkAgg')

from voronoi import VoronoiPolygons 
"""
# Polygonal Map Generation

TODO desc
"""

voronoi_polygons = VoronoiPolygons(N=25)
voronoi_plot_2d(voronoi_polygons.vor)
# plt.show()
print(voronoi_polygons)
print(123)
# #23

df = pd.DataFrame({
  'first column': [1, 2, 3, 4],
  'second column': [10, 20, 30, 40]
})

df

arr = np.random.normal(1, 1, size=100)

plt.hist(arr, bins=20)

st.pyplot()
