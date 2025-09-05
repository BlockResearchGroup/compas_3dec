import os
import compas
from compas_3dec.datastructure.problem_3dec import Problem3dec
from compas.colors import Color

# =============================================================================
# Input problem init
# =============================================================================
HERE = os.path.dirname(__file__)
FILE_I1 = os.path.join(HERE, 'problem_init.json')
problem_init: Problem3dec = compas.json_load(FILE_I1)

# =============================================================================
# Input problem gravity
# =============================================================================
FILE_I2 = os.path.join(HERE, 'problem_gravity.json')
problem_gravity: Problem3dec = compas.json_load(FILE_I2)


# =============================================================================
# View
# =============================================================================
from compas.scene import Scene
scene = Scene()
scene.clear_context()

# =============================================================================
# show blocks
# =============================================================================
for block in problem_gravity.blocks:
    scene.add(block.mesh, color = block.color_equilibrium)

# =============================================================================
# show contact forces
# =============================================================================
from compas_3dec.datastructure import Interaction3dec
for interaction in problem_gravity.interactions:
    interaction: Interaction3dec
    if interaction.forces_per_contact:
        application_point = interaction.display_resultant_application_point()
        resultant_force = interaction.display_resultant_force(0.002)
        scene.add(application_point)
    for line in resultant_force:
        scene.add(line, color=(0, 81, 12), width=20.0)


# resultants, magnitudes, components = problem_gravity.support_resultants(0.002)

# import rhinoscriptsyntax as rs
# for line,mag in zip(resultants,magnitudes):
#     scene.add(line, color=Color.red(), width=20.0)
#     rs.AddTextDot(str(mag), line.midpoint)




# =============================================================================
# draw geometry
# =============================================================================
scene.draw()