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
s.run(HERE, ["displacement.dat"])

FILE = os.path.join(HERE, "step_01_equ__x_0.0mm_y_0.0mm_z_0.0mm.txt")
solve_ratio(FILE)
