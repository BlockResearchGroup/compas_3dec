from __future__ import print_function
from __future__ import absolute_import
from __future__ import division

from compas.datastructures import Graph
from compas_assembly.datastructures import Assembly, Block
from compas.datastructures import mesh_weld
from compas.datastructures import mesh_explode


__all__ = ['from_rhino_select_convex',
           'from_rhino_select_concave',
           'from_assembly',
           ]

class Assembly_3dec(Assembly):
    """A data structure for managing the analysis of discrete geometries
    using the DEM software 3DEC by Itasca. This class is based on the Assembly data
    structure from ''compas_assembly.datastructures.Assembly'', and it adds
    attributes and methods useful for the assessment and design of unreinforced
    masonry structures.

    Parameters
    ----------
    name : str, optional
        The name of the assembly.

    Attributes
    ----------
    attributes : dict[str, Any]
        General attributes of the data structure that will be included in the data dict and serialization.
    graph : :class:`compas.datastructures.Graph`
        The graph that is used under the hood to store the parts and their connections.

    Examples
    --------
    """

    def __init__(self, name=None, **kwargs):
        super(Assembly, self).__init__()

        self._blocks = {}
        self.attributes = {"name": name or "Assembly_3dec"}
        self.attributes.update(kwargs)
        self.graph = Graph()
        self.graph.update_default_node_attributes(
            {
                "block":            None,
                "mass":             None,
                "weight":           None,
                "density":          None,
                "is_support":       False,
                "section":          None,
                "mesh_size":        None,
                "3dec_region":      None,
                "3dec_block_ID":    None,
                "3dec_group":       None,
                "3dec_unbal_force": None,
                "3dec_velocity":    None,
                "3dec_moment":      None,
                "3dec_step":        None,
                "displacement":     [0, 0, 0, 0, 0, 0],
            }
        )
        self.graph.update_default_edge_attributes(
            {
                "interfaces": None,
            }
        )

    @classmethod
    def from_rhino_select_convex(cls):
        """Construct an assembly by manually selecting Rhino convex meshes.
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
        supports = select_meshes('Select support meshes')
        for guid in supports:
            mesh = RhinoMesh.from_guid(guid)
            compas_mesh = mesh.to_compas()
            compas_mesh = mesh_weld(compas_mesh)
            s_node = assembly_3dec.add_block(compas_mesh)
            assembly_3dec.graph.node_attribute(s_node, "is_support", True)
            assembly_3dec.graph.node_attribute(s_node, "3dec_group", 'Supports')
        compas_rhino.rs.UnselectAllObjects()

        blocks = select_meshes('Select block meshes')
        for guid in blocks:
            mesh = RhinoMesh.from_guid(guid)
            compas_mesh = mesh.to_compas()
            compas_mesh = mesh_weld(compas_mesh)
            b_node = assembly_3dec.add_block(compas_mesh)
            assembly_3dec.graph.node_attribute(b_node, "3dec_group", 'Blocks')
        compas_rhino.rs.UnselectAllObjects()
        return assembly_3dec

    @classmethod
    def from_rhino_select_concave(cls):
        """Construct an assembly by manually selecting Rhino concave or
        convex meshes. At least one mesh as a support and one mesh as a
        block should be selected. The meshes in Rhino should be closed
        and with welded vertices. The concave meshes should be made out
        of convex meshes joined together in Rhino.

        Returns
        -------
        :class:`Assembly_3dec`
            The assembly datastructure with Supports, Blocks and compound
            groups defined.
        """
        import compas_rhino
        from compas_rhino.geometry import RhinoMesh
        from compas_rhino.utilities import select_meshes

        assembly_3dec = cls()
        supports = select_meshes('Select support meshes')
        support_count = 0
        for guid in supports:
            s_comp_group = 'Support_comp_' + str(support_count)
            mesh = RhinoMesh.from_guid(guid)
            compas_mesh = mesh.to_compas()
            submeshes = mesh_explode(compas_mesh)
            for submesh in submeshes:
                compas_mesh = mesh_weld(submesh)
                s_node = assembly_3dec.add_block(compas_mesh)
                assembly_3dec.graph.node_attribute(s_node, "is_support", True)
                assembly_3dec.graph.node_attribute(s_node, "3dec_group", 'Supports')
                assembly_3dec.graph.node_attribute(s_node, "comp_group", str(s_comp_group))
            support_count += 1
        compas_rhino.rs.UnselectAllObjects()

        blocks = select_meshes('Select block meshes')
        block_count = 0
        for guid in blocks:
            b_comp_group = 'Block_comp_' + str(block_count)
            mesh = RhinoMesh.from_guid(guid)
            compas_mesh = mesh.to_compas()
            submeshes = mesh_explode(compas_mesh)
            for submesh in submeshes:
                compas_mesh = mesh_weld(submesh)
                b_node = assembly_3dec.add_block(compas_mesh)
                assembly_3dec.graph.node_attribute(b_node, "3dec_group", 'Blocks')
                assembly_3dec.graph.node_attribute(b_node, "comp_group", str(b_comp_group))
            block_count += 1
        compas_rhino.rs.UnselectAllObjects()
        return assembly_3dec

    @classmethod
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
                assembly_3dec.graph.node_attribute(node_support, "3dec_group", 'Supports')
            else:
                block = assembly.node_block(node)
                node_block = assembly_3dec.add_block(block)
                assembly_3dec.graph.node_attribute(node_block, "3dec_group", 'Blocks')
        return assembly_3dec
