
import os
import compas
from compas_3dec.analysis import Analysis
from compas_3dec.datastructures import Assembly_3dec
from compas_3dec.mechanical import MechParam

path = os.path.dirname(__file__)
model = Assembly_3dec.from_rhino_select(path)
mechparam = MechParam.standard_material()



FILE = os.path.join(path, 'model.json')
compas.json_dump(model, FILE, True)

analysis = Analysis.selfweight(model, mechparam, path)
