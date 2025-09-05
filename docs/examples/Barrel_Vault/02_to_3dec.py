#! python 3
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
FILE = os.path.join(HERE, 'barrel_vault_01.json')
barrel_vault: BlockModel= compas.json_load(FILE)

# =============================================================================
# Convert to 3DEC model
# =============================================================================
problem: Problem3dec = Problem3dec.from_blockmodel(barrel_vault, working_path=HERE)


# =============================================================================
# add/assign groups
# =============================================================================
block_group = Group(name="Blocks")
support_group = Group(name="Supports")
problem.add_group(block_group)
problem.add_group(support_group)

# =============================================================================
# add material
# =============================================================================
concrete = problem.add_material(name="Concrete", E=30e9, poisson=0.2, rho=22000, group=[block_group.name, support_group.name])

# =============================================================================
# add contact_properties
# =============================================================================
stiffness = problem.set_joint_stiffness_one_material(
    block_height=0.5,
    reduction_factor=1,
    block_length=None,
    material=concrete)

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

