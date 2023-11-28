import os
import compas
import compas_rhino
import rhinoscriptsyntax as rs
from compas_3dec.utilities import timestep
from compas_3dec.utilities import displacement_settings
from compas_3dec.utilities import cycle_displ_n
from compas_3dec.utilities import displacement_file

# # ==============================================================================
# # import
# # ==============================================================================
HERE = os.path.dirname(__file__)
FILE = os.path.join(HERE, 'assembly_3dec.json')
assembly_3dec = compas.json_load(FILE)

for node in assembly_3dec.nodes():
    centroid = assembly_3dec.node_block(node).centroid()
    rs.AddLayer('IDs')
    rs.CurrentLayer('IDs')
    compas_rhino.rs.AddTextDot(int(node)+1,centroid)

FILE_1 = os.path.join(HERE, 'grav_state.txt')
displ, d_steps, n_steps, d_vector, region = displacement_settings()
timest = timestep(FILE_1)
cycle = cycle_displ_n(d_steps,timest)

displacement_file(HERE,n_steps,0.0,0.0,0.0,1,3,cycle,d_vector,'Analysis_test',region)









