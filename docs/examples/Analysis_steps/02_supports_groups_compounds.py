import os
import time
start = time.time()
import compas
from compas.scene import Scene
from compas_3dec.datastructures.problem3dec import MohrCoulomb

# =============================================================================
# Input
# =============================================================================
HERE = os.path.dirname(__file__)
FILE = os.path.join(HERE, 'problem.json')
problem = compas.json_load(FILE)

# =============================================================================
# add supports
# =============================================================================
problem.blocks[0].is_support = True
problem.blocks[-1].is_support = True

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
concrete = problem.add_material(name="Concrete", E=30e9, poisson=0.2, rho=2400, group = ["Blocks", "Supports"])

# =============================================================================
# add contact_properties
# =============================================================================
stiffness_1 = problem.set_joint_stiffness_one_material(
    block_height=0.5,
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
# save to json
# =============================================================================
HERE = os.path.dirname(__file__)
FILE = os.path.join(HERE, 'problem.json')
compas.json_dump(problem, FILE)

end = time.time()
print("input_geometry", end - start)
