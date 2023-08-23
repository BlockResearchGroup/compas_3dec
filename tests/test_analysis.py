
import os
import compas
import sys
from compas_3dec.datastructures import Assembly_3dec
from compas_3dec.analysis import Analysis
from compas_3dec.mechanical import MechParam
from compas_3dec.solver import Solver


# ==============================================================================
# import
# ==============================================================================
HERE = os.path.dirname(__file__)
FILE = os.path.join(HERE, 'assembly_3dec.json')
assembly = compas.json_load(FILE)

# ==============================================================================
# Get geometry
# ==============================================================================
# assembly_3dec = Assembly_3dec.from_rhino_select(path)
assembly_3dec = Assembly_3dec.from_assembly(assembly,'Blocks')

# ==============================================================================
# Get/set mechanical parameters
# ==============================================================================
mechparam = MechParam.standard_material()

# ==============================================================================
# Analysis
# ==============================================================================
Analysis.geometry_dat(assembly_3dec,HERE)
Analysis.main_dat(mechparam,HERE,'Analysis_test')


# ==============================================================================
# Solver
# ==============================================================================
s = Solver()
s.run(HERE, ['main.dat'])


# ==============================================================================
# Results
# ==============================================================================

# ==============================================================================
# Visualisation
# ==============================================================================
