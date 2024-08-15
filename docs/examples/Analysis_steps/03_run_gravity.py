import os
import time
start = time.time()
import compas

# =============================================================================
# Input
# =============================================================================
HERE = os.path.dirname(__file__)
FILE = os.path.join(HERE, 'problem.json')
problem = compas.json_load(FILE)

# =============================================================================
# create gravity.dat
# =============================================================================
gravity_file = problem.gravity()

# =============================================================================
# run 3DEC
# =============================================================================
problem.run([gravity_file])

end = time.time()
print("input_geometry", end - start)
