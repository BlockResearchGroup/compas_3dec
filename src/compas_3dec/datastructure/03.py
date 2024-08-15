import os
import compas
from compas.geometry import Line, Point, Vector
from compas_viewer import Viewer
from compas_viewer.scene import Tag
from compas.colors import Color


HERE = os.path.dirname(__file__)
FILE_I1 = os.path.join(HERE, "problem_load.json")
problem_load = compas.json_load(FILE_I1)


FILE_I2 = os.path.join(HERE, "problem_gravity.json")
problem_gravity = compas.json_load(FILE_I2)

viewer = Viewer()
viewer.renderer.view = "top"
distances = []
scaled_displacements = []
for block_init, block_grav in zip(problem_gravity.blocks, problem_load.blocks):
    centroid_init = block_init.mesh.centroid()
    centroid_grav = block_grav.mesh.centroid()
    displacement = Line(centroid_init, centroid_grav)
    vector = Vector.from_start_end(centroid_init, centroid_grav)
    scaled_vector = vector.scaled(10)
    new_vector = Vector.sum_vectors([centroid_init, scaled_vector])
    # viewer.scene.add(new_vector,)
    scaled_displacement = Line(centroid_init, new_vector)
    scaled_displacements.append(scaled_displacement)
    # viewer.scene.add(Point(*new_vector))
    distance = displacement.length
    distances.append(distance)
    viewer.scene.add(Point(*centroid_init), pointcolor=Color.from_rgb255(200, 0, 0), pointsize=5)
    viewer.scene.add(Tag(str(round(distance, 3)), scaled_displacement.end, height=50))
    # print(distance)
    # if distance > 0.001:
    #     viewer.scene.add(displacement,linewidth=5)


from compas.itertools import normalize_values
from compas.colors import ColorMap

scale = normalize_values(distances, 0, 1)
map = ColorMap.from_two_colors((1, 0, 0), (0, 1, 0))
for v, d in zip(scale, scaled_displacements):
    color = map(v)
    viewer.scene.add(d, linecolor=color, linewidth=10)
viewer.show()
