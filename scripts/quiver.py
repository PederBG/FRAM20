import matplotlib.pyplot as plt
import numpy as np

import Image

np.set_printoptions(threshold=np.nan)
import numpy.ma as ma


import netCDF4 as nc

# x = np.linspace(0,10,1)
# y = np.linspace(10,0,1)
# print(x)
# print(y)
#
# dx = np.zeros((9,9))
# dy = np.zeros((3,2))
#
# dx[1,1] = 2


# ---------------------------------------------------------

#len(dx) = 177, len(dx[0])=119
fh = nc.Dataset('icedrift.nc', mode='r')
dx = (fh.variables['dX'][:][0])
dy = (fh.variables['dY'][:][0])

# dx = dx[0:dx.size:dx.size/10]
# dy = dy[0:dx.size:dy.size/10]



x = np.linspace(0,119, 119)
y = np.linspace(177,0,177)


# print(x)
# print(y)
# print(dx)
# print("---")

fig = plt.figure(figsize=(11.9*3, 17.7*3), frameon=False)
print(fig)
ax = plt.Axes(fig, [0., 0., 1., 1.])
ax.set_axis_off()
fig.add_axes(ax)

plt.quiver(x, y, dx, dy, scale=900, width=0.001)


fig.savefig('icequiver.png', transparent=False, format='png')
Image.open('icequiver.png').convert('RGB').save('icequiver.jpg','JPEG')
