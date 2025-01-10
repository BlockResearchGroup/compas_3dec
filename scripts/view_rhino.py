import os
import compas
HERE = os.path.dirname(__file__)
FILE_I = os.path.join(HERE, 'meshes.json')
meshes = compas.json_load(FILE_I)


import os
import compas
HERE = os.path.dirname(__file__)
FILE_I = os.path.join(HERE, 'problem_gravity_jk1.json')
problem = compas.json_load(FILE_I)

from compas.scene import Scene
scene = Scene()

from compas_3dec.datastructure import Interaction3dec
for interaction in problem.interactions:
    interaction: Interaction3dec
    print(interaction.neighbours)

    # if interaction.forces_per_contact:

    #     application_point = interaction.display_resultant_application_point()
    #     resultant_force = interaction.display_resultant_force(0.01)
    #     scene.add(application_point)
    # for line in resultant_force:
    #     scene.add(line, color=(0, 81, 12), width=20.0)





# for mesh in meshes:
#     scene.add(mesh)

# scene.draw()
