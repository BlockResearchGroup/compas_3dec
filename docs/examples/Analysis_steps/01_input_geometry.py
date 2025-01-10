import os
import time
start = time.time()
import compas
from compas.scene import Scene
from compas_3dec.data.arch import Arch
from compas_3dec.datastructure import Problem3dec

# =============================================================================
# Input geometry
# =============================================================================
arch = Arch(rise=5, span=10, thickness=0.5, depth=0.5, n=20)
meshes = arch.blocks()

# =============================================================================
# Init Problem3dec
# =============================================================================
problem = Problem3dec(working_path='C:\\Users\\adellend\\Code2\\compas_3dec\\docs\\examples\\Analysis_step')

# =============================================================================
# add blocks
# =============================================================================
problem.add_blocks(meshes)

# =============================================================================
# save to json
# =============================================================================
HERE = os.path.dirname(__file__)
FILE = os.path.join(HERE, 'problem.json')
compas.json_dump(problem, FILE)

# =============================================================================
# View
# =============================================================================
import rhinoscriptsyntax as rs
rs.DeleteObjects(rs.AllObjects())
scene = Scene()
for block in problem.blocks:
    scene.add(block.mesh)
scene.draw()


end = time.time()
print("input_geometry", end - start)
