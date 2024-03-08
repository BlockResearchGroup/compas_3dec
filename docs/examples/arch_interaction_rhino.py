#! python3
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
arch = Arch(rise=5, span=10, thickness=0.5, depth=0.5, n=20)
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
rigidinteraction = RigidInteraction()
model.add_interaction(model.elementlist[1], model.elementlist[2], rigidinteraction)
model.add_interaction(model.elementlist[2], model.elementlist[3], interaction=RigidInteraction())
model.add_interaction(model.elementlist[-2], model.elementlist[-3], interaction=RigidInteraction())
model.add_interaction(model.elementlist[-3], model.elementlist[-4], interaction=RigidInteraction())
model.add_interaction(model.elementlist[-5], model.elementlist[-6], interaction=RigidInteraction())

# =============================================================================
# create geometry.dat
# =============================================================================
model.to_3dec_geometry_interactions()

# =============================================================================
# input material
# =============================================================================
# to be moved to compas_model
model.threedec_config.add_material("concrete", 2200, 35, 5000000, 0.8)

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
# read results
# =============================================================================
init_dict = model.from_3dec_blocks("init_state.txt")
mapping_dict = model.mapping(init_dict)
grav_dict = model.from_3dec_blocks("grav_state.txt")
model.update_blocks(grav_dict,mapping_dict)

output_3dec_per_vertex = model.from_3dec_contacts("contact_grav.txt")



# from compas_notebook.viewer import Viewer
scene = Scene()
scene.clear()
# viewer = Viewer()
# viewer.scene.context = "Rhino"
for edge, attr in model.graph.edges(True):
    if isinstance(attr["interaction"], Interaction3dec):
        scene.add(attr["interaction"],
        show_normal_force_lines=True,
        show_shear_force_lines=False,
        show_points = True,
        show_mesh_normal_stress = True,
        show_mesh_shear_stress = False,
        )


for e in model.elementlist:
    scene.add(e)

scene.draw()
# scene = Scene(context= "Notebook")
# for e in model.elementlist:
#     viewer.scene.add(e)

# for edge, interaction in model.graph.edges(True):
#     # print(edge, interaction)
#     if isinstance(interaction["interaction"], Interaction3dec):
#         viewer.scene.add(
#         interaction["interaction"],
#         show_normal_force_lines=True,
#         show_shear_force_lines=False,
#         show_points = True,
#         show_mesh_normal_stress = True,
#         show_mesh_shear_stress = False,
#         )

# viewer.show()
