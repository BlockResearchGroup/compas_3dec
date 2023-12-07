import os
from compas_3dec.datastructures import Assembly_3dec
from compas_3dec.analysis import Analysis
from compas_3dec.mechanical import MechParam

# ==============================================================================
# Folder
# ==============================================================================
HERE = os.path.dirname(__file__)

# ==============================================================================
# Create assembly
# ==============================================================================
assembly = Assembly_3dec.from_rhino_select_convex()

# ==============================================================================
# Mechanical parameters
# ==============================================================================
parameters = MechParam.standard_material()

# ==============================================================================
# Create dat files for 3DEC
# ==============================================================================
geometry_dat = Analysis.geometry_dat_convex(assembly,HERE)
main_dat = Analysis.main_dat_txt(parameters,HERE,'test')



