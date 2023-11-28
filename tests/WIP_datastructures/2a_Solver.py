import os
from compas_3dec.solver import Solver
from compas_3dec.utilities import solve_ratio

# ==============================================================================
# import
# ==============================================================================
HERE = os.path.dirname(__file__)

# ==============================================================================
# Solver
# ==============================================================================
s = Solver()
s.run(HERE, ['main.py'])

# FILE = os.path.join(HERE, 'grav_state.txt')
# solve_ratio(FILE)
