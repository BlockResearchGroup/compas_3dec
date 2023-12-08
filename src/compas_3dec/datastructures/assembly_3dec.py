from __future__ import print_function
from __future__ import absolute_import
from __future__ import division

import os
from compas.datastructures import Graph
from compas_assembly.datastructures import Assembly, Block
from compas.datastructures import mesh_weld
from compas.datastructures import mesh_explode
from compas_3dec.utilities import (
    find_duplicate_dict,
    overwrite_file,
    threedec7_support_description,
    threedec7_block_description
)

__all__ = [
    "from_rhino_select",
    "from_assembly",
    "to_3dec",
]

class Assembly_3dec(Assembly):
    """A data structure for managing the analysis of discrete geometries using
    the DEM software 3DEC by Itasca. This class is an extension of the
    ''compas_assembly.datastructures.Assembly'' and is tailored to facilitate
    geometry translations specifically for 3DEC analysis. It incorporates
    additional attributes and methods designed for the assessment and design
    of unreinforced masonry structures.

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
        # self.graph.update_default_node_attributes(
        #     {
        #         "block": None,
        #         "mass": None,
        #         "weight": None,
        #         "density": None,
        #         "is_support": False,
        #         "section": None,
        #         "mesh_size": None,
        #         "3dec_region": None,
        #         "3dec_block_ID": None,
        #         "3dec_group": None,
        #         "3dec_unbal_force": None,
        #         "3dec_velocity": None,
        #         "3dec_moment": None,
        #         "3dec_step": None,
        #         "displacement": [0, 0, 0, 0, 0, 0],
        #     }
        # )
        self.graph.update_default_edge_attributes(
            {
                "interfaces": None,
            }
        )

    @classmethod
    def from_rhino_select(cls):
        """Construct an assembly by manually selecting Rhino concave or
        convex meshes. At least one mesh as a support and one mesh as a
        block should be selected. The meshes in Rhino should be closed
        and with welded vertices. If some blocks are concave, each of
        them should be subdivided into convex meshes and joined, forming
        a compound.

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
        supports = select_meshes("Select support meshes")
        support_count = 0
        for guid in supports:
            s_comp_group = "Support_comp_" + str(support_count)
            mesh = RhinoMesh.from_guid(guid)
            compas_mesh = mesh.to_compas()
            submeshes = mesh_explode(compas_mesh)
            for submesh in submeshes:
                compas_mesh = mesh_weld(submesh)
                s_node = assembly_3dec.add_block(compas_mesh)
                assembly_3dec.graph.node_attribute(s_node, "is_support", True)
                assembly_3dec.graph.node_attribute(s_node, "3dec_group", "Supports")
                assembly_3dec.graph.node_attribute(s_node, "comp_group", str(s_comp_group))
            support_count += 1
        compas_rhino.rs.UnselectAllObjects()

        blocks = select_meshes("Select block meshes")
        block_count = 0
        for guid in blocks:
            b_comp_group = "Block_comp_" + str(block_count)
            mesh = RhinoMesh.from_guid(guid)
            compas_mesh = mesh.to_compas()
            submeshes = mesh_explode(compas_mesh)
            for submesh in submeshes:
                compas_mesh = mesh_weld(submesh)
                b_node = assembly_3dec.add_block(compas_mesh)
                assembly_3dec.graph.node_attribute(b_node, "3dec_group", "Blocks")
                assembly_3dec.graph.node_attribute(b_node, "comp_group", str(b_comp_group))
            block_count += 1
        compas_rhino.rs.UnselectAllObjects()
        return assembly_3dec

    @classmethod
    def from_assembly(cls,assembly):
        """Construct a compas_3dec model starting from an assembly of 3D compas meshes with
        supports already defined. In the case of complex concave blocks, each block needs to
        be first subdivided in smaller convex components. Each component of the same compound
        has to be named with the same compound name, which must be added as a value of the
        attribute "comp_group".
        For example, in the following case, the name 'Block_comp_0' was assigned to the attribute
        "comp_group" of node '2' in the assembly:
        assembly.graph.node_attribute(2, "comp_group", 'Block_comp_0')


        Parameters
        ----------
        Assembly:       class:`compas_assembly.datastructures.Assembly`

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
                if assembly.graph.node_attribute(node_support, "comp_group"):
                    comp = assembly.graph.node_attribute(node_support, "comp_group")
                    assembly_3dec.graph.node_attribute(node_support, "comp_group",str(comp))
            else:
                block = assembly.node_block(node)
                node_block = assembly_3dec.add_block(block)
                assembly_3dec.graph.node_attribute(node_block, "3dec_group", "Blocks")
                if assembly.graph.node_attribute(node_block, "comp_group"):
                    comp = assembly.graph.node_attribute(node_block, "comp_group")
                    assembly_3dec.graph.node_attribute(node_block, "comp_group",str(comp))
        return assembly_3dec

    @classmethod
    def to_3dec(cls,assembly_3dec,path):
        """Create the .dat files of the Blocks and Supports geometry for 3DEC from an
        Assembly_3DEC object. This function recognises compounds of joined blocks (e.g.
        a group of 3D convex meshes joined together forming a concave shape) enabling
        the creation of Master/Slave compounds in 3DEC.

        Parameters
        ----------
        assembly_3dec : _type_
            _description_
        path : _type_
            _description_

        Returns
        -------
        files:  block_geometry.dat and support_geometry.dat
        """
        string_s = ";__create geometry__" + "\n"
        string_b = ";__create geometry__" + "\n"
        s_comp_dict = {}
        b_comp_dict = {}
        for node in assembly_3dec.nodes():
            if assembly_3dec.graph.node_attribute(node, "is_support") == True:
                support = assembly_3dec.node_block(node)
                name = "support_geometry.dat"
                geometry_path_s = os.path.join(path, name)
                node_i = int(node)
                if assembly_3dec.graph.node_attribute(node_i, "comp_group"):
                    s_comp_group = assembly_3dec.graph.node_attribute(node_i, "comp_group")
                    s_comp_dict[node_i] = s_comp_group
                string_s += threedec7_support_description(support, node_i, precision=10)
            else:
                block = assembly_3dec.node_block(node)
                group = assembly_3dec.graph.node_attribute(node, "3dec_group")
                name = "block_geometry.dat"
                geometry_path_b = os.path.join(path, name)
                node_j = int(node)
                if assembly_3dec.graph.node_attribute(node_j, "comp_group"):
                    b_comp_group = assembly_3dec.graph.node_attribute(node_j, "comp_group")
                    b_comp_dict[node_j] = b_comp_group
                string_b += threedec7_block_description(block, group, node_j, precision=10)
        joined_block_names = find_duplicate_dict(b_comp_dict)
        for j in joined_block_names:
            string_b += ("block join range region {}".format(j)) + "\n"
        joined_block_s_names = find_duplicate_dict(s_comp_dict)
        for js in joined_block_s_names:
            string_s += ("block join range region {}".format(js)) + "\n"
        overwrite_file(geometry_path_s, string_s)
        overwrite_file(geometry_path_b, string_b)
        return
