
import os
import compas
from compas_3dec.datastructures import Assembly_3dec


HERE = os.path.dirname(__file__)
FILE = os.path.join(HERE, 'model2.json')

model = Assembly_3dec.from_rhino_select(HERE)

compas.json_dump(model, FILE, True)
