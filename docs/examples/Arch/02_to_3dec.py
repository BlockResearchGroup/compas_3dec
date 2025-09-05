#! python3
# r: compas, tessagon
# venv: himass1

import time
start = time.time()
import os
import compas
from compas.colors import Color
from compas.scene import Scene
from compas_dem.models import BlockModel
from compas_3dec.datastructure import Problem3dec, Group, MohrCoulomb

# =============================================================================
# Load Blockmodel
# =============================================================================
HERE = os.path.dirname(__file__)
FILE = os.path.join(HERE, 'arch_01.json')
arch: BlockModel= compas.json_load(FILE)

# =============================================================================
# Convert to 3DEC model
# =============================================================================
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
end = time.time()
print('time', end - start,'s')

# =============================================================================
# View
# =============================================================================
scene = Scene()
scene.clear_context()
for block in problem.blocks:
        scene.add(block.mesh, color=block.color)
scene.draw()

