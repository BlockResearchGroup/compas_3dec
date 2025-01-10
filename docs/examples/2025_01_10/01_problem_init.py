import time
start = time.time()
import os
import compas
from compas.colors import Color

# =============================================================================
# Input geometry
# =============================================================================
HERE = os.path.dirname(__file__)
FILE = os.path.join(HERE, 'geometry.json')
geometry = compas.json_load(FILE)

# =============================================================================
# Init Problem3dec
# =============================================================================
from compas_3dec.datastructure import Problem3dec, contact_property
problem = Problem3dec(working_path='C:\\Users\\adellend\\Code2\\compas_3dec\\docs\\examples\\2025_01_10')

# =============================================================================
# add blocks
# =============================================================================
problem.add_blocks(geometry)

# =============================================================================
# Define supports based on z coordinate
# =============================================================================
for block in problem.blocks:
    zc = block.mesh.vertices_attribute("z")
    for i in zc:
        if -0.001 <= i <= 0.001:
            block.is_support = True

# =============================================================================
# add/assign groups
# =============================================================================
from compas_3dec.datastructure import Group
block_group = Group(name="Blocks")
support_group = Group(name="Supports")
problem.add_group(block_group)
problem.add_group(support_group)

for b in problem.blocks:
    if not b.is_support:
        b.group = block_group.name
    else:
        b.group = support_group.name
        b.color = Color.blue()

# =============================================================================
# add material
# =============================================================================
concrete = problem.add_material(name="Concrete", E=30e9, poisson=0.2, rho=2400, group=[block_group.name, support_group.name])

# =============================================================================
# add contact_properties
# =============================================================================
from compas_3dec.datastructure import MohrCoulomb
stiffness = problem.set_joint_stiffness_one_material(
    block_height=0.5,
    reduction_factor=1,
    block_length=None,
    material=concrete)

failure_criteria = MohrCoulomb(friction=35)
contact_property = problem.add_contact_property(stiffness, failure_criteria, [block_group.name])

failure_criteria_support = MohrCoulomb(friction=90)
contact_property_supports = problem.add_contact_property(stiffness, failure_criteria_support, [support_group.name])

# =============================================================================
# Save problem_init
# =============================================================================
FILE_O = os.path.join(HERE, 'problem_init.json')
compas.json_dump(problem, FILE_O)
end = time.time()
print('problem_init_time', end - start,'s')

# =============================================================================
# View
# =============================================================================
from compas.scene import Scene
scene = Scene()
scene.clear_objects()   #doesn't work
for block in problem.blocks:
        scene.add(block.mesh, color=block.color)
scene.draw()
