#! python3
# r: compas, tessagon
# venv: himass1

import os
import compas
from compas.colors import Color
from compas.scene import Scene
from compas_3dec.datastructure import Problem3dec, Group, MohrCoulomb

# =============================================================================
# Input meshes
# =============================================================================
HERE = os.path.dirname(__file__)
FILE_I = os.path.join(HERE, 'meshes.json')
meshes = compas.json_load(FILE_I)

# =============================================================================
# Init Problem3dec
# =============================================================================
problem = Problem3dec(working_path=HERE)

# =============================================================================
# Add blocks
# =============================================================================
problem.add_blocks(meshes)

# =============================================================================
# Define supports based on z coordinate
# =============================================================================
for block in problem.blocks:
    z_coord = block.mesh.vertices_attribute('z')
    for i in z_coord:
        if -0.005 <= i <= 0.005:
            block.is_support = True

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
# Add material
# =============================================================================
marble = problem.add_material(name="Marble", E=2.5e10, poisson=0.2, rho=2500, group = [block_group.name, support_group.name])

# =============================================================================
# Add contact properties
# =============================================================================
stiffness = problem.set_joint_stiffness_one_material(
    block_height=0.211,
    reduction_factor=1,
    block_length=None,
    material = marble)

failure_criteria = MohrCoulomb(friction=35)
contact_property = problem.add_contact_property(stiffness, failure_criteria, [block_group.name, support_group.name])

# =============================================================================
# Save problem init
# =============================================================================
FILE_O = os.path.join(HERE, 'problem_init.json')
compas.json_dump(problem, FILE_O)


# =============================================================================
# View
# =============================================================================
scene = Scene()
scene.clear_context()
for block in problem.blocks:
        scene.add(block.mesh, color=block.color)
scene.draw()
