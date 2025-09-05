#! python 3
# r: compas, tessagon
# venv: himass1

import os
import compas
from compas.scene import Scene
from compas_dem.models.blockmodel import BlockModel

# =============================================================================
# Load Blockmodel
# =============================================================================
HERE = os.path.dirname(__file__)
FILE = os.path.join(HERE, 'barrel_vault_00.json')
barrel_vault = compas.json_load(FILE)

# =============================================================================
# Select supports
# =============================================================================
supports = [0,10,20,30,40,53,9,19,29,39,53,54]
for block in barrel_vault.blocks():
    if block.graphnode in supports:
        block.is_support = True
   
# =============================================================================
# Save Blockmodel
# =============================================================================
HERE = os.path.dirname(__file__)
FILE_O = os.path.join(HERE, 'barrel_vault_01.json')
compas.json_dump(barrel_vault, FILE_O)

# =============================================================================
# View in Rhino
# =============================================================================
# scene = Scene()
# scene.clear_context()
# for block in barrel_vault.blocks():
#     scene.add(block._geometry)
# for support in barrel_vault.supports():
#     scene.add(support._geometry, color= (255,0,0))
# scene.draw()