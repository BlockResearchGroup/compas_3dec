import os
from compas.datastructures import Graph
from compas_assembly.datastructures import Assembly, Block
from compas.datastructures import mesh_weld
from compas.datastructures import mesh_explode
from compas_3dec.utilities import (
    blocks_output,
    save_blocks_output,
    save_analysis,
    restore_analysis,
    contacts_output,
    save_contacts_output,
    gravity_equilibrium,
    find_duplicate_dict,
    overwrite_file,
    threedec7_support_description,
    threedec7_block_description
from compas_3dec.datastructures import Assembly_3dec

def from_rhino_select_convex(cls):
    """Construct an Assembly_3DEC by manually selecting Rhino convex 3D meshes.
    At least one mesh as a support and one mesh as a block should be
    selected. The meshes in Rhino should be closed.

    Returns
    -------
    :class:`Assembly_3dec`
        The assembly datastructure with Supports and Blocks defined.
    """

    import compas_rhino
    from compas_rhino.geometry import RhinoMesh
    from compas_rhino.utilities import select_meshes

    assembly_3dec = cls()
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




def from_assembly(cls, assembly):
    """Construct a compas_3dec model starting from an assembly of 3D compas meshes with
    supports already defined. In the case of complex concave blocks, each block needs to
        be first subdivided in smaller convex components and then joined using the command
        "compas.datastructures.meshes_join".

    Parameters
    ----------
    Assembly:       class

    Returns
    -------
    :class:`Assembly_3dec`

    Examples
    --------
    """
    # Notes: add .json files generation if needed for post processing
    assembly_3dec = cls()
    for node in assembly.nodes():
        if assembly.graph.node_attribute(node, "is_support"):
            support = assembly.node_block(node)
            node_support = assembly_3dec.add_block(support)
            assembly_3dec.graph.node_attribute(node_support, "is_support", True)
            assembly_3dec.graph.node_attribute(node_support, "3dec_group", "Supports")
        else:
            block = assembly.node_block(node)
            node_block = assembly_3dec.add_block(block)
            assembly_3dec.graph.node_attribute(node_block, "3dec_group", "Blocks")
    return assembly_3dec
