import os
from compas_3dec.model_3dec import Model_3dec
from compas.colors import Color

#from compas_viewer import Viewer
#from compas.scene import Scene
# from compas_notebook.viewer import Viewer

# =============================================================================
# input geometry from obj
# =============================================================================
path_s = r"C:\Users\adellend\Code2\compas_3dec\src\compas_3dec\data\support.obj"
path_b = r"C:\Users\adellend\Code2\compas_3dec\src\compas_3dec\data\block.obj"

model = Model_3dec.model_from_obj(path_s, path_b)

# =============================================================================
# create geometry.dat
# =============================================================================
model.to_3dec_geometry()

# =============================================================================
# input material
# =============================================================================
# to be moved to compas_model
model.threedec_config.add_material("concrete", 2200, 35, 5000000, 0.2)

# =============================================================================
# create analysis.dat files
# =============================================================================
# calculate joint stiffness from material and geometric input
# to be changed considering the Material class from compas_model
model.threedec_config.get_joint_stiffness_one_material("concrete", 1, 10)
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

contact_grav = model.from_3dec_contacts("contact_grav.txt")
print(contact_grav)
print (model.update_contacts(contact_grav))
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
# viewer = Viewer()
# for m in model.elements_list:
#     me = m.geometry
#     viewer.add(me,  color=Color.azure())
# viewer.show()

#viewer = Viewer()
#for index, block_element in enumerate(model.elements_list):
#    # print(block_element.geometry)
#    if block_element.is_support:
#        viewer.add(block_element.geometry, linescolor=Color.red())
#    else:
#        viewer.add(block_element.geometry)
#viewer.show()




# for key,item in model.elements.items():
#     for k,a in item.geometry.vertices(True):
#         # print (k,item.geometry.vertex_coordinates(k))
#     for key in item.geometry.faces():
        # print (item.geometry.face_vertices(key))



