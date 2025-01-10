import time

start = time.time()
import compas
import os
from compas_viewer import Viewer

HERE = os.path.dirname(__file__)
FILE_I = os.path.join(HERE, "problem_gravity.json")
problem = compas.json_load(FILE_I)

# =============================================================================
# PT loads
# =============================================================================
from compas.geometry import Vector, Point

load_strings = "; load" + "\n"
for block in problem.blocks:
    if block.is_support == False:
        mesh = block.mesh
        start = mesh.vertex_coordinates(2)
        arc_centre = (2.790, 0.300, -7.121)
        # deviation_direction = (Vector.from_start_end(start, arc_centre)).unitized()
        # deviation_vector = Point(*Vector.sum_vectors([start,deviation_direction]))
        load = 1000
        sphere_radius = 0.02
        load_strings += problem.set_point_load(start, arc_centre, load, sphere_radius, 1)

from compas.geometry import Vector, Point

m13 = problem.blocks[13].mesh
normal = m13.face_normal(8)
normal_v = Vector(*normal)
normal_v.invert()
point_of_application = m13.vertex_coordinates(0)
pp = Vector(*point_of_application)
pv = Vector.sum_vectors([pp, normal_v])
load_strings += problem.set_point_load(point_of_application, pv, 7692.3, 0.02, 1)

m25 = problem.blocks[25].mesh
normal = m25.face_normal(5)
normal_v = Vector(*normal)
normal_v.invert()
point_of_application = m25.vertex_coordinates(3)
pp = Vector(*point_of_application)
pv = Vector.sum_vectors([pp, normal_v])
load_strings += problem.set_point_load(point_of_application, pv, 7692.3, 0.02, 1)

load_file = problem.set_load_analysis(load_strings, 13000, 1000)


# =============================================================================
# run 3DEC
# =============================================================================
problem.run([load_file])


# =============================================================================
# read results
# =============================================================================
init_dict = problem.from_3dec_blocks("init_state.txt")
mapping_dict = problem.mapping(init_dict)
# grav_dict = problem.from_3dec_blocks("grav_state.txt")
load_dict = problem.from_3dec_blocks("Load_step_13_load_magnitude_13000 N.txt")
problem.solve_ratio_check("Load_step_13_load_magnitude_13000 N.txt")
problem.update_blocks(load_dict, mapping_dict)
output_3dec_per_vertex = problem.from_3dec_contacts("Load_step_13_load_magnitude_13000 N_contacts.txt")

HERE = os.path.dirname(__file__)
FILE_O = os.path.join(HERE, "problem_load.json")
problem = compas.json_dump(problem, FILE_O)

# viewer = Viewer()

# viewer.scene.add(m13)
# viewer.show()

# =============================================================================
# end analysis
# =============================================================================
end = time.time()
print("analysis_3dec time", end - start)
