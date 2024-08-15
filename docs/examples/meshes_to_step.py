import time
start = time.time()
from compas_3dec.datastructures.problem3dec import Problem3dec, Group, MohrCoulomb, Interaction3dec
from compas_3dec.data.arch import Arch
import os
import compas
from compas.geometry import Brep
# =============================================================================
# Input
# =============================================================================
HERE = os.path.dirname(__file__)
FILE = os.path.join(HERE, 'meshes.json')
meshes = compas.json_load(FILE)

from compas.geometry import Box, Frame
frameb = Frame([0,0,-0.125],[1,0,0],[0,1,0])
base = Box(7,7,0.25,frame = frameb)
base = Box.to_mesh(base)
meshes.append(base)

FILE2 = os.path.join(HERE, 'meshes.stp')
for mesh in meshes:
    Brep.from_mesh(mesh).to_step(FILE2)


end = time.time()
print("analysis_3dec time", end - start)
