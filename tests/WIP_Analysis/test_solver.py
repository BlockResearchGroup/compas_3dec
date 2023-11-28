import os
from compas_3dec.solver import Solver

HERE = os.path.dirname(__file__)
# FILE = os.path.join(HERE, 'model.json')

s = Solver()
s.run(HERE, ['main.dat'])

# print ('done')
