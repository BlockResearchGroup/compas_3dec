#! python3
# r: compas, tessagon
# venv: himass1

import os
import compas
from compas_3dec.datastructure import Problem3dec, Interaction3dec
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
for interaction in problem_gravity.interactions:
    interaction: Interaction3dec
    if interaction.forces_per_contact:
        application_point = interaction.display_resultant_application_point()
        resultant_force = interaction.display_resultant_force(0.02)
        scene.add(application_point)
    for line in resultant_force:
        scene.add(line, color=(0, 81, 12), width=20.0)

# =============================================================================
# show support reaction magnitudes
# =============================================================================
resultants, magnitudes, components, resultant_points = problem_gravity.support_resultants(0.02)
import rhinoscriptsyntax as rs
for magnitude, point in zip(magnitudes, resultant_points):
    rs.AddTextDot(str(magnitude), point)

# =============================================================================
# draw geometry
# =============================================================================
scene.draw()