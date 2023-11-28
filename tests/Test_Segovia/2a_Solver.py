import os
from compas_3dec.solver import Solver
from compas_3dec.utilities import solve_ratio

# ==============================================================================
# import
# ==============================================================================
HERE = os.path.dirname(__file__)
FILE_1 = os.path.join(HERE, 'init_state.txt')
FILE_2 = os.path.join(HERE, 'grav_state.txt')
FILE_3 = os.path.join(HERE, 'contact_init.txt')
FILE_4 = os.path.join(HERE, 'contact_grav.txt')
FILE_5 = os.path.join(HERE, 'assembly_3dec.json')
FILE_6 = os.path.join(HERE, 'blocks.json')
FILE_7 = os.path.join(HERE, 'supports.json')
FILE_8 = os.path.join(HERE, 'Analysis_test_init.sav')
FILE_9 = os.path.join(HERE, 'Analysis_test_grav.sav')

try:
    if FILE_1:
        os.remove(FILE_1)
    if FILE_2:
        os.remove(FILE_2)
    if FILE_3:
        os.remove(FILE_3)
    if FILE_4:
        os.remove(FILE_4)
    if FILE_5:
        os.remove(FILE_5)
    if FILE_6:
        os.remove(FILE_6)
    if FILE_7:
        os.remove(FILE_7)
    if FILE_8:
        os.remove(FILE_8)
except Exception:
    pass


# ==============================================================================
# Solver
# ==============================================================================
s = Solver()
s.run(HERE, ['main.dat'])

FILE = os.path.join(HERE, 'grav_state.txt')
solve_ratio(FILE)
