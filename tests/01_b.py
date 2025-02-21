import time

start = time.time()
import compas
import os
from compas_viewer import Viewer
from compas_viewer.scene import Tag
from compas.geometry import Point, Vector, Line, Plane, Polygon, Frame, Transformation
from compas.scene import Scene


viewer = Viewer()
# viewer = Scene()

HERE = os.path.dirname(__file__)
FILE_I1 = os.path.join(HERE, "problem_init.json")
problem_init = compas.json_load(FILE_I1)

FILE_I2 = os.path.join(HERE, "problem_gravity.json")
problem_grav = compas.json_load(FILE_I2)

# =============================================================================
# Get resultants lines and magnitudes
# =============================================================================
# res,mag,comp = problem.support_resultants(0.1)

# =============================================================================
# Check resultant point positions inside or outside contact area
# =============================================================================
# pols, pts, pout, pnp = problem.check_resultant_points()

# =============================================================================
# Compare block positions
# =============================================================================
distances = []
displacements = []
for block_init, block_grav in zip(problem_init.blocks, problem_grav.blocks):
    centroid_init = block_init.mesh.centroid()
    centroid_grav = block_grav.mesh.centroid()
    vector = Vector.from_start_end(centroid_init, centroid_grav)
    viewer.scene.add(Point(*vector))
    scaled_vector = vector.scaled(2)
    new_vector = Vector.from_start_end(centroid_init, scaled_vector)
    # viewer.scene.add(Point(*new_vector))
    displacement = Line(centroid_init, new_vector)
    displacements.append(displacement)
    viewer.scene.add(Point(*centroid_init), pointcolor=Color.from_rgb, size=10)
    distance = displacement.length
    distances.append(distance)
    # viewer.scene.add(Tag(str(distance),displacement.end,height=50))

from compas.itertools import normalize_values
from compas.colors import ColorMap

scale = normalize_values(distances, 0, 1)
map = ColorMap.from_two_colors((1, 0, 0), (0, 1, 0))
for v, d in zip(scale, displacements):
    color = map(v)
    # viewer.scene.add(d, linecolor=color, linewidth=20)


# print(distance)
# if distance > 0.001:
#     viewer.scene.add(displacement)


# =============================================================================
# View
# =============================================================================
# for m,r in zip(mag, res):
#     viewer.scene.add(Tag(m,Point(*r.end),height=5))
#     viewer.scene.add(r)

# for block in problem.blocks:
#     mesh = block.mesh
#     viewer.scene.add(mesh)

# for po in pols:
#     viewer.scene.add(po)
# for pt in pts:
#     viewer.scene.add(pt)

# HERE = os.path.dirname(__file__)
# FILE_I= os.path.join(HERE, 'problem.json')
# problem  = compas.json_load(FILE_I)

# for block in problem.blocks:
#     mesh = block.mesh
#     color = block.color
#     print(color)

# #     mesh = block.mesh
#     viewer.scene.add(mesh)


viewer.show()
