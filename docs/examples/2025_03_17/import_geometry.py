
import os
from compas_3dec.wip.input import Block
from compas_viewer import Viewer
from compas.colors import Color
from compas.scene import Scene
from compas.datastructures import Mesh
# from compas_model.elements import BlockElement
from compas_3dec.data.arch import Arch

from compas_model.models import Model 

from compas_masonry.models import BlockModel
from compas_masonry.elements import BlockElement



# =============================================================================
# Input
# =============================================================================
arch = Arch(rise=5, span=10, thickness=0.5, depth=0.5, n=20)
meshes = arch.blocks()



