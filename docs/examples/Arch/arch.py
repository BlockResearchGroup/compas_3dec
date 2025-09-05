#! python3
# r: compas, tessagon
# venv: himass1

import time
start = time.time()
import os
import compas
from compas.colors import Color
from compas.geometry import Point, Line
from compas_dem.templates import ArchTemplate
from compas_dem.models import BlockModel
from compas_3dec.datastructure import Problem3dec, Group, MohrCoulomb, Interaction3dec

# =============================================================================
# Create Arch
# =============================================================================
rise = 2
span = 5
thickness = 0.3
depth = 0.3
n = 20
arch = BlockModel.from_template(ArchTemplate(rise,span,thickness,depth,n))

# =============================================================================
# Select supports
# =============================================================================
supports = [0,19]
for block in arch.blocks():
    if block.graphnode in supports:
        block.is_support = True

# =============================================================================
# Convert to 3DEC model
# =============================================================================
HERE = os.path.dirname(__file__)
problem: Problem3dec = Problem3dec.from_blockmodel(arch, working_path=HERE)

# =============================================================================
# add/assign groups
# =============================================================================
block_group = Group(name="Blocks")
support_group = Group(name="Supports")
problem.add_group(block_group)
problem.add_group(support_group)

for b in problem.blocks:
    if not b.is_support:
        b.group = block_group.name
    else:
        b.group = support_group.name
        b.color = Color.from_rgb255(89,154,255)

# =============================================================================
# add material
# =============================================================================
marble = problem.add_material(name="Marble", E=2.5e10, poisson=0.2, rho=2500, group = [block_group.name, support_group.name])

# =============================================================================
# add contact_properties
# =============================================================================
stiffness = problem.set_joint_stiffness_one_material(
    block_height=0.5,
    reduction_factor=1,
    block_length=None,
    material=marble)

failure_criteria = MohrCoulomb(friction=35)
contact_property = problem.add_contact_property(stiffness, failure_criteria, [block_group.name, support_group.name])

# =============================================================================
# Save problem_init
# =============================================================================
FILE_O = os.path.join(HERE, 'problem_init.json')
compas.json_dump(problem, FILE_O)

# =============================================================================
# To 3DEC geometry
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

# # =============================================================================
# # read results blocks and interactions
# # =============================================================================
init_dict = problem.from_3dec_blocks("init_state.txt")
mapping_dict = problem.mapping(init_dict)
grav_dict = problem.from_3dec_blocks("grav_state.txt")
problem.solve_ratio_check("grav_state.txt")
problem.update_blocks(grav_dict,mapping_dict)
output_3dec_per_vertex = problem.from_3dec_contacts("contact_grav.txt")

# =============================================================================
# save problem gravity
# =============================================================================
FILE_Og = os.path.join(HERE, 'problem_gravity.json')
compas.json_dump(problem, FILE_Og)

# =============================================================================
# Input problem init
# =============================================================================
FILE_I1 = os.path.join(HERE, 'problem_init.json')
problem_init: Problem3dec = compas.json_load(FILE_I1)

# =============================================================================
# Input problem gravity
# =============================================================================
FILE_I2 = os.path.join(HERE, 'problem_gravity.json')
problem_gravity: Problem3dec = compas.json_load(FILE_I2)

# =============================================================================
# View
# =============================================================================
from compas.scene import Scene
scene = Scene()
scene.clear_context()

# =============================================================================
# show blocks
# =============================================================================
for block in problem_gravity.blocks:
    scene.add(block.mesh, color = block.color_equilibrium)

# =============================================================================
# show contact forces
# =============================================================================
for interaction in problem_gravity.interactions:
    interaction: Interaction3dec
    if interaction.forces_per_contact:
        application_point = interaction.display_resultant_application_point()
        resultant_force = interaction.display_resultant_force(0.02)
        scene.add(application_point)
    for line in resultant_force:
        scene.add(line, color=(0, 81, 12), width=20.0)

# =============================================================================
# show support reaction magnitudes
# =============================================================================
resultants, magnitudes, components, resultant_points = problem_gravity.support_resultants(0.02)
import rhinoscriptsyntax as rs
for magnitude, point in zip(magnitudes, resultant_points):
    rs.AddTextDot(str(magnitude), point)

# =============================================================================
# draw geometry
# =============================================================================
scene.draw()

end = time.time()
print('analysis_3dec time', end - start, 's')   