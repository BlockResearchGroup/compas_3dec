import os
import compas
from compas_3dec.analysis import Analysis
from compas_3dec.datastructures import Assembly_3dec

HERE = os.path.dirname(__file__)
FILE = os.path.join(HERE, 'model2.json')
model3 = compas.json_load(FILE)

# assembly_3dec = Assembly_3dec.from_rhino_select(HERE)

assembly = Assembly_3dec.from_assembly(model3,'Ale')
Analysis.geometry_dat(assembly,HERE)





