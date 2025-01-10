import os
import compas
from compas.scene import Scene
from compas.colors import Color

HERE = os.path.dirname(__file__)
FILE_I1 = os.path.join(HERE, "problem_init.json")
problem_init = compas.json_load(FILE_I1)

FILE_I2 = os.path.join(HERE, "problem_gravity.json")
problem_gravity = compas.json_load(FILE_I2)

FILE_I3 = os.path.join(HERE, "problem_load.json")
problem_load = compas.json_load(FILE_I3)


viewer = Scene()
viewer.clear()

for block in problem_init.blocks:
    mesh_init = block.mesh
    viewer.add(mesh_init, color=Color.from_rgb255(0, 0, 255))

for block in problem_gravity.blocks:
    if not block.is_support:
        mesh_grav = block.mesh
        viewer.add(mesh_grav, color=Color.from_rgb255(255, 0, 0))

for block in problem_load.blocks:
    if not block.is_support:
        mesh_load = block.mesh
        viewer.add(mesh_load, color=Color.from_rgb255(0, 255, 0))


# =============================================================================
# Get resultants lines and magnitudes
# =============================================================================

res, mag, comp = problem_gravity.support_resultants(0.1)
for res, mag in zip(res, mag):
    viewer.add(res, color=Color.from_rgb255(0, 0, 0))
    viewer.add()
    viewer.add_tag(mag, res.end, height=5)

# =============================================================================
# Check resultant point positions inside or outside contact area
# =============================================================================
# pols, pts, pout, pnp = problem.check_resultant_points()

viewer.draw()
