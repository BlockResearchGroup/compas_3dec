import time
start = time.time()
import os
import compas
from compas.colors import Color
from compas_3dec.datastructure.problem_3dec import Problem3dec
from compas_3dec.datastructure.failure_criteria import MohrCoulomb
from compas_3dec.datastructure.group import Group


# =============================================================================
# Input meshes
# =============================================================================
HERE = os.path.dirname(__file__)
FILE_I = os.path.join(HERE, 'meshes_3dec.json')
meshes = compas.json_load(FILE_I)

# =============================================================================
# Init Problem3dec
# =============================================================================
problem = Problem3dec(working_path='C:\\Users\\adellend\\Code2\\compas_3dec\\scripts')


# =============================================================================
# Add blocks
# =============================================================================
problem.add_blocks(meshes)


# =============================================================================
# Define supports based on z coordinate
# =============================================================================
for block in problem.blocks:
    zc = block.mesh.vertices_attribute('z')
    for i in zc:
        if -0.25 <= i <= -0.20:
            block.is_support = True


# =============================================================================
# Add and assign groups
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
marble = problem.add_material(name="Marble", E=2.5e10, poisson=0.2, rho=2000, group = [block_group.name, support_group.name])


# =============================================================================
# Add contact properties
# =============================================================================
stiffness = problem.set_joint_stiffness_one_material(
    block_height=0.8,
    reduction_factor=1,
    block_length=None,
    material = marble)

failure_criteria = MohrCoulomb(friction=40)
contact_property = problem.add_contact_property(stiffness, failure_criteria, [block_group.name])
failure_criteria_support = MohrCoulomb(friction=90)
contact_property_supports = problem.add_contact_property(stiffness, failure_criteria_support, [support_group.name])

# =============================================================================
# Save problem init
# =============================================================================
FILE_O = os.path.join(HERE, 'problem_init_jk1.json')
compas.json_dump(problem, FILE_O)
end = time.time()
print('analysis_3dec time', end - start)

print(problem.contact_properties)

