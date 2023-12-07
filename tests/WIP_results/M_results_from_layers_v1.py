import os
import compas
import time
import rhinoscriptsyntax as rs

from adem.file_management import get_blocks_from_json_file_2
from adem.threedec import mesh_block_map_dict_concave
from adem.threedec import threedec_data_init_grav_step_concave
from adem.threedec import update_concave
from adem.threedec import threedec_data_contact_step
from adem.threedec import contact_interface
from adem.threedec import contact_forces_light_test
from adem.rhino import mesh_view
from adem.rhino import init_layers_light

from compas.geometry import Vector

# ==============================================================================
# Initialise folders and layers
# ==============================================================================
start = time.time()
compas.PRECISION = "10"
DIR = os.path.dirname(__file__)
readpath = os.path.join(DIR, "json_data")
HERE = os.path.dirname(__file__)
# init_layers()
init_layers_light()

block_json = "blocks.json"
support_json = "supports.json"
other_json = "others.json"
displ_x = 0.0
displ_y = 0.0
displ_z = 0.0

# reaction output
WRITEPATH = os.path.join(DIR, "to_zha")
HERE = os.path.dirname(__file__)

filename1 = "forces.json"

# ==============================================================================
# mapping 3DEC/compas
# ==============================================================================
for n in range(27, 28):
    # get geometry from json
    support_blocks = get_blocks_from_json_file_2(HERE, "supports.json")
    compound_blocks = get_blocks_from_json_file_2(HERE, "blocks.json")

    # mapping + mechanical update
    blocks, blocks_grav, blocks_step = threedec_data_init_grav_step_concave(
        "init_state.txt", "grav_state.txt", n, 0.0, 0.0, 0.0, True
    )
    bindex_mindex = mesh_block_map_dict_concave(blocks, support_blocks, compound_blocks, 2, 3)
    up_mesh = update_concave(bindex_mindex, blocks_step)

    # 3DEC contacts data per step
    filename = threedec_data_contact_step(n, displ_x, displ_y, displ_z)

    # Mesh categorization based on out of balance
    for bkey in up_mesh.keys():
        if up_mesh[bkey]["status"] == "in":
            mesh = up_mesh[bkey]["mesh"]
            if up_mesh[bkey]["layer"] == "Layer 1":
                rs.CurrentLayer("Layer 1")
            if up_mesh[bkey]["layer"] == "Layer 2":
                rs.CurrentLayer("Layer 2")
            if up_mesh[bkey]["layer"] == "Layer 3":
                rs.CurrentLayer("Layer 3")
            if up_mesh[bkey]["layer"] == "Layer 4":
                rs.CurrentLayer("Layer 4")
            if up_mesh[bkey]["layer"] == "Layer 5":
                rs.CurrentLayer("Layer 5")
            if up_mesh[bkey]["layer"] == "Layer 6":
                rs.CurrentLayer("Layer 6")
            if up_mesh[bkey]["layer"] == "Layer 7":
                rs.CurrentLayer("Layer 7")
            if up_mesh[bkey]["layer"] == "Layer 8":
                rs.CurrentLayer("Layer 8")
            if up_mesh[bkey]["layer"] == "Support":
                rs.CurrentLayer("Support")
            # mesh_view(mesh)
            if up_mesh[bkey]["layer"] == "Slaves":
                rs.CurrentLayer("Slaves")
        mesh_view(mesh)

        # Ftot = contact_interface(filename, 0.00001)
        # json files name with geometry + mechanical info
        # for bkey in up_mesh.keys():
        fs, pt = contact_forces_light_test(filename, 0.0001, bkey, 0.466, False)

end = time.time()
print("analysis_3dec time", end - start)
