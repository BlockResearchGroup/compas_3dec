import os
import inspect
from subprocess import call

from compas.files import OBJ
from compas.datastructures import Mesh
from compas.geometry import convex_hull_xy, Plane, Frame, Transformation, transform_points, Polygon

from compas_model.model import Model, GroupNode
from compas_model.elements import BlockElement, InterfaceElement

from compas_3dec.threedec_config import ThreedecConfig
from compas_3dec.interactions_3dec import Interaction3dec


class Model_3dec(Model):
    """Class representing a general model of hierarchically organised elements, with interactions.

    Attributes
    ----------
    elements : dict
        The elements of the model mapped by their guid.
    tree : :class:`ElementTree`
        A hierarchical structure of the elements in the model.
    graph : :class:`InteractionGraph`
        A graph containing the interactions between the elements of the model on its edges.

    Notes
    -----
    Model elements are contained in the tree hierarchy in tree nodes.
    Model elements are contained in the interaction graph in graph nodes.
    Every model element can appear only once in the tree, and once in the graph.
    This means every element can have only one hierarchical parent.
    Every element can have many interactions with other elements.
    The interactions and hierarchical relations are independent.

    """

    def __init__(
        self,
        name=None,
        executable_path='"C:\\Program Files\\Itasca\\3DEC700\\exe64\\3dec700_console.exe"',
        working_path=None,
    ):
        super(Model_3dec, self).__init__(name)
        self.threedec_config = ThreedecConfig()
        self.executable_path = executable_path
        self.working_path = working_path
        if not self.working_path:
            caller_frame = inspect.stack()[1]
            caller_filename = caller_frame.filename
            self.working_path = os.path.dirname(os.path.abspath(caller_filename))

    def init_element_features(self):
        for guid, element in self.elements.items():
            if isinstance(element, BlockElement):
                element.features = {
                    "unbalanced_force": [],
                    "velocity": [],
                    "density": None,
                    "mass": None,
                    "weight": None,
                    "position": {},
                    "transformation": [],
                    "material_properties": {
                        "density": None,
                        "friction_angle": None,
                        "young_modulus": None,
                        "poisson_ration": None,
                    },
                }
            elif isinstance(element, InterfaceElement):
                element.features = {
                    "type": None,
                    "frame": None,
                    "polygon": None,
                    "neighbours": [],
                    "vertices": {
                        "position": [],
                        "normal_force": None,
                        "shear_force": [],
                        "normal_stress": None,
                        "shear_stress": None,
                        "normal_displ": None,
                        "shear_displ": [],
                    },
                    "material_properties": {
                        "density": None,
                        "friction_angle": None,
                        "young_modulus": None,
                        "poisson_ration": None,
                    },
                }

    @classmethod
    def from_model(cls, model: Model):
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

        return

    @staticmethod
    def from_obj(path):
        obj = OBJ(path)
        obj.read()
        meshes = []
        for name in obj.objects:
            mesh = Mesh.from_vertices_and_faces(*obj.objects[name])
            mesh.name = name
            meshes.append(mesh)
        return meshes

    @staticmethod
    def model_from_obj(path_supports, path_blocks):
        caller_frame = inspect.stack()[1]
        caller_filename = caller_frame.filename
        meshes_supports = Model_3dec.from_obj(path_supports)
        meshes_blocks = Model_3dec.from_obj(path_blocks)
        model = Model_3dec(working_path=os.path.dirname(os.path.abspath(caller_filename)))
        group_supports = model.add_group("Supports")
        group_blocks = model.add_group("Blocks")
        for i in range(len(meshes_supports)):
            support = BlockElement(meshes_supports[i], is_support=True)
            model.add_element(support, group_supports)
            # group_supports.add(ElementNode(support))
        for i in range(len(meshes_blocks)):
            block = BlockElement(meshes_blocks[i], is_support=False)
            model.add_element(block, group_blocks)
            # group_blocks.add(ElementNode(block))
        return model

    def _overwrite_file(self, file_path, replace_string):
        # Overwrite existing file with replace_string

        if os.path.exists(file_path):
            if os.access(file_path, os.W_OK):
                f = open(file_path, "w+")
                f.write(replace_string)
                f.close()
            else:
                "File write access denied..."
        else:
            with open(file_path, "a+") as f:
                f.write(replace_string)

    def _threedec7_mesh_description(self, meshes, indices, group=None, precision=10):
        # create blocks
        # ***************************************************************************
        unit_scale = 1.0
        block_description = ""
        for i, mesh in enumerate(meshes):
            face_description = ""  # should not work with sub_blocks
            for face in mesh.faces():
                # add new face
                face_description += "face "
                # get the vertices of the face in order!
                vertices = list(mesh.face_vertices(face))
                # reverse vertex order for 3DEC
                vertices.reverse()
                # add the vertices of this face
                for vertex in vertices:
                    vertex_coordinates = mesh.vertex_coordinates(vertex)
                    face_description += "{0:.{3}f},{1:.{3}f},{2:.{3}f} ".format(
                        vertex_coordinates[0] / unit_scale,
                        vertex_coordinates[1] / unit_scale,
                        vertex_coordinates[2] / unit_scale,
                        precision,
                    )
            # add all faces of the block to the block description
            sub_block_description = (
                "block create group " + '"' + str(group) + '"' + " poly %s r=%i" % (face_description, indices[i])
            )
            block_description += sub_block_description + "\n"
        if len(meshes) > 1:
            str_indices = [str(num) for num in indices]
            block_description += "block join range region " + " ".join(str_indices) + "\n"
        return block_description

    def to_3dec_geometry(self):
        """Create the .dat files of the Blocks and Supports geometry for 3DEC from an
        Assembly_3DEC object. This function recognises compounds of joined blocks (e.g.
        a group of 3D convex meshes joined together forming a concave shape) enabling
        the creation of Master/Slave compounds in 3DEC.
        """
        # path = os.path.dirname(__file__)

        outputs = ""
        for node in self.tree.root.children:
            outputs += ";__create " + str(node.name) + "__" + "\n"
            for subnode in node:
                indices = []
                meshes = []
                if isinstance(subnode, GroupNode):
                    for subsubnode in subnode:
                        meshes.append(subsubnode.element.geometry)
                        indices.append(subsubnode.element.graph_node)
                else:
                    meshes.append(subnode.element.geometry)
                    indices.append(subnode.element.graph_node)
                outputs += self._threedec7_mesh_description(meshes, indices, node.name, precision=10)
        geometry_path = os.path.join(self.working_path, "geometry.dat")
        self._overwrite_file(geometry_path, outputs)

    def run(self, sequence=[]):
        args = ["cd", self.working_path, "&&", self.executable_path] + sequence
        call(" ".join(args), shell=True)

    def from_3dec_blocks(self, filename):
        blocks = {}
        with open(os.path.join(self.working_path, filename), "r") as fo:
            for line in fo:
                line = line.strip()
                if not line:
                    continue
                parts = line.split()
                if not len(parts):
                    continue
                if parts[0] == "block":
                    id = int(parts[1]) - 1
                    blocks[id] = {
                        "centroid": None,
                        "vertices": [],
                        "force": None,
                        "velocity": None,
                        "mass": None,
                        "region": None,
                        "moment": None,
                        "load": None,
                    }
                    continue
                if parts[0] == "centroid":
                    blocks[id]["centroid"] = [float(c) for c in parts[2].split(",")]
                    continue
                if parts[0] == "vertex":
                    xyz = [float(c) for c in parts[2][1:-1].split(",")]
                    blocks[id]["vertices"].append(xyz)
                    continue
                if parts[0] == "forces":
                    xyz = [float(c) for c in parts[2].split(",")]
                    blocks[id]["force"] = xyz
                    continue
                if parts[0] == "loads":
                    xyz = [float(c) for c in parts[2].split(",")]
                    blocks[id]["load"] = xyz
                    continue
                if parts[0] == "moment":
                    xyz = [float(c) for c in parts[2].split(",")]
                    blocks[id]["moment"] = xyz
                    continue
                if parts[0] == "velocity":
                    xyz = [float(c) for c in parts[2][1:-1].split(",")]
                    blocks[id]["velocity"] = xyz
                    continue
                if parts[0] == "region":
                    region = int(parts[1])
                    blocks[id]["region"] = region
                if parts[0] == "mass":
                    mass = float(parts[1])
                    blocks[id]["mass"] = mass
                    continue
        return blocks

    def solve_ratio_check(self, filename):
        with open(os.path.join(self.working_path, filename), "r") as fo:
            for line in fo:
                line = line.strip()
                if not line:
                    continue
                parts = line.split()
                if not len(parts):
                    continue
                if parts[0] == "solve":
                    solve_r = float(parts[3])
                    if solve_r <= 1.0000e-05:
                        print("Equilibrium reached")
                        print("solve ratio = " + str(solve_r))
                    else:
                        print("Equilibrium NOT reached")
                        print("solve ratio = " + str(solve_r))
        return

    def geometric_key(self, xyz, precision="3f", sanitize=True):
        """Convert XYZ coordinates to a string that can be used as a dict key.

        Parameters
        ----------
        xyz : list[float]
            The XYZ coordinates.
        precision : str, optional
            A formatting option that specifies the precision of the
            individual numbers in the string.
            Supported values are any float precision (e.g. ``'3f'``), or decimal integer (``'d'``).
            Default is ``None``, in which case the global precision setting will be used (:attr:`compas.PRECISION`).
        sanitize : bool, optional
            If True, minus signs ("-") will be removed from values that are equal to zero up to the given precision.

        Returns
        -------
        str
            The string representation of the given coordinates.

        See also
        --------
        geometric_key_xy

        Examples
        --------
        >>> from math import pi
        >>> geometric_key([pi, pi, pi])
        '3.142,3.142,3.142'

        """
        x, y, z = xyz
        if not precision:
            precision = "3f"
        if precision == "d":
            return "{0},{1},{2}".format(int(x), int(y), int(z))
        if sanitize:
            minzero = "-{0:.{1}}".format(0.0, precision)
            if "{0:.{1}}".format(x, precision) == minzero:
                x = 0.0
            if "{0:.{1}}".format(y, precision) == minzero:
                y = 0.0
            if "{0:.{1}}".format(z, precision) == minzero:
                z = 0.0
        return "{0:.{3}},{1:.{3}},{2:.{3}}".format(x, y, z, precision)

    def mapping(self, init_dict_3dec):
        block_map = {}
        for bkey, block in init_dict_3dec.items():
            region = block["region"]
            block_gkey_index = {}
            for index, xyz in enumerate(block["vertices"]):
                gkey = self.geometric_key(xyz)
                block_gkey_index[gkey] = index
            block_map[region] = {}
            for vkey in self.elementlist[region].geometry.vertices():
                xyz = self.elementlist[region].geometry.vertex_coordinates(vkey)
                gkey = self.geometric_key(xyz)
                v_index = block_gkey_index[gkey]
                block_map[region][vkey] = v_index
        return block_map

    def update_blocks(self, step_dict, mapping_dict):
        for index, block_element in enumerate(self.elementlist):
            for vkey, attr in block_element.geometry.vertices(True):
                vertex_3dec = mapping_dict[index][vkey]
                xyz = step_dict[index]["vertices"][vertex_3dec]
                attr["x"] = xyz[0]
                attr["y"] = xyz[1]
                attr["z"] = xyz[2]

    def _remove_duplicate_points(self, points, tolerance=0.00001):
        unique_points = []
        for point in points:
            is_unique = True
            for existing_point in unique_points:
                distance = sum((a - b) ** 2 for a, b in zip(point, existing_point)) ** 0.5
                if distance < tolerance:
                    is_unique = False
                    break
            if is_unique:
                unique_points.append(point)
        return unique_points

    def from_3dec_contacts(self, filename):
        contacts = {}
        with open(os.path.join(self.working_path, filename), "r") as fo:
            for line in fo:
                line = line.strip()
                if not line:
                    continue
                parts = line.split()
                if not len(parts):
                    continue
                if parts[0] == "contact" and (
                    (int(parts[3]) == 1)
                    or (int(parts[3]) == 3)
                    or (int(parts[3]) == 5)
                    or (int(parts[3]) == 4)
                    or (int(parts[3]) == 2)
                    or (int(parts[3]) == 0)
                ):
                    id = int(parts[2])
                    contacts[id] = {
                        "type": int(parts[3]),
                        "neighbours": [int(parts[4]), int(parts[5])],
                        "position": [float(c) for c in parts[6][1:-1].split(",")],
                        "normal": [float(c) for c in parts[7][1:-1].split(",")],
                        "subcontacts": {},
                    }
                    continue
                if parts[0] == "subcontact":
                    ids = int(parts[5])
                    contacts[id]["subcontacts"][ids] = {}
                    coordinates = [float(c) for c in parts[2][1:-1].split(",")]
                    normal_force = float(parts[3])
                    shear_force = [float(c) for c in parts[4][1:-1].split(",")]
                    normal_displ = float(parts[6])
                    shear_displ = [float(c) for c in parts[7][1:-1].split(",")]
                    normal_stress = float(parts[8])
                    shear_stress = float(parts[9])
                    area = float(parts[10])
                    contacts[id]["subcontacts"][ids]["coordinates"] = coordinates
                    contacts[id]["subcontacts"][ids]["normal_force"] = normal_force
                    contacts[id]["subcontacts"][ids]["shear_force"] = shear_force
                    contacts[id]["subcontacts"][ids]["normal_displ"] = normal_displ
                    contacts[id]["subcontacts"][ids]["shear_displ"] = shear_displ
                    contacts[id]["subcontacts"][ids]["normal_stress"] = normal_stress
                    contacts[id]["subcontacts"][ids]["shear_stress"] = shear_stress
                    contacts[id]["subcontacts"][ids]["area"] = area
                    continue

        for key, value in contacts.items():
            neighbours = value["neighbours"]
            # get list of subcontacts coordinates
            points = []
            for key, subcontact in value["subcontacts"].items():
                point = subcontact["coordinates"]
                print(point)
                points.append(point)

            # remove duplicates and create polygon
            self._remove_duplicate_points(points)
            normal = value["normal"]
            position = value["position"]
            plane = Plane(position, normal)
            frame = Frame.from_plane(plane)
            transformation = Transformation.from_frame_to_frame(frame, Frame.worldXY())
            points = transform_points(points, transformation)

            if len(points) > 3:
                points = convex_hull_xy(points)
            points = transform_points(points, transformation.inverse())
            polygon = Polygon(points)

            interaction = Interaction3dec(type=value["type"], normal=value["normal"], polygon=polygon)
            self.add_interaction(self.elementlist[neighbours[0]], self.elementlist[neighbours[1]], interaction)
        self.print()
        return contacts

        # for index, block_element in enumerate(self.elements_list):  # index and mesh from compas mesh
        #     block_map[index] = {
        #         'vertices'  : {},
        #     }
        #     for vkey in block_element.vertices():
        #         xyz = block_element.vertex_coordinates(vkey)
        #         gkey = self.geometric_key(xyz)
        #         v_index = block_gkey_index[region][gkey]
        #         block_map[index]['vertices'][vkey] = v_index
        # return block_map

        # # FILE1 = os.path.join(HERE, 'supports.json')
        # # FILE2 = os.path.join(HERE, 'blocks.json')
        # # data1 = compas.json_load(FILE1)
        # # data2 = compas.json_load(FILE2)
        # # mesh_list = data1 + data2
        # mesh_list = support + blocks
        # # FILE_O = os.path.join(HERE, 'Step.json')
        # # compas.json_dump(mesh_list, FILE_O)
        # block_gkey_key = {}
        # block_gkey_index = {}
        # mindex_key = {}
        # block_map = {}
        # bindex_mindex = {}
        # compas.PRECISION = '10f'
        # for bkey in init_dict_3dec:  # key of each block in the init_dict_3dec dict
        #     # print ('bk',bkey)
        #     block = init_dict_3dec[bkey]  # values of each block in the dict
        #     compas.PRECISION = str(centr_prec) + 'f'
        #     # print block['centroid']
        #     # creates gkey from centroid for each block
        #     gkey = geometric_key(block['centroid'])
        #     block_gkey_key[gkey] = bkey  # dict = {gkey(centroid):block_key)}
        #     block_gkey_index[bkey] = {}  # dict = {block_key: }
        #     compas.PRECISION = str(vert_prec) + 'f'
        #     # index and coordinates of each vertex for each block
        #     for index, xyz in enumerate(block['vertices']):
        #         gkey = geometric_key(xyz)  # creates gkey from vertices coordinates
        #         # dict = {block_key:{gkey_v_coord:vertex index}}
        #         block_gkey_index[bkey][gkey] = index
        # compas.PRECISION = '10f'
        # for index, mesh in enumerate(mesh_list):  # index and mesh from compas mesh
        #     # print ('ind',index)
        #     pts = [mesh.vertex_coordinates(v) for v in mesh.vertex]
        #     centroid = centroid_points(pts)
        #     compas.PRECISION = str(centr_prec) + 'f'
        #     # creates gkey from centroid for each compas mesh
        #     gkey = geometric_key(centroid)
        #     # print gkey
        #     bkey = block_gkey_key[gkey]  # map mesh_gkey with block_key
        #     mindex_key[index] = bkey  # dict = {mesh index:block_key)}
        # compas.PRECISION = '10f'

        # # creates gkey from centroid for each compas mesh
        # for mindex, mesh in enumerate(mesh_list):
        #     bkey = mindex_key[mindex]
        #     block = init_dict_3dec[bkey]
        #     block_map[mindex] = {
        #         'bkey': None,
        #         'vertices': {},
        #     }
        #     block_map[mindex]['bkey'] = bkey
        #     for vkey in mesh.vertices():
        #         xyz = mesh.vertex_coordinates(vkey)
        #         # print xyz
        #         compas.PRECISION = str(vert_prec) + 'f'
        #         gkey = geometric_key(xyz)
        #         # print gkey
        #         index = block_gkey_index[bkey][gkey]
        #         block_map[mindex]['vertices'][vkey] = index

        #     bindex_mindex[bkey] = {
        #         'mindex': None,
        #         'mesh': None,
        #         'map_verts': {},
        #         'type': None,
        #         'status': 'in',
        #         'weight': None,
        #         'unb_force': None,
        #         'unb_f_ratio': None,
        #         'layer': None,
        #         'region': init_dict_3dec[bkey]['region'],
        #         'centroid': init_dict_3dec[bkey]['centroid']
        #     }
        #     bindex_mindex[bkey]['mindex'] = mindex
        #     bindex_mindex[bkey]['mesh'] = mesh
        #     bindex_mindex[bkey]['map_verts'] = block_map[mindex]['vertices']

        #     if mindex <= len(support) - 1:
        #         bindex_mindex[bkey]['type'] = 'support'
        #     else:
        #         bindex_mindex[bkey]['type'] = 'block'

        # return bindex_mindex

    def solve(self):
        pass

    def result(self):
        pass


# =============================================================================
# Viewer
# =============================================================================
# viewer = Viewer()
# for m in meshes:
#     viewer.add(m)
# viewer.show()

# =============================================================================
# Rhino Viewer
# =============================================================================
# scene = Scene()
# for e in model.elements_list:
#     scene.add(e)
# scene.draw()


# model.threedec_config.add_material("concrete", 2200, 35, 300000, 0.2)
# model.threedec_config.get_joint_stiffness_one_material("concrete", 0.20, 10)
# model.threedec_config.get_gravity_input("concrete")
