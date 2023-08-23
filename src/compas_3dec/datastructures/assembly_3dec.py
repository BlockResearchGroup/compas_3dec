from __future__ import print_function
from __future__ import absolute_import
from __future__ import division

import os
import compas
from compas.datastructures import Graph
from compas_assembly.datastructures import Assembly, Block
from compas_3dec.utilities import threedec7_support_description,threedec7_block_description,overwrite_file

__all__ = ['from_rhino_select', 'from_assembly','geometry_dat']

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
                "volume":           None,
                "is_support":       False,
                "section":          None,
                "mesh_size":        None,
                "3dec_region":      None,
                "3dec_block_ID":    None,
                "3dec_group":       None,
                "3dec_unbal_force": None,
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
    def from_rhino_select(cls, path):
        """Construct a compas_3dec model by manually selecting Rhino meshes.
        At least one mesh as a support and one mesh as a block should be
        selected.`

        Parameters
        ----------
        guids : list[str]
            A list of GUIDs identifying the meshes representing the blocks of the assembly.

        Returns
        -------
        :class:`Assembly_3dec`

        Examples
        --------
        """

        # Notes: delete .json files generation if not anymore needed for post processing

        import compas_rhino
        from compas_rhino.geometry import RhinoMesh
        from compas_rhino.utilities import select_meshes

        assembly_3dec = cls()
        supports = select_meshes('Select support meshes')
        support_meshes = []
        for guid in supports:
            support_mesh = []
            submeshes = compas_rhino.rs.ExplodeMeshes(guid)
            for submesh in submeshes:
                mesh = RhinoMesh.from_guid(submesh)
                compas_mesh = mesh.to_compas()
                support_mesh.append(compas_mesh)
                assembly_3dec.add_block(compas_mesh)
                for node in assembly_3dec.nodes():
                    assembly_3dec.graph.node_attribute(node, "is_support", True)
                    assembly_3dec.graph.node_attribute(node, "3dec_group", 'Supports')
            support_meshes.append(support_mesh)
            compas_rhino.rs.UnselectAllObjects()
        FILE = os.path.join(path, 'supports.json')
        compas.json_dump(support_meshes, FILE, True)

        # pro function: multiple groups
        # while True:
        out = compas_rhino.rs.GetString("Input Block's group")
        # if not out:
        #     break

        blocks = select_meshes('Select meshes belonging to {}'.format(out))
        block_meshes = []
        for guid in blocks:
            block_mesh = []
            submeshes = compas_rhino.rs.ExplodeMeshes(guid)
            for submesh in submeshes:
                mesh = RhinoMesh.from_guid(submesh)
                compas_mesh = mesh.to_compas()
                block_mesh.append(compas_mesh)
                assembly_3dec.add_block(compas_mesh)
                for node in assembly_3dec.nodes():
                    if assembly_3dec.graph.node_attribute(node, "is_support") == False:
                        assembly_3dec.graph.node_attribute(node, "3dec_group", str(out))
            block_meshes.append(block_mesh)
            compas_rhino.rs.UnselectAllObjects()
        FILE = os.path.join(path, '{}.json'.format(out))
        FILE_a = os.path.join(path, 'assembly_3dec.json')
        compas.json_dump(block_meshes, FILE, True)
        compas.json_dump(assembly_3dec,FILE_a, True)
        return assembly_3dec

    @classmethod
    def from_assembly(cls, assembly, group):
        """Construct a compas_3dec model starting from an assembly of 3D compas meshes with
        supports already defined.

        Parameters
        ----------
        Assembly:       class
        group's name:   str

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
                assembly_3dec.graph.node_attribute(node_block, "3dec_group", group)

        return assembly_3dec


    @classmethod
    def geometry_dat(cls, path):
        assembly_3dec = cls()

        string_s = ';__create geometry__' + '\n'
        string_b = ';__create geometry__' + '\n'
        geometry_path_s = os.path.join(path, 'support_geometry.dat')
        geometry_path_b = os.path.join(path, 'block_geometry.dat')
        for node in assembly_3dec.nodes():
            print(node)
            if assembly_3dec.graph.node_attribute(node, "is_support") == True:
                support = assembly_3dec.node_block(node)
                string_s += threedec7_support_description(support,node, precision=10)
            else:
                block = assembly_3dec.node_block(node)
                group = assembly_3dec.node_attribute(node, "3dec_group")
                string_b += threedec7_block_description(
                block, group,node, precision=10)
        overwrite_file(geometry_path_s, string_s)
        overwrite_file(geometry_path_b, string_b)
        return
