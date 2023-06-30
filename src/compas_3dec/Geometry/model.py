from __future__ import print_function
from __future__ import absolute_import
from __future__ import division

import os
import compas
import compas_rhino
from compas_rhino.utilities import select_meshes
from compas_rhino.geometry import RhinoMesh
from compas.datastructures import Graph
from compas_assembly.datastructures import Assembly
from compas_assembly.datastructures import Block


__all__ = ['from_rhino_select']


class Model(Assembly):
    """A data structure for managing the discrete geometry of masonry structures
    before and after the 3DEC analysis. This class is based on the Assembly data
    structure from ''compas_assembly.datastructures.Assembly'', and it adds
    attributes and methods useful for the assessment and design of unreinforced
    masonry structures.

    Parameters
    ----------
    name : _type_
        _description_
    """

    def __init__(self, name=None, **kwargs):
        super(Assembly, self).__init__()

        self._blocks = {}
        self.attributes = {"name": name or "Assembly"}
        self.attributes.update(kwargs)
        self.graph = Graph()
        self.graph.update_default_node_attributes(
            {
                "block":            None,
                "3dec_region":      None,
                "3dec_group":       None,
                "mass":             None,
                "weight":           None,
                "is_support":       False,
                "section":          None,
                "mesh_size":        None,
                "3dec_unbal_force": None,
                "3dec_moment":      None,
                "displacement":     [0, 0, 0, 0, 0, 0],
            }
        )
        self.graph.update_default_edge_attributes(
            {
                "interfaces": None,
            }
        )

    @classmethod
    def from_rhino_select(cls,path):
        """Construct a compas_3dec model by manually selecting Rhino meshes. The user
        should select at least one mesh as a support and one mesh as a
        block. `

        Parameters
        ----------
        guids : list[str]
            A list of GUIDs identifying the meshes representing the blocks of the assembly.

        Returns
        -------
        :class:`Assembly`

        Examples
        --------
        >>> assembly = Assembly()
        >>> guids = compas_rhino.select_meshes()
        >>> assembly.add_blocks_from_rhinomeshes(guids)

        """
        assembly = cls()

        supports = select_meshes('Select support meshes')
        support_meshes = []
        for guid in supports:
            support_mesh = []
            submeshes = compas_rhino.rs.ExplodeMeshes(guid)
            for submesh in submeshes:
                mesh = RhinoMesh.from_guid(submesh)
                compas_mesh = mesh.to_compas()
                support_mesh.append(compas_mesh)
                assembly.add_block(compas_mesh)
                for node in assembly.nodes():
                    assembly.graph.node_attribute(node, "is_support",True)
                    assembly.graph.node_attribute(node, "3dec_group",'Supports')
            support_meshes.append(support_mesh)
            compas_rhino.rs.UnselectAllObjects()
        FILE = os.path.join(path, 'supports.json')
        compas.json_dump(support_meshes, FILE, True)

        while True:
            out = compas_rhino.rs.GetString("Input Block's group")
            if not out:
                break

            blocks = select_meshes('Select meshes belonging to {}'.format(out))
            block_meshes = []
            for guid in blocks:
                block_mesh = []
                submeshes = compas_rhino.rs.ExplodeMeshes(guid)
                for submesh in submeshes:
                    mesh = RhinoMesh.from_guid(submesh)
                    compas_mesh = mesh.to_compas()
                    block_mesh.append(compas_mesh)
                    assembly.add_block(compas_mesh)
                    for node in assembly.nodes():
                        if assembly.graph.node_attribute(node, "is_support") == False:
                            assembly.graph.node_attribute(node, "3dec_group",str(out))
                block_meshes.append(block_mesh)
                compas_rhino.rs.UnselectAllObjects()
            FILE = os.path.join(path, '{}.json'.format(out))
            compas.json_dump(block_meshes, FILE, True)

        return assembly
