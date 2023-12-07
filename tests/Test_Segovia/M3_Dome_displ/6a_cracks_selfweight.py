import os
import time
import compas
import rhinoscriptsyntax as rs
from adem.threedec import mesh_block_map_dict_concave
from adem.threedec import threedec_data_init_grav_step_concave
from adem.threedec import update_concave
from adem.threedec import threedec_data_contact_step
from adem.file_management import get_blocks_from_json_file_2
from adem.threedec import cracks

# ==============================================================================
# Initialise folders and layers
# ==============================================================================
compas.PRECISION = "10"
start = time.time()
HERE = os.path.dirname(__file__)
readpath = os.path.join(HERE, "json_data")

displ_x = 0.0
displ_y = 0.0
displ_z = 0.0
for n in range(0, 1):
    filename = threedec_data_contact_step(n, displ_x, displ_y, displ_z)
    # get geometry from json
    support_blocks = get_blocks_from_json_file_2(HERE, "supports.json")
    compound_blocks = get_blocks_from_json_file_2(HERE, "blocks.json")
    # mapping + mechanical update
    blocks, blocks_grav, blocks_step = threedec_data_init_grav_step_concave(
        "init_state.txt", "grav_state.txt", n, 0.0, 0.0, 0.0, True
    )
    bindex_mindex = mesh_block_map_dict_concave(blocks, support_blocks, compound_blocks, 2, 2)
    up_mesh = update_concave(bindex_mindex, blocks_step, 2)
    cracks(filename, up_mesh, 0.0001, 0.0001, 0.01)

    # rs.AddLayer('new')
    # rs.CurrentLayer('new')
    # rs.LayerVisible('Default',False)

end = time.time()
print("analysis_3dec time", end - start)
