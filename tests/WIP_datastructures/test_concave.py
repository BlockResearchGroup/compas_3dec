import os
import compas
from compas_3dec.datastructures import Assembly_3dec
from compas_3dec.analysis import Analysis
from compas_3dec.mechanical import MechParam


HERE = os.path.dirname(__file__)
FILE = os.path.join(HERE, 'Assembly_test.json')
# assembly = compas.json_load(FILE)


assembly_3dec = Assembly_3dec.from_rhino_select_concave_test()
compas.json_dump(assembly_3dec, FILE, True)
# assembly_3dec = Assembly_3dec.from_assembly(assembly, 'blocks')
mechparam = MechParam.standard_material()
Analysis.geometry_dat(assembly_3dec,HERE)

