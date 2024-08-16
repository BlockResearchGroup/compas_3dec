import time
start = time.time()
import os
import compas
from compas.colors import Color
from compas_viewer import Viewer
from compas_3dec.datastructure.problem_3dec import Problem3dec
from compas_3dec.datastructure.failure_criteria import MohrCoulomb
from compas_3dec.datastructure.group import Group

# =============================================================================
# Input
# =============================================================================
HERE = os.path.dirname(__file__)
FILE = os.path.join(HERE, "meshes.json")
meshes = compas.json_load(FILE)

# =============================================================================
# Init Problem3dec
# =============================================================================
problem = Problem3dec(working_path="C:\\Users\\adellend\\Code2\\compas_3dec\\src\\compas_3dec\\datas")


# =============================================================================
# add blocks
# =============================================================================
problem.add_blocks(meshes)


# =============================================================================
# Define supports based on z coordinate
# =============================================================================
for block in problem.blocks:
    zc = block.mesh.vertices_attribute("z")
    for i in zc:
        if -0.005 <= i <= 0.005:
            block.is_support = True


# =============================================================================
# add/assign groups
# =============================================================================
group1 = Group(name="Blocks")
group2 = Group(name="Supports")
problem.add_group(group1)
problem.add_group(group2)

for b in problem.blocks:
    if not b.is_support:
        b.group = group1.name
    else:
        b.group = group2.name
        b.color = Color.blue()


# =============================================================================
# add material
# =============================================================================
concrete = problem.add_material(name="Marble", E=2.5e10, poisson=0.2, rho=2500, group=[group1.name, group2.name])


# =============================================================================
# add contact_properties
# =============================================================================
stiffness_1 = problem.set_joint_stiffness_one_material(
    block_height=0.211, reduction_factor=1, block_length=None, material=concrete
)

failure_criteria = MohrCoulomb(friction=54)
contact_property = problem.add_contact_property(stiffness_1, failure_criteria, [group1.name, group2.name])

# =============================================================================
# save problem init
# =============================================================================
HERE = os.path.dirname(__file__)
FILE_O = os.path.join(HERE, "problem_init.json")
compas.json_dump(problem, FILE_O)


# =============================================================================
# create geometry.dat
# =============================================================================
problem.to_geometry_3dec()

# =============================================================================
# create gravity.dat
# =============================================================================
gravity_file = problem.gravity()

# =============================================================================
# run 3DEC
# =============================================================================
problem.run([gravity_file])

# =============================================================================
# read results
# =============================================================================
init_dict = problem.from_3dec_blocks("init_state.txt")
mapping_dict = problem.mapping(init_dict)
grav_dict = problem.from_3dec_blocks("grav_state.txt")
problem.solve_ratio_check("grav_state.txt")
problem.update_blocks(grav_dict, mapping_dict)
output_3dec_per_vertex = problem.from_3dec_contacts("contact_grav.txt")

# =============================================================================
# save problem gravity
# =============================================================================
HERE = os.path.dirname(__file__)
FILE_O = os.path.join(HERE, "problem_gravity.json")
compas.json_dump(problem, FILE_O)


# # =============================================================================
# # PT loads
# # =============================================================================
# from compas.geometry import Vector, Point
# load_strings = "; load" + "\n"
# for block in problem.blocks:
#     if block.is_support == False:
#         mesh = block.mesh
#         start = mesh.vertex_coordinates(2)
#         arc_centre = (2.790,0.300,-7.121)
#         # deviation_direction = (Vector.from_start_end(start, arc_centre)).unitized()
#         # deviation_vector = Point(*Vector.sum_vectors([start,deviation_direction]))
#         load = 1000
#         sphere_radius = 0.02
#         load_strings += problem.set_point_load(start,arc_centre, load, sphere_radius,1)

# from compas.geometry import Vector, Point
# m13 = problem.blocks[13].mesh
# normal = m13.face_normal(8)
# normal_v = Vector(*normal)
# normal_v.invert()
# point_of_application = m13.vertex_coordinates(0)
# pp = Vector(*point_of_application)
# pv = Vector.sum_vectors([pp,normal_v])
# load_strings += problem.set_point_load(point_of_application,pv,7692.3,0.02,1)

# m25 = problem.blocks[25].mesh
# normal = m25.face_normal(5)
# normal_v = Vector(*normal)
# normal_v.invert()
# point_of_application = m25.vertex_coordinates(3)
# pp = Vector(*point_of_application)
# pv = Vector.sum_vectors([pp,normal_v])
# load_strings += problem.set_point_load(point_of_application,pv,7692.3,0.02,1)


# load_file = problem.set_load_analysis(load_strings,13000,1000)


# =============================================================================
# run 3DEC
# =============================================================================
# problem.run([load_file])


# =============================================================================
# end analysis
# =============================================================================
end = time.time()
print("analysis_3dec time", end - start)


# # =============================================================================
# # View
# # =============================================================================
viewer = Viewer()
# viewer.scene.add([meshes])

# viewer.scene.clear()
for interaction in problem.interactions:
    if interaction.forces_per_contact:
        application_point = interaction.display_resultant_application_point()
        application_point_shear = interaction.display_resultant_shear_application_point()
        resultant_force = interaction.display_resultant_force(scale_factor=0.005)
        resultant_normal = interaction.display_resultant_normal(scale_factor=0.005)
        resultant_shear = interaction.display_resultant_shear(scale_factor=0.005)
        resultant_shear_transported = interaction.display_resultant_shear_transported(scale_factor=0.005)
        resultant_torque = interaction.display_resultant_torque(scale_factor=0.005)
        viewer.scene.add([application_point])

        for line in resultant_force:
            viewer.scene.add(line, color=Color.from_rgb255(0, 166, 12))


for block in problem.blocks:
    viewer.scene.add(block.mesh, color=block.color_equilibrium)

viewer.show()
