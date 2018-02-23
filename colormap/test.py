from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import colormap
import numpy as np

# define some random data that emulates your indeded code:
NCURVES = 10
np.random.seed(101)
curves = [np.random.random(20) for i in range(NCURVES)]
print(curves)
values = range(NCURVES)

# jet = cm = colormap.get_cmap('gnuplot') 
# cNorm  = colormap.normalize(vmin=0, vmax=values[-1])
# scalarMap = colormap.scale(norm=cNorm, cmap=jet)
scalarMap = colormap.create_scaled_colormap('gnuplot', 0, values[-1])
print(scalarMap.get_clim())

lines = []
for idx in range(len(curves)):
    line = curves[idx]
    colorVal = scalarMap.to_rgba(line, bytes=True)
    print(line)
    print(colorVal)
    colorVal = colormap.get_opengl_colors('gnuplot', line)
    print(colorVal)

print(colormap.list_colormaps())
