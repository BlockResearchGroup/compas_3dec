import os
import compas
from compas_assembly.datastructures import Assembly
from compas_assembly.viewer import DEMViewer
from compas.artists import Artist



HERE = os.path.dirname('C:/Users/adellend/Code/compas_3dec/src/compas_3dec/Analysis/WIP/')
FILE_I = os.path.join(HERE, "Test_assembly.json")
init_assembly = compas.json_load(FILE_I)





viewer = DEMViewer()
viewer.view.camera.position = [0, -17, 5]
viewer.view.camera.look_at([0, 0, 3])
viewer.add_assembly(init_assembly)

viewer.run()
