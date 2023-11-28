
import os
import compas
from compas_assembly.datastructures import Assembly
from compas_assembly.geometry import Arch
from compas_3dec.mechanical import MechParam
from compas_3dec.analysis import Analysis
from compas_3dec.datastructures import Assembly_3dec



HERE = os.path.dirname(__file__)
FILE_Ar = os.path.join(HERE, 'arch_assembly.json')


arch = Arch(rise=5, span=10, thickness=0.5, depth=0.5, n=20)
assembly = Assembly.from_template(arch)
assembly.graph.node_attribute(0, "is_support", True)
assembly.graph.node_attribute(19, "is_support", True)

compas.json_dump(assembly,FILE_Ar,HERE)


assembly_3dec = Assembly_3dec.from_assembly(assembly, 'blocks')
mechparam = MechParam.standard_material()

Analysis.geometry_assembly_dat(assembly_3dec, HERE)
