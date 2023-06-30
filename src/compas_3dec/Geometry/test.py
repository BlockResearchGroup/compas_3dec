from compas_3dec.Geometry import Model
import os
import compas


HERE = os.path.dirname(__file__)
FILE = os.path.join(HERE, 'model.json')

model = Model.from_rhino_select(HERE)

compas.json_dump(model, FILE, True)
