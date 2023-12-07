import os
import compas
from compas_3dec.analysis import Analysis
from compas_3dec.datastructures import Assembly_3dec
from compas_3dec.mechanical import MechParam

path = os.path.dirname(__file__)
# model = Assembly_3dec.from_rhino_select(path)
mechparam = MechParam.standard_material()


FILE = os.path.join(path, "model.json")
assembly_3dec = compas.json_load(FILE)

# analysis = Analysis.selfweight(model, mechparam, path)

Analysis.geometry_dat(assembly_3dec, path)
Analysis.main_dat(mechparam, path, "Analysis_test")
