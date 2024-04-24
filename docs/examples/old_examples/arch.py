from compas.scene import Scene
from compas.datastructures import Mesh
from compas_model.elements import BlockElement
from compas_3dec.model_3dec import Model_3dec
from compas_3dec.data.arch import Arch

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
# Material
# =============================================================================

model.threedec_config.add_material("concrete", 2200, 35, 300000, 0.2)
model.threedec_config.get_joint_stiffness_one_material("concrete", 0.20, 10)
test = model.threedec_config.get_gravity_input("concrete")
print (test)

model.run(True)
