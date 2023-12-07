import os
import time
import compas
import compas_rhino
from compas.colors import Color
from compas.artists import Artist
import rhinoscriptsyntax as rs
from adem.threedec import mesh_block_map_dict_concave
from adem.threedec import threedec_data_init_grav_step_concave
from adem.threedec import update_concave
from adem.threedec import threedec_data_contact_step
from adem.file_management import get_blocks_from_json_file_2
from adem.rhino import init_layers_light
from adem.threedec import cracks
from compas_3dec.results import contact_interfaces
from compas_3dec.results import contact_forces_one_block
from compas_3dec.results import contact_interfaces_color_position

# ==============================================================================
# Initialise folders and layers
# ==============================================================================
user_choice = compas_rhino.rs.GetString("Select visualisation", strings=["contacts", "contacts_one_block"])


compas.PRECISION = "10"
start = time.time()
HERE = os.path.dirname(__file__)
readpath = os.path.join(HERE, "json_data")
init_layers_light()

import compas_rhino

step = compas_rhino.rs.GetString("Displacement step")

displ_x = 0.0
displ_y = 0.0
displ_z = 0.0
for n in range(int(step), int(step) + 1):
    filename = threedec_data_contact_step(n, displ_x, displ_y, displ_z)
    # get geometry from json
    support_blocks = get_blocks_from_json_file_2(HERE, "supports.json")
    compound_blocks = get_blocks_from_json_file_2(HERE, "blocks.json")
    # mapping + mechanical update
    blocks, blocks_grav, blocks_step = threedec_data_init_grav_step_concave(
        "init_state.txt", "grav_state.txt", n, 0.0, 0.0, 0.0, True
    )
    bindex_mindex = mesh_block_map_dict_concave(blocks, support_blocks, compound_blocks, 2, 3)
    up_mesh = update_concave(bindex_mindex, blocks_step, 2)
    for bkey in up_mesh.keys():
        if up_mesh[bkey]["status"] == "in":
            mesh = up_mesh[bkey]["mesh"]
            if up_mesh[bkey]["layer"] == "Layer 1":
                artist = Artist(mesh, layer="Layer 1")
                artist.draw(color=Color.from_rgb255(150, 150, 150))
                rs.CurrentLayer("Layer 1")
            if up_mesh[bkey]["layer"] == "Layer 2":
                artist = Artist(mesh, layer="Layer 2")
                artist.draw(color=Color.from_rgb255(255, 230, 231))
                rs.CurrentLayer("Layer 2")
            if up_mesh[bkey]["layer"] == "Layer 3":
                artist = Artist(mesh, layer="Layer 3")
                artist.draw(color=Color.from_rgb255(253, 204, 207))
                rs.CurrentLayer("Layer 3")
            if up_mesh[bkey]["layer"] == "Layer 4":
                artist = Artist(mesh, layer="Layer 4")
                artist.draw(color=Color.from_rgb255(250, 179, 183))
                rs.CurrentLayer("Layer 4")
            if up_mesh[bkey]["layer"] == "Layer 5":
                artist = Artist(mesh, layer="Layer 5")
                artist.draw(color=Color.from_rgb255(245, 153, 159))
                rs.CurrentLayer("Layer 5")
            if up_mesh[bkey]["layer"] == "Layer 6":
                artist = Artist(mesh, layer="Layer 6")
                artist.draw(color=Color.from_rgb255(239, 126, 136))
                rs.CurrentLayer("Layer 6")
            if up_mesh[bkey]["layer"] == "Layer 7":
                artist = Artist(mesh, layer="Layer 7")
                artist.draw(color=Color.from_rgb255(231, 98, 213))
                rs.CurrentLayer("Layer 7")
            if up_mesh[bkey]["layer"] == "Layer 8":
                artist = Artist(mesh, layer="Layer 8")
                artist.draw(color=Color.from_rgb255(222, 66, 91))
                rs.CurrentLayer("Layer 8")
            if up_mesh[bkey]["layer"] == "Support":
                artist = Artist(mesh, layer="Support")
                artist.draw(color=Color.from_rgb255(0, 150, 0))
                rs.CurrentLayer("Support")
            if up_mesh[bkey]["layer"] == "Slaves":
                artist = Artist(mesh, layer="Slaves")
                artist.draw(color=Color.from_rgb255(150, 150, 150))
                rs.CurrentLayer("Slaves")

    if user_choice == "contacts":
        contact_interfaces_color_position(filename, 0.00002, 100, up_mesh)
    if user_choice == "contacts_one_block":
        # HERE = os.path.dirname(__file__)
        # FILE = os.path.join(HERE, 'assembly_3dec.json')
        # assembly_3dec = compas.json_load(FILE)
        # for node in assembly_3dec.nodes():
        #     centroid = assembly_3dec.node_block(node).centroid()
        #     rs.AddLayer('IDs')
        #     rs.CurrentLayer('IDs')
        #     compas_rhino.rs.AddTextDot(int(node)+1,centroid)

        block_id = compas_rhino.rs.GetString("Block ID")
        contact_forces_one_block(filename, 0.00002, int(block_id), 35, 10, True, False)
    # contact_interfaces(filename,0.00002,10)
    # if user_choice == 'cracks':
    #     cracks(filename, up_mesh, 0.0001, 0.0001, 0.01)

    # contact_interfaces_color_position(filename,0.00002,100,up_mesh)
    # contact_interfaces(filename,0.00002,10)
    # contact_forces_one_block(filename, 0.00002, 6, 35, 10, True, False)
    # cracks(filename, up_mesh, 0.0001, 0.0001, 0.01)

    # rs.AddLayer('new')
    # rs.CurrentLayer('new')
    # rs.LayerVisible('Default',False)

end = time.time()
print("analysis_3dec time", end - start)
