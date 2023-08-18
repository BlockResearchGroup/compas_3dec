
import os
import compas
from compas_3dec.Analysis import Analysis
from compas_3dec.Geometry import Model
from compas_3dec.Parameters import MechParam

path = os.path.dirname(__file__)
model = Model.from_rhino_select(path)
mechparam = MechParam.standard_material()



FILE = os.path.join(path, 'model.json')
compas.json_dump(model, FILE, True)

analysis = Analysis.selfweight(model, mechparam, path)
