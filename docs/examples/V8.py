import time
start = time.time()
import compas.colors
from compas_3dec.datastructures.problem3dec import Problem3dec, Group, MohrCoulomb, Interaction3dec
from compas_3dec.data.arch import Arch
import os
import compas

# =============================================================================
# Input
# =============================================================================
HERE = os.path.dirname(__file__)
FILE = os.path.join(HERE, 'meshes.json')
meshes = compas.json_load(FILE)

from compas.geometry import Box, Frame
frameb = Frame([0,0,-0.125],[1,0,0],[0,1,0])
base = Box(7,7,0.25,frame = frameb)
base = Box.to_mesh(base)

meshes.append(base)

# =============================================================================
# Init Problem3dec
# =============================================================================
problem = Problem3dec(working_path='C:\\Users\\adellend\\Code2\\compas_3dec\\docs\\examples')

# =============================================================================
# add blocks
# =============================================================================
problem.add_blocks(meshes)

# =============================================================================
# Define supports based on z coordinate
# =============================================================================
for block in problem.blocks:
    zc = block.mesh.vertices_attribute('z')
    for i in zc:
        if -0.3 <= i <= -0.009:
            block.is_support = True



# =============================================================================
# add/assign groups
# =============================================================================
problem.add_group("Blocks")
problem.add_group("Supports")

for b in problem.blocks:
    if not b.is_support:
        b.group = problem.get_group_by_name("Blocks")
    else:
        b.group = problem.get_group_by_name("Supports")

# =============================================================================
# add compounds
# =============================================================================
# problem.add_rigid_interactions([[3,4,5],[7,8]])

# =============================================================================
# add material
# =============================================================================
concrete = problem.add_material(name="Concrete", E=30e9, poisson=0.2, rho=1500, group = ["Blocks", "Supports"])

# =============================================================================
# add contact_properties
# =============================================================================
stiffness_1 = problem.set_joint_stiffness_one_material(
    block_height=1.0,
    reduction_factor=1,
    block_length=None,
    material_name="Concrete")

failure_criteria = MohrCoulomb(friction=35)

contact_property = problem.add_contact_property(stiffness_1, failure_criteria, ["Blocks","Supports"])

# =============================================================================
# create geometry.dat
# =============================================================================
problem.to_geometry_3dec()

# =============================================================================
# create gravity.dat
# =============================================================================
gravity_file = problem.gravity()

# # =============================================================================
# # run 3DEC
# # =============================================================================
problem.run([gravity_file])

# # =============================================================================
# # read results
# # =============================================================================
init_dict = problem.from_3dec_blocks("init_state.txt")
mapping_dict = problem.mapping(init_dict)
grav_dict = problem.from_3dec_blocks("grav_state.txt")
problem.solve_ratio_check("grav_state.txt")
problem.update_blocks(grav_dict,mapping_dict)
output_3dec_per_vertex = problem.from_3dec_contacts("contact_grav.txt")

# # =============================================================================
# # view
# # =============================================================================
from compas.scene import Scene
from compas.colors import Color
import rhinoscriptsyntax as rs
rs.DeleteObjects(rs.AllObjects())
scene = Scene()
scene.clear()
scene.clear_objects()
for interaction in problem.interactions:
    if interaction.forces_per_contact:
        application_point = interaction.display_resultant_application_point()
        application_point_shear = interaction.display_resultant_shear_application_point()
        resultant_force = interaction.display_resultant_force(scale_factor=0.005)
        resultant_normal = interaction.display_resultant_normal(scale_factor=0.005)
        resultant_shear = interaction.display_resultant_shear(scale_factor=0.005)
        resultant_shear_transported = interaction.display_resultant_shear_transported(scale_factor=0.005)
        resultant_torque = interaction.display_resultant_torque(scale_factor=0.005)

        for line in resultant_force:
            scene.add(line, color= Color.from_rgb255(0, 166, 12))
        for line in resultant_normal:
            scene.add(line, color= Color.from_rgb255(0, 47, 167))
        for line in resultant_shear_transported:
            scene.add(line, color= Color.from_rgb255(166, 0, 62))
        for line in resultant_shear:
            scene.add(line, color= Color.from_rgb255(166, 0, 62))
        for line in resultant_torque:
            scene.add(line, color= Color.from_rgb255(166, 118, 0))
        scene.add(application_point)
        scene.add(application_point_shear)

for block in problem.blocks:
    # scene.add(block.mesh)
    scene.add(block.mesh, color = block.color_equilibrium)
scene.draw()



# =============================================================================
# view
# =============================================================================
# from compas.scene import Scene
# scene = Scene()
# for block in problem.blocks:
#     scene.add(block.mesh, color = block.color_equilibrium)
# scene.draw()


# for b in problem.blocks:

#     print(b)


# for interaction in problem.rigid_interactions:
#     print(interaction)

end = time.time()
print("analysis_3dec time", end - start)
