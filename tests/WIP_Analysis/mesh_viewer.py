from compas_3dec.results import rhinoview
from adem.rhino import mesh_view

import os
import compas


HERE = os.path.dirname("C:/Users/adellend/Code/compas_3dec/src/compas_3dec/Analysis/WIP/")
FILE_I = os.path.join(HERE, "Test_mesh.json")
mesh_list = compas.json_load(FILE_I)

for m in mesh_list:
    mesh_view(m)
