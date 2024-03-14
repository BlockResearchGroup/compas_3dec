import os
from compas_3dec.model_3dec import Model_3dec
from compas.colors import Color
from compas.geometry import Rotation

#from compas_viewer import Viewer
#from compas.scene import Scene
# from compas_notebook.viewer import Viewercls

# =============================================================================
# input geometry from obj
# =============================================================================
path_s = r"C:\Users\adellend\Code2\compas_3dec\src\compas_3dec\data\support.obj"
path_b = r"C:\Users\adellend\Code2\compas_3dec\src\compas_3dec\data\block.obj"


model = Model_3dec.model_from_obj(path_s, path_b)
print(model.working_path)
# for element in model.elementlist:
#     element.transform(Rotation.from_axis_and_angle([0,1,0],0.1,[0,0,0]))

# =============================================================================
# create geometry.dat
# =============================================================================
model.to_3dec_geometry()

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
# print(model.threedec_config.get_model_timestep())
# displacement0 = model.threedec_config.set_blocks_displacement([0,4,7,9], displacement_direction = [0,0,10], displ_magnitude_per_step=0.001)
displacement1 = model.threedec_config.set_block_displacement(0, displacement_direction = [0,2,5], displ_magnitude_per_step=0.001)
model.threedec_config.set_displacement_analysis([displacement1], total_displacement = 0.003, displ_magnitude_per_step=0.001, solver_time = 3, displacement_capacity = False)

# init_dict = model.from_3dec_blocks("init_state.txt")
# mapping_dict = model.mapping(init_dict)
# grav_dict = model.from_3dec_blocks("grav_state.txt")
# model.update_blocks(grav_dict,mapping_dict)

# output_3dec_per_vertex = model.from_3dec_contacts_resultant("contact_grav.txt")




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
# viewer = Viewer()
# for m in model.elementlist:
#     me = m.geometry
#     viewer.add(me, opacity=0.5)
# for edge,interaction in model.graph.edges(True):
#     viewer.add(interaction["interaction"].contact_geometry, facescolor=Color.azure())
#     normal, shear, points, mesh_normal_stress, mesh_shear_stress, resultant_force = interaction["interaction"].vector_force_display(0.1)
#     viewer.add(normal,lineswidth=5, linescolor=Color.red())
#     viewer.add(shear, lineswidth=5, linescolor=Color.blue())
#     viewer.add(resultant_force,lineswidth=5, linescolor=Color.green())

#     # viewer.add(polygon)
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



