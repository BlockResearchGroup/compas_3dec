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
# read results
# =============================================================================
init_dict = problem.from_3dec_blocks("init_state.txt")
mapping_dict = problem.mapping(init_dict)
grav_dict = problem.from_3dec_blocks("grav_state.txt")
problem.solve_ratio_check("grav_state.txt")
problem.update_blocks(grav_dict,mapping_dict)
problem.from_3dec_contacts("contact_grav.txt")

# =============================================================================
# save to json
# =============================================================================
HERE = os.path.dirname(__file__)
FILE = os.path.join(HERE, 'problem.json')
compas.json_dump(problem, FILE)

end = time.time()
print("input_geometry", end - start)
