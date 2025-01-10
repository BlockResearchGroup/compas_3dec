import os
import compas
from compas_3dec.datastructure.problem_3dec import Problem3dec
from compas.colors import Color

# =============================================================================
# Input problem init
# =============================================================================
HERE = os.path.dirname(__file__)
# FILE_I0 = os.path.join(HERE, 'problem_init_jk1.json')
# problem_init = compas.json_load(FILE_I0)
# =============================================================================
# Input problem gravity
# =============================================================================
FILE_I = os.path.join(HERE, 'problem_gravity_jk1.json')
problem_grav: Problem3dec = compas.json_load(FILE_I)

# =============================================================================
# Input problem load
# =============================================================================
# FILE_II = os.path.join(HERE, 'problem_load.json')
# problem_pt: Problem3dec = compas.json_load(FILE_II)

# =============================================================================
# Input problem stress
# =============================================================================
# FILE_III = os.path.join(HERE, 'problem_stress.json')
# problem_stress: Problem3dec = compas.json_load(FILE_III)


import rhinoscriptsyntax as rs
rs.DeleteObjects(rs.AllObjects())

# =============================================================================
# show geometry
# =============================================================================
from compas.scene import Scene
scene = Scene()
scene.clear_objects()
for block in problem_grav.blocks:
    scene.add(block.mesh, color = block.color)

# for block in problem_pt.blocks:
#     scene.add(block.mesh, color = Color.from_rgb255(255, 0, 0))


# =============================================================================
# show contact forces
# =============================================================================
from compas_3dec.datastructure import Interaction3dec
for interaction in problem_grav.interactions:
    interaction: Interaction3dec
    if interaction.forces_per_contact:
        application_point = interaction.display_resultant_application_point()
        resultant_force = interaction.display_resultant_force(0.01)
        scene.add(application_point)
    for line in resultant_force:
        scene.add(line, color=(0, 81, 12), width=20.0)


# from compas_3dec.datastructure import Interaction3dec
# for interaction in problem_pt.interactions:
#     interaction: Interaction3dec
#     if interaction.forces_per_contact:
#         application_point = interaction.display_resultant_application_point()
#         resultant_force = interaction.display_resultant_force(0.001)
#         scene.add(application_point)
#     for line in resultant_force:
#         scene.add(line, color=(255, 0, 0), width=20.0)

# from compas_3dec.datastructure import Interaction3dec
# for interaction in problem_stress.interactions:
#     interaction: Interaction3dec
#     if interaction.forces_per_contact:
#         application_point = interaction.display_resultant_application_point()
#         resultant_force = interaction.display_resultant_force(0.01)
#         scene.add(application_point)
#     for line in resultant_force:
#         scene.add(line, color=(255, 0, 0), width=20.0)



# =============================================================================
# Resultant forces
# =============================================================================
# res, mag, comp = problem_grav.support_resultants(0.05)
# for r,m,c in zip(res,mag, comp):
#     # line = rs.AddLine(r.start, r.end)
#     line = rs.AddLine(r.end,r.start)
#     rs.CurveArrows(line, 2)
#     rs.AddTextDot(m,[r.end[0],r.end[1],r.end[2]-0.2])
    # rs.AddTextDot(c,[r.end[0],r.end[1],r.end[2]-0.5])

# res, mag, comp = problem_pt.support_resultants(0.2)
# for r,m,c in zip(res,mag, comp):
#     line = rs.AddLine(r.start, r.end)
#     rs.CurveArrows(line, 2)
#     rs.AddTextDot(m,[r.end[0],r.end[1],r.end[2]-0.2])
#     rs.AddTextDot(c,[r.end[0],r.end[1],r.end[2]-0.5])

# res, mag, comp = problem_stress.support_resultants(0.2)
# for r,m,c in zip(res,mag, comp):
#     line = rs.AddLine(r.start, r.end)
#     rs.CurveArrows(line, 2)
#     rs.AddTextDot(m,[r.end[0],r.end[1],r.end[2]-0.2])
#     rs.AddTextDot(c,[r.end[0],r.end[1],r.end[2]-0.5])




# =============================================================================
# compare blocks position
# =============================================================================
# from compas.geometry import Line, Point, Vector
# scaled_displacements = []
# distances = []
# for block_init, block_grav in zip(problem_init.blocks, problem_grav.blocks):
#     if not block_init.is_support and not block_grav.is_support:
#         centroid_init = block_init.mesh.centroid()
#         centroid_grav = block_grav.mesh.centroid()
#         displacement = Line(centroid_init, centroid_grav)
#         vector = Vector.from_start_end(centroid_init, centroid_grav)
#         scaled_vector = vector.scaled(1000000)
#         new_vector = Vector.sum_vectors([centroid_init, scaled_vector])
#         scaled_displacement = Line(centroid_init, new_vector)
#         scaled_displacements.append(scaled_displacement)
#         distance = displacement.length
#         distances.append(distance)

# from compas.itertools import normalize_values
# from compas.colors import ColorMap, Color
# scale = normalize_values(distances, 0, 1)
# c1 = Color.from_rgb255(255, 0, 0)
# c2 = Color.from_rgb255(0, 255, 0)
# # map = ColorMap.from_two_colors(c1,c2,True)
# map = ColorMap.from_palette('imola')
# for v,d in zip(scale, scaled_displacements):
#     color = map(v)
#     rgb = color.rgb255
#     displ = rs.AddLine(d.start, d.end)
#     rs.ObjectColor(displ, rgb)
#     arrow = rs.CurveArrows(displ, 2)

# sorted_distances = sorted(distances)
# normalized_distances = normalize_values(sorted_distances, 0, 1)
# for i,n in enumerate(normalized_distances):
#     legend_color = map(n)
#     legend_rgb = legend_color.rgb255
#     pt = Point(0, 0, 0.1*i)
#     txt = rs.AddTextDot(str(round(sorted_distances[i],10)), (pt[0]-1, pt[1], pt[2]))
#     rs.ObjectColor(txt, legend_rgb)
# scene.draw()

# =============================================================================
# show blocks index
# =============================================================================
# for block in problem_grav.blocks:
#     centroid = block.mesh.centroid()
#     rs.AddTextDot(block.index, centroid)

# =============================================================================
# show contact geometry
# =============================================================================
from compas.geometry import Polygon
from compas.datastructures import Mesh
from compas.colors import Color, ColorMap
from compas_3dec.datastructure import Interaction3dec
for interaction in problem_grav.interactions:  
    interaction: Interaction3dec
    if isinstance(interaction.contact_geometry, Polygon):
        scene.add(interaction.contact_geometry, color = (0, 0, 255), hide_coplanaredges=True, linewidth=3, show_faces=True)
   



scene.draw()