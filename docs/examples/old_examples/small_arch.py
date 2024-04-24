#! python3
import time
start = time.time()
from compas.scene import Scene
from compas.datastructures import Mesh
from compas_3dec.blockelement3dec import BlockElement
from compas_3dec.model_3dec import Model_3dec
from compas_3dec.data.arch import Arch
import os

# from compas_viewer import Viewer
from compas.colors import Color
from compas_3dec.interactions_3dec import Interaction3dec
from compas_3dec.rigid_interaction import RigidInteraction


# =============================================================================
# Input
# =============================================================================
arch = Arch(rise=0.5, span=3, thickness=0.08, depth=0.5, n=5)
meshes = arch.blocks()
# =============================================================================
# Model
# =============================================================================
# model = Model_3dec(working_path = r"C:\Users\adellend\Code2\compas_3dec\docs\examples" )
model = Model_3dec(working_path = os.path.dirname(__file__))
for m in meshes:
    model.add_element(BlockElement(m))
model.elementlist[0].is_support = True
model.elementlist[-1].is_support = True

# =============================================================================
# create geometry.dat
# =============================================================================
model.to_3dec_geometry_interactions()

# =============================================================================
# input material
# =============================================================================
# to be moved to compas_model
model.threedec_config.add_material("concrete", 2200, 35, 10000000, 0.8)

# =============================================================================
# create analysis.dat files
# =============================================================================
# calculate joint stiffness from material and geometric input
# to be changed considering the Material class from compas_model
model.threedec_config.get_joint_stiffness_one_material("concrete", 1, 0.05)
gravity_dat = model.threedec_config.set_gravity_analysis("concrete")

# =============================================================================
# run 3dec solver
# =============================================================================
model.run([gravity_dat])

# =============================================================================
# read results
# =============================================================================
init_dict = model.from_3dec_blocks("init_state.txt")
mapping_dict = model.mapping(init_dict)
grav_dict = model.from_3dec_blocks("grav_state.txt")
model_gravity = model.update_blocks(grav_dict,mapping_dict)
# output_3dec_per_vertex = model.from_3dec_contacts("contact_grav.txt")
output_3dec_per_vertex = model.from_3dec_contacts_resultant("contact_grav.txt")

#____________________________
scene = Scene()
scene.clear()
scene.add(model)
scene.draw()
#____________________________
end = time.time()
print("analysis_3dec time", end - start)
