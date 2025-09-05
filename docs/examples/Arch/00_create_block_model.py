#! python 3
# r: compas, tessagon
# venv: himass1

import os
import compas
from compas.colors import Color
from compas.geometry import Point, Line
from compas_dem.templates import ArchTemplate
from compas_dem.models import BlockModel
from compas.scene import Scene


# =============================================================================
# Create Arch
# =============================================================================
rise = 2
span = 5
thickness = 0.3
depth = 0.3
n = 20
arch = BlockModel.from_template(ArchTemplate(rise,span,thickness,depth,n))

# =============================================================================
# Save Blockmodel
# =============================================================================
HERE = os.path.dirname(__file__)
FILE_O = os.path.join(HERE, 'arch_00.json')
compas.json_dump(arch, FILE_O)

# =============================================================================
# View in Rhino
# =============================================================================
scene = Scene()
scene.clear_context()
import rhinoscriptsyntax as rs
for block in arch.blocks():
    scene.add(block._geometry)
    rs.AddTextDot(block.graphnode,block._geometry.centroid())
scene.draw()