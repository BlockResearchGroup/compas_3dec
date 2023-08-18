# from compas_assembly.datastructures import Assembly
from compas_3dec.Geometry import Model

import os
import compas
import compas_rhino
import os
import compas
import compas_rhino
from compas_rhino.utilities import select_meshes
from compas_rhino.geometry import RhinoMesh
from compas.datastructures import Graph
from compas_assembly.datastructures import Assembly
from compas_assembly.datastructures import Block

HERE = os.path.dirname(__file__)
FILE = os.path.join(HERE, 'mod.json')

# model = compas.json_load(FILE)


# for node in model.nodes():
#     centroid = model.node_block(node).centroid()
#     compas_rhino.rs.AddTextDot(node,centroid)

# for node in model.nodes():
#     if model.graph.node_attribute(node, "is_support") == True:
#         support = model.node_block(node)
#         group = model.graph.node_attribute(node, "3dec_group")

#         print (group)


    # print (centroid)

def from_rhino_select(Model,path):
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
        assembly = Model()

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
                assembly.add_block(compas_mesh)
                for node in assembly.nodes():
                    if assembly.graph.node_attribute(node, "is_support") == False:
                        assembly.graph.node_attribute(node, "3dec_group",str(out))
            block_meshes.append(block_mesh)
            compas_rhino.rs.UnselectAllObjects()
        FILE = os.path.join(path, '{}.json'.format(out))
        compas.json_dump(block_meshes, FILE, True)

        return assembly

mod = from_rhino_select(Model,HERE)
compas.json_dump(mod,FILE,True)
