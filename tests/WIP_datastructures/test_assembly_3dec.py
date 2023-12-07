import os
import compas
from compas_3dec.datastructures import Assembly_3dec


HERE = os.path.dirname(__file__)
FILE_I = os.path.join(HERE, "model.json")
FILE_O = os.path.join(HERE, "model3.json")

assembly = compas.json_load(FILE_I)

assem = Assembly_3dec.from_assembly(assembly, "Ale")

compas.json_dump(assem, FILE_O, True)
