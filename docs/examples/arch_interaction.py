from compas.scene import Scene
from compas.datastructures import Mesh
from compas_model.elements import BlockElement
from compas_3dec.model_3dec import Model_3dec
from compas_3dec.data.arch import Arch
import os
from compas_viewer import Viewer
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
model = Model_3dec()
for m in meshes:
    model.add_element(BlockElement(m))
model.elementlist[0].is_support = True
model.elementlist[-1].is_support = True

model.add_interaction(model.elementlist[1], model.elementlist[2], RigidInteraction())
model.add_interaction(model.elementlist[2], model.elementlist[3], RigidInteraction())
model.add_interaction(model.elementlist[-2], model.elementlist[-3], RigidInteraction())
model.add_interaction(model.elementlist[-3], model.elementlist[-4], RigidInteraction())
model.add_interaction(model.elementlist[-5], model.elementlist[-6], RigidInteraction())


# # =============================================================================
# # create geometry.dat
# # =============================================================================
# model.to_3dec_geometry_interactions()

# # =============================================================================
# # input material
# # =============================================================================
# # to be moved to compas_model
# model.threedec_config.add_material("concrete", 2200, 35, 5000000, 0.8)

# # =============================================================================
# # create analysis.dat files
# # =============================================================================
# # calculate joint stiffness from material and geometric input
# # to be changed considering the Material class from compas_model
# model.threedec_config.get_joint_stiffness_one_material("concrete", 1, 0.1)
# gravity_dat = model.threedec_config.set_gravity_analysis("concrete")

# # =============================================================================
# # run 3dec solver
# # =============================================================================
# model.run([gravity_dat])

# # =============================================================================
# # read results
# # =============================================================================
# init_dict = model.from_3dec_blocks("init_state.txt")
# mapping_dict = model.mapping(init_dict)
# grav_dict = model.from_3dec_blocks("grav_state.txt")
# model.update_blocks(grav_dict,mapping_dict)

# output_3dec_per_vertex = model.from_3dec_contacts("contact_grav.txt")




# print (model.update_contacts(contact_grav))
# model.update_contacts(contact_grav)
# model.print

# =============================================================================
# equilibrium check
# =============================================================================
# HERE = os.path.dirname(__file__)
# FILE = os.path.join(HERE, "grav_state.txt")
# model.solve_ratio_check("grav_state.txt")


# =============================================================================
# visualisation
# =============================================================================
# =============================================================================
# Viewer
# =============================================================================
# from compas_viewer import Viewer

# scene = Scene(context= "Notebook")
# scene.add(model.elementlist[0])
# scene.draw()
# # scene.draw()

from compas_notebook.viewer import Viewer
viewer = Viewer()
# scene = Scene(context= "Notebook")
for m in model.elementlist:
    viewer.scene.add(m)
viewer.show()














# for m in model.elementlist:
#     me = m.geometry
#     viewer.add(me, opacity=0.5)
# for edge,interaction in model.graph.edges(True):
#     if isinstance(interaction["interaction"], Interaction3dec):
#     # viewer.add(interaction["interaction"].contact_geometry, facescolor=Color.azure())
#         normal, shear, points, mesh_normal_stress, mesh_shear_stress = interaction["interaction"].vector_force_display(0.05)
#         viewer.add(normal,lineswidth=3, linescolor=Color.red())
#         viewer.add(shear, lineswidth=3, linescolor=Color.blue())
#         viewer.add(points, show_points=True, pointssize=10)
#         viewer.add(mesh_normal_stress, use_vertexcolors=True)
#     # viewer.add(mesh_shear_stress, use_vertexcolors=True)

#     # viewer.add(polygon)
# viewer.show()
