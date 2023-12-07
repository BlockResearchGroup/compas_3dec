import os
import compas
from compas_3dec.datastructures import Assembly_3dec
from compas_3dec.analysis import Analysis
from compas_3dec.mechanical import MechParam
from compas.datastructures import mesh_weld
from compas_assembly.datastructures import Assembly

HERE = os.path.dirname(__file__)
FILE = os.path.join(HERE, "Assembly_test.json")


def from_rhino_select_convex(path):
    import compas_rhino
    from compas_rhino.geometry import RhinoMesh
    from compas_rhino.utilities import select_meshes

    assembly_3dec = Assembly()
    supports = select_meshes("Select support meshes")
    for guid in supports:
        mesh = RhinoMesh.from_guid(guid)
        compas_mesh = mesh.to_compas()
        compas_mesh = mesh_weld(compas_mesh)
        s_node = assembly_3dec.add_block(compas_mesh)
        assembly_3dec.graph.node_attribute(s_node, "is_support", True)
        assembly_3dec.graph.node_attribute(s_node, "3dec_group", "Supports")
    compas_rhino.rs.UnselectAllObjects()

    blocks = select_meshes("Select block meshes")
    for guid in blocks:
        mesh = RhinoMesh.from_guid(guid)
        compas_mesh = mesh.to_compas()
        compas_mesh = mesh_weld(compas_mesh)
        b_node = assembly_3dec.add_block(compas_mesh)
        assembly_3dec.graph.node_attribute(b_node, "3dec_group", "Blocks")
    compas_rhino.rs.UnselectAllObjects()
    return assembly_3dec


assembly_3dec = from_rhino_select_convex(HERE)
mechparam = MechParam.standard_material()
Analysis.geometry_dat(assembly_3dec, HERE)


compas.json_dump(assembly_3dec, FILE, True)
