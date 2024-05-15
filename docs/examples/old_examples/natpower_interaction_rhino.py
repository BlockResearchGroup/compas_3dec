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


import compas
import pathlib
from compas.scene import Scene


HERE = pathlib.Path(__file__).parent
# rootdir = HERE / "SESSION"
# filepath = rootdir / "meshes.json"

# HERE = os.path.dirname(__file__)
rootdir = HERE
filepath = rootdir / "meshes.json"


# =============================================================================
# Input
# =============================================================================
meshes = compas.json_load(filepath)
# =============================================================================
# Model
# =============================================================================
# model = Model_3dec(working_path = r"C:\Users\adellend\Code2\compas_3dec\docs\examples" )
model = Model_3dec(working_path = os.path.dirname(__file__))
for m in meshes:
    model.add_element(BlockElement(m))

# close mesh
# for element in model.elementlist:
#     vertices = element.geometry.vertices_on_boundaries()
#     for v in vertices:
#         element.geometry.add_face(v)

# check vertices to define supports
for element in model.elementlist:
    zc = element.geometry.vertices_attribute('z')
    for i in zc:
        if -0.1 <= i <= 0.1:
            element.is_support = True

#show graph nodes
# import rhinoscriptsyntax as rs
# for i in model.elementlist:
#     centroid = i.geometry.centroid()
#     node = i.graph_node
#     rs.AddTextDot(node, centroid)
model2 = Model_3dec(working_path = os.path.dirname(__file__))
for e in model.elementlist:
    # if e.graph_node != 54 and e.graph_node != 46:
    if e.graph_node > 34 and e.graph_node != 54 and e.graph_node != 46:
    # if e.graph_node >34:
        centroid = e.geometry.centroid()
        node = e.graph_node
        # rs.AddTextDot(node, centroid)
        vertices = e.geometry.vertices_on_boundaries()
        for v in vertices:
            e.geometry.add_face(v)
        model2.add_element(e)








# model.elementlist[0].is_support = True
# model.elementlist[-1].is_support = True
# rigidinteraction = RigidInteraction()
# model.add_interaction(model.elementlist[1], model.elementlist[2], rigidinteraction)
# model.add_interaction(model.elementlist[2], model.elementlist[3], interaction=RigidInteraction())
# model.add_interaction(model.elementlist[-2], model.elementlist[-3], interaction=RigidInteraction())
# model.add_interaction(model.elementlist[-3], model.elementlist[-4], interaction=RigidInteraction())
# model.add_interaction(model.elementlist[-5], model.elementlist[-6], interaction=RigidInteraction())

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
# init_dict = model.from_3dec_blocks("init_state.txt")
# mapping_dict = model.mapping(init_dict)
# grav_dict = model.from_3dec_blocks("grav_state.txt")
# model.solve_ratio_check("grav_state.txt")
# model_gravity = model.update_blocks(grav_dict,mapping_dict)
# # output_3dec_per_vertex = model.from_3dec_contacts("contact_grav.txt")
# output_3dec_per_vertex = model.from_3dec_contacts_resultant("contact_grav.txt")



# # from compas_notebook.viewer import Viewer
# scene = Scene()
# scene.clear()
# # viewer = Viewer()
# # viewer.scene.context = "Rhino"
# # for edge, attr in model.graph.edges(True):
# #     if isinstance(attr["interaction"], Interaction3dec):
# #         scene.add(attr["interaction"],
# #         show_normal_force_lines=True,
# #         show_shear_force_lines=False,
# #         show_points = True,
# #         show_mesh_normal_stress = True,
# #         show_mesh_shear_stress = False,
# #         )


# # for e in model.elementlist:
# #     scene.add(e)
# scene.add(model)
# scene.draw()
# # scene = Scene(context= "Notebook")
# # for e in model.elementlist:
# #     viewer.scene.add(e)

# # for edge, interaction in model.graph.edges(True):
# #     # print(edge, interaction)
# #     if isinstance(interaction["interaction"], Interaction3dec):
# #         viewer.scene.add(
# #         interaction["interaction"],
# #         show_normal_force_lines=True,
# #         show_shear_force_lines=False,
# #         show_points = True,
# #         show_mesh_normal_stress = True,
# #         show_mesh_shear_stress = False,
# #         )

# # viewer.show()

# scene = Scene()
# scene.clear_objects()
# scene.clear()

# for e in model.elementlist:
#     # if e.graph_node != 54 and e.graph_node != 46:
#     if e.graph_node > 34 and e.graph_node != 54 and e.graph_node != 46:
#     # if e.graph_node >34:
#         centroid = e.geometry.centroid()
#         node = e.graph_node
#         # rs.AddTextDot(node, centroid)
#         vertices = e.geometry.vertices_on_boundaries()
#         for v in vertices:
#             e.geometry.add_face(v)

#         scene.add(e)


# scene.add(model2)
# scene.draw()




# scene = Scene()
# scene.clear()


# # for m in meshes:
# #     scene.add(m)

# for e in model.elementlist:
#     scene.add(e)

# scene.draw()
