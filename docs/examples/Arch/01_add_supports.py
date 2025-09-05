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
FILE = os.path.join(HERE, 'arch_00.json')
arch = compas.json_load(FILE)

# =============================================================================
# Select supports
# =============================================================================
supports = [0,19]
for block in arch.blocks():
    if block.graphnode in supports:
        block.is_support = True
   
# =============================================================================
# Save Blockmodel
# =============================================================================
HERE = os.path.dirname(__file__)
FILE_O = os.path.join(HERE, 'arch_01.json')
compas.json_dump(arch, FILE_O)

# =============================================================================
# View in Rhino
# =============================================================================
scene = Scene()
scene.clear_context()
for block in arch.blocks():
    scene.add(block._geometry)
for support in arch.supports():
    scene.add(support._geometry, color= (255,0,0))
scene.draw()