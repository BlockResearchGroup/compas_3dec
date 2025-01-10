import time
start = time.time()
import os
import compas
from compas_3dec.datastructure.problem_3dec import Problem3dec

# =============================================================================
# Input problem_init
# =============================================================================
HERE = os.path.dirname(__file__)
FILE_I = os.path.join(HERE, 'problem_init.json')
problem: Problem3dec = compas.json_load(FILE_I)

# =============================================================================
# To 3DEC geometry
# =============================================================================
problem.to_geometry_3dec()

# =============================================================================
# create gravity.dat
# =============================================================================
gravity_file = problem.gravity()

# =============================================================================
# run 3DEC
# =============================================================================
problem.run([gravity_file])

# =============================================================================
# read results blocks and interactions
# =============================================================================
init_dict = problem.from_3dec_blocks("init_state.txt")
mapping_dict = problem.mapping(init_dict)
grav_dict = problem.from_3dec_blocks("grav_state.txt")
problem.solve_ratio_check("grav_state.txt")
problem.update_blocks(grav_dict,mapping_dict)
output_3dec_per_vertex = problem.from_3dec_contacts("contact_grav.txt")

# =============================================================================
# save problem gravity
# =============================================================================
FILE_O = os.path.join(HERE, 'problem_gravity.json')
compas.json_dump(problem, FILE_O)
end = time.time()
print('analysis_3dec time', end - start, 's')