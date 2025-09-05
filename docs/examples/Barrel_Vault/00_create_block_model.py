#! python 3
# r: compas, tessagon
# venv: himass1

import os
import compas
from compas.colors import Color
from compas.geometry import Point, Line
from compas_dem.templates import BarrelVaultTemplate
from compas_dem.models import BlockModel
from compas.scene import Scene


# =============================================================================
# Create Barrel Vault
# =============================================================================
rise = 2
span = 5
length = 6
thickness = 0.3
vou_span = 10
vou_length = 5
barrel_vault = BlockModel.from_template(BarrelVaultTemplate(span, length, thickness, rise, vou_span, vou_length, False))    

# =============================================================================
# Save Blockmodel
# =============================================================================
HERE = os.path.dirname(__file__)
FILE_O = os.path.join(HERE, 'barrel_vault_00.json')
compas.json_dump(barrel_vault, FILE_O)

# =============================================================================
# View in Rhino
# =============================================================================
# scene = Scene()
# scene.clear_context()
# # import rhinoscriptsyntax as rs
# for block in barrel_vault.blocks():
#     scene.add(block._geometry)
#     scene.add(span_line, color = (255,0,0))
#     scene.add(rise_line, color=(0,255,0))
#     # rs.AddTextDot(block.graphnode,block._geometry.centroid())
# scene.draw()