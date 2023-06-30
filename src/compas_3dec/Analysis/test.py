
import os
from compas_3dec.Analysis import Analysis
from compas_3dec.Geometry import Model
from compas_3dec.Parameters import MechParam

path = os.path.dirname(__file__)
model = Model.from_rhino_select(path)
mechparam = MechParam.standard_material()

analysis = Analysis.selfweight(model, mechparam, path)
