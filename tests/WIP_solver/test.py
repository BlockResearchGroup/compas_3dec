import os
from compas_3dec.Solver import Solver

HERE = os.path.dirname(__file__)
# FILE = os.path.join(HERE, 'model.json')

s = Solver()
s.run(HERE, ['test_itasca.py'])

