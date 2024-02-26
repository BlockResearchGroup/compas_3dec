from compas.scene import Scene
from compas.datastructures import Mesh
from compas_model.elements import BlockElement
from compas_3dec.model_3dec import Model_3dec
from compas_3dec.data.arch import Arch
import os
from compas_3dec.utilities import solve_ratio_check

# =============================================================================
# Input
# =============================================================================
arch = Arch(rise=5, span=10, thickness=0.5, depth=0.5, n=20)
meshes = arch.blocks()
# =============================================================================
# Model
# =============================================================================
model = Model_3dec()
group_supports = model.add_group("Supports")
group_blocks = model.add_group("Blocks")
support_0 = BlockElement(meshes[0], is_support=True)
support_1 = BlockElement(meshes[-1], is_support=True)
group_supports.add_element(support_0)
group_supports.add_element(support_1)

compound0 = group_blocks.add_group("Compound_0")
compound0.add_elements([BlockElement(meshes[1]), BlockElement(meshes[2])])

for i in range(3, len(meshes) - 1):
    group_blocks.add_element(BlockElement(meshes[i]))


# =============================================================================
# create geometry.dat
# =============================================================================
model.to_3dec_geometry()

# =============================================================================
# input material
# =============================================================================
# to be moved to compas_model
model.threedec_config.add_material("concrete", 2200, 35, 80000000, 0.2)

# =============================================================================
# create analysis.dat files
# =============================================================================
# calculate joint stiffness from material and geometric input
# to be changed considering the Material class from compas_model
model.threedec_config.get_joint_stiffness_one_material("concrete", 1, 0.1)
gravity_dat = model.threedec_config.set_gravity_analysis("concrete")

# =============================================================================
# run 3dec solver
# =============================================================================
model.run([gravity_dat])

# =============================================================================
# equilibrium check
# =============================================================================
HERE = os.path.dirname(__file__)
FILE = os.path.join(HERE, "grav_state.txt")
solve_ratio_check(FILE)
