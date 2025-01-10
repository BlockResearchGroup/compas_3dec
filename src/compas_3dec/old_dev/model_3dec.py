import os
import inspect
from subprocess import call
import logging

from compas.files import OBJ
from compas.datastructures import Mesh
from compas.geometry import convex_hull_xy, Transformation, transform_points, scale_vector
from compas.geometry import Plane, Frame, Polygon, Point, Line

from compas.geometry import (
    scale_vector,
    cross_vectors,
    centroid_points,
    normalize_vector,
    transform_points,
    convex_hull_xy,
    sum_vectors,
    dot_vectors,
)


from compas_model.model import Model, GroupNode
from compas_model.elements import BlockElement

from compas_3dec.threedec_config import ThreedecConfig
from compas_3dec.interactions_3dec import Interaction3dec
from compas.geometry import normalize_vector, norm_vector


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
        self.threedec_config = ThreedecConfig(self)
        self.executable_path = executable_path
        self.working_path = working_path
        if not self.working_path:
            caller_frame = inspect.stack()[-1]
            caller_filename = caller_frame.filename
            self.working_path = os.path.dirname(os.path.abspath(caller_filename))

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
    def model_from_obj(path_supports, path_blocks, working_path=None):
        meshes_supports = Model_3dec.from_obj(path_supports)
        meshes_blocks = Model_3dec.from_obj(path_blocks)
        model = Model_3dec(working_path=working_path)
        group_supports = model.add_group("Supports")
        group_blocks = model.add_group("Blocks")
        for i in range(len(meshes_supports)):
            support = BlockElement(meshes_supports[i], is_support=True)
            model.add_element(support, group_supports)
        for i in range(len(meshes_blocks)):
            block = BlockElement(meshes_blocks[i], is_support=False)
            model.add_element(block, group_blocks)
        return model

    @staticmethod
    def from_library(index):

        # if index
        pass

    @staticmethod
    def model_from_rhino():
        pass

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

    def _threedec7_mesh_description(self, meshes, indices, group=None, precision=3):
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

    # =============================================================================
    # create geometry.dat
    # =============================================================================

    def to_3dec_geometry(self):
        """Create the .dat files of the Blocks and Supports geometry for 3DEC from an
        Assembly_3DEC object. This function recognises compounds of joined blocks (e.g.
        a group of 3D convex meshes joined together forming a concave shape) enabling
        the creation of Master/Slave compounds in 3DEC.
        """
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
                outputs += self._threedec7_mesh_description(meshes, indices, node.name, precision=3)
        geometry_path = os.path.join(self.working_path, "geometry.dat")
        self._overwrite_file(geometry_path, outputs)

    def to_3dec_geometry_interactions(self):
        """Create the .dat files of the Blocks and Supports geometry for 3DEC from an
        Assembly_3DEC object. This function recognises compounds of joined blocks (e.g.
        a group of 3D convex meshes joined together forming a concave shape) enabling
        the creation of Master/Slave compounds in 3DEC.
        """
        outputs = ""
        for indices in self.graph.connected_nodes():
            name = "Supports" if self.elementlist[indices[0]].is_support else "Blocks"
            outputs += ";__create " + str(name) + "__" + "\n"
            meshes = []
            for index in indices:
                meshes.append(self.elementlist[index].geometry)
            outputs += self._threedec7_mesh_description(meshes, indices, name, precision=3)
        geometry_path = os.path.join(self.working_path, "geometry.dat")
        self._overwrite_file(geometry_path, outputs)

    # =============================================================================
    # run 3dec in the background
    # =============================================================================
    def run(self, sequence=[]):
        args = ["cd", self.working_path, "&&", self.executable_path] + sequence
        call(" ".join(args), shell=True)

    # =============================================================================
    # get and process BLOCK data from 3dec
    # =============================================================================
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

    # =============================================================================
    # get and process CONTACT data from 3dec
    # =============================================================================
    def from_3dec_contacts(self, filename, precision="3f"):
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
                    contacts[id]["subcontacts"][ids]["normal_force"] = normal_force / 1000
                    contacts[id]["subcontacts"][ids]["shear_force"] = [
                        shear_force[0] / 1000,
                        shear_force[1] / 1000,
                        shear_force[2] / 1000,
                    ]
                    contacts[id]["subcontacts"][ids]["normal_displ"] = normal_displ
                    contacts[id]["subcontacts"][ids]["shear_displ"] = shear_displ
                    contacts[id]["subcontacts"][ids]["normal_stress"] = normal_stress
                    contacts[id]["subcontacts"][ids]["shear_stress"] = shear_stress
                    contacts[id]["subcontacts"][ids]["area"] = area
                    continue

        for key, contact in contacts.items():
            neighbours = contact["neighbours"]

            # get list of subcontacts coordinates
            output_3dec_per_vertex = {}

            for key, subcontact in contact["subcontacts"].items():
                point = subcontact["coordinates"]
                position = self.geometric_key(point, precision)
                normal_force = scale_vector(contact["normal"], subcontact["normal_force"])
                shear_force = subcontact["shear_force"]
                normal_displacement = scale_vector(contact["normal"], subcontact["normal_displ"])
                shear_displacement = subcontact["shear_displ"]
                normal_stress = subcontact["normal_stress"]
                shear_stress = subcontact["shear_stress"]
                area = subcontact["area"]

                if position in output_3dec_per_vertex:
                    # Correctly access and update the dictionary for the existing key
                    output_3dec_per_vertex[position]["normal_force"] = [
                        x + y for x, y in zip(output_3dec_per_vertex[position]["normal_force"], normal_force)
                    ]
                    output_3dec_per_vertex[position]["shear_force"] = [
                        x + y for x, y in zip(output_3dec_per_vertex[position]["shear_force"], shear_force)
                    ]
                    output_3dec_per_vertex[position]["normal_displacement"] = [
                        x + y
                        for x, y in zip(output_3dec_per_vertex[position]["normal_displacement"], normal_displacement)
                    ]
                    output_3dec_per_vertex[position]["shear_displacement"] = [
                        x + y
                        for x, y in zip(output_3dec_per_vertex[position]["shear_displacement"], shear_displacement)
                    ]
                    output_3dec_per_vertex[position]["normal_stress"] += normal_stress
                    output_3dec_per_vertex[position]["shear_stress"] += shear_stress
                    output_3dec_per_vertex[position]["area"] += area
                    output_3dec_per_vertex[position]["is_combined"] = True
                else:
                    output_3dec_per_vertex[position] = {
                        "position": point,
                        "normal_force": normal_force,
                        "shear_force": shear_force,
                        "normal_displacement": normal_displacement,
                        "shear_displacement": shear_displacement,
                        "normal_stress": normal_stress,
                        "shear_stress": shear_stress,
                        "area": area,
                        "is_combined": False,
                    }

            points = []
            output_list = []
            for key, value in output_3dec_per_vertex.items():
                points.append(value["position"])

            if len(points) > 2:
                normal = contact["normal"]
                position = contact["position"]
                plane = Plane(position, normal)
                frame = Frame.from_plane(plane)
                transformation = Transformation.from_frame_to_frame(frame, Frame.worldXY())
                points = transform_points(points, transformation)
                # ToDo: to be verified based on contact conditions (hinge)
                points = convex_hull_xy(points)
                points = transform_points(points, transformation.inverse())
                contact_geometry = Polygon(points)
                for point in points:
                    gkey = self.geometric_key(point, precision)
                    output_list.append(output_3dec_per_vertex[gkey])

            elif len(points) == 2:
                contact_geometry = Line(points[0], points[1])
                output_list = output_3dec_per_vertex.values()
            else:
                contact_geometry = Point(points[0])
                output_list = output_3dec_per_vertex.values()

            interaction = Interaction3dec(
                type=contact["type"],
                normal=contact["normal"],
                contact_geometry=contact_geometry,
                forces_per_vertices=output_list,
            )
            self.add_interaction(self.elementlist[neighbours[0]], self.elementlist[neighbours[1]], interaction)
        return output_3dec_per_vertex, contacts

    def from_3dec_contacts_resultant(self, filename, precision="3f"):
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
                    contacts[id]["subcontacts"][ids]["normal_force"] = normal_force / 1000
                    contacts[id]["subcontacts"][ids]["shear_force"] = [
                        shear_force[0] / 1000,
                        shear_force[1] / 1000,
                        shear_force[2] / 1000,
                    ]
                    contacts[id]["subcontacts"][ids]["normal_displ"] = normal_displ
                    contacts[id]["subcontacts"][ids]["shear_displ"] = shear_displ
                    contacts[id]["subcontacts"][ids]["normal_stress"] = normal_stress
                    contacts[id]["subcontacts"][ids]["shear_stress"] = shear_stress
                    contacts[id]["subcontacts"][ids]["area"] = area
                    continue

        for key, contact in contacts.items():
            neighbours = contact["neighbours"]
            contact_normal = normalize_vector(contact["normal"])

            # get list of subcontacts coordinates
            output_3dec_per_vertex = {}

            for key, subcontact in contact["subcontacts"].items():
                point = subcontact["coordinates"]
                position = self.geometric_key(point, precision)
                normal_force = scale_vector(contact_normal, subcontact["normal_force"])
                shear_force = subcontact["shear_force"]
                normal_displacement = scale_vector(contact_normal, subcontact["normal_displ"])
                shear_displacement = subcontact["shear_displ"]
                normal_stress = subcontact["normal_stress"]
                shear_stress = subcontact["shear_stress"]
                area = subcontact["area"]

                if position in output_3dec_per_vertex:
                    # Correctly access and update the dictionary for the existing key
                    output_3dec_per_vertex[position]["normal_force"] = [
                        x + y for x, y in zip(output_3dec_per_vertex[position]["normal_force"], normal_force)
                    ]
                    output_3dec_per_vertex[position]["shear_force"] = [
                        x + y for x, y in zip(output_3dec_per_vertex[position]["shear_force"], shear_force)
                    ]
                    output_3dec_per_vertex[position]["normal_displacement"] = [
                        x + y
                        for x, y in zip(output_3dec_per_vertex[position]["normal_displacement"], normal_displacement)
                    ]
                    output_3dec_per_vertex[position]["shear_displacement"] = [
                        x + y
                        for x, y in zip(output_3dec_per_vertex[position]["shear_displacement"], shear_displacement)
                    ]
                    output_3dec_per_vertex[position]["normal_stress"] += normal_stress
                    output_3dec_per_vertex[position]["shear_stress"] += shear_stress
                    output_3dec_per_vertex[position]["area"] += area
                    output_3dec_per_vertex[position]["is_combined"] = True

                else:
                    output_3dec_per_vertex[position] = {
                        "position": point,
                        "normal_force": normal_force,
                        "shear_force": shear_force,
                        "normal_displacement": normal_displacement,
                        "shear_displacement": shear_displacement,
                        "normal_stress": normal_stress,
                        "shear_stress": shear_stress,
                        "area": area,
                        "is_combined": False,
                    }
            # post-processing
            Mtorque_tot = [0, 0, 0]
            Mtot = [0, 0, 0]
            Ntot = 0
            Stot = [0, 0, 0]

            output_list = []
            points = [value["position"] for value in output_3dec_per_vertex.values()]
            if points:
                centroid = centroid_points(points)

            output_3dec_per_contact = {}
            first_iteration = True
            for key, value in output_3dec_per_vertex.items():
                vertex = value["position"]
                ri = [vertex[0] - centroid[0], vertex[1] - centroid[1], vertex[2] - centroid[2]]
                if first_iteration:
                    e1_plane = normalize_vector(ri)
                    e2_plane = cross_vectors(contact_normal, e1_plane)
                    first_iteration = False
                Ni = norm_vector(value["normal_force"])
                Mi = cross_vectors(ri, value["normal_force"])
                Mtot = sum_vectors([Mtot, Mi])
                Ntot = Ntot + Ni
                Si = value["shear_force"]
                Stot = sum_vectors([Stot, Si])
                Mtorque_i = cross_vectors(ri, Si)
                Mtorque_tot = sum_vectors([Mtorque_tot, Mtorque_i])

            # if Ntot:
            if Ntot:
                Ftot = sum_vectors([Stot, scale_vector(contact_normal, Ntot)])
                NN = scale_vector(contact_normal, Ntot)
                b1 = -1 * dot_vectors(Mtot, e2_plane) / Ntot
                b2 = dot_vectors(Mtot, e1_plane) / Ntot
                # point of application of the resultant normal force
                po = sum_vectors([centroid, scale_vector(e1_plane, b1), scale_vector(e2_plane, b2)])
                norm_Stot = norm_vector(Stot)
                if norm_Stot != 0:
                    s1 = -1 * dot_vectors(Mtorque_tot, e2_plane) / norm_Stot
                    s2 = dot_vectors(Mtorque_tot, e1_plane) / norm_vector(Stot)
                    ps = sum_vectors([centroid, scale_vector(e1_plane, s1), scale_vector(e2_plane, s2)])
                else:
                    s1 = 0  # or some other value that makes sense in this context
                # s1 = -1 * dot_vectors(Mtorque_tot, e2_plane) / norm_vector(Stot)
                # s2 = dot_vectors(Mtorque_tot, e1_plane) / norm_vector(Stot)
                # one point along the line of action of the resultant shear force
                # ps = sum_vectors([centroid, scale_vector(e1_plane, s1), scale_vector(e2_plane, s2)])
                # Calculate the vector from po to the centroid
                r_po_centroid = sum_vectors([centroid, scale_vector(po, -1)])
                # Calculate the moment generated by the total shear force at a distance from po
                M_shear_po = cross_vectors(r_po_centroid, Stot)

                output_3dec_per_contact["resultant_force"] = Ftot
                output_3dec_per_contact["resultant_point"] = po
                output_3dec_per_contact["resultant_point_shear"] = ps
                output_3dec_per_contact["resultant_normal"] = NN
                output_3dec_per_contact["resultant_shear"] = Stot
                output_3dec_per_contact["resultant_torque"] = M_shear_po

            if len(points) > 2:
                normal = contact["normal"]
                position = contact["position"]
                plane = Plane(position, normal)
                frame = Frame.from_plane(plane)
                transformation = Transformation.from_frame_to_frame(frame, Frame.worldXY())
                points = transform_points(points, transformation)
                # ToDo: to be verified based on contact conditions (hinge)
                points = convex_hull_xy(points)
                points = transform_points(points, transformation.inverse())
                contact_geometry = Polygon(points)
                # for point in points:
                #     gkey = self.geometric_key(point, precision)
                #     output_list.append(output_3dec_per_vertex[gkey])

            elif len(points) == 2:
                contact_geometry = Line(points[0], points[1])
                output_list = output_3dec_per_vertex.values()
            else:
                # contact_geometry = Point(points[0])
                # contact_geometry = "no contact"
                output_list = output_3dec_per_vertex.values()

            interaction = Interaction3dec(
                type=contact["type"],
                normal=contact_normal,
                contact_geometry=contact_geometry,
                forces_per_vertices=output_list,
                forces_per_contact=output_3dec_per_contact,
            )
            self.add_interaction(self.elementlist[neighbours[0]], self.elementlist[neighbours[1]], interaction)
        return output_3dec_per_vertex

    # =============================================================================
    # analysis utilities
    # =============================================================================
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

    # =============================================================================
    # post_processing
    # =============================================================================
    def cracks_detection(self, cracks=True, hinges=False):
        pass

    # =============================================================================
    # utilities
    # =============================================================================
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

    def solve(self):
        pass

    def result(self):
        pass

    # def contact_forces(self, output_3dec_per_vertex, scale_factor, region, mu, Shear=False):
    #     # visualise contact forces acting on a single block in compression in only one region is given as argument
    #     # otherwise it visualises action and reaction forces in all blocks
    #     # contacts = data_from_threedec_contact(str(contact_file))
    #     normals = []
    #     points = []
    #     c_forces = []
    #     cc_pos = []
    #     # loop per contact
    #     for contact in contacts:
    #         # check if the region is in the contact neighbours
    #         if region in contacts[contact]['neighbours']:
    #             #check if the contact has subcontacts otherwise there are no mechanical data from 3DEC
    #             if contacts[contact]['subcontacts']:
    #                 # check the position of the region(block) in the neighbours list
    #                 # according to the position [0] or [1] the contact's normal has to be flipped to visualise compression
    #                 # and get the contact's normal + the subcontacts' list
    #                 if contacts[contact]['neighbours'][0] == region:
    #                     s_dict = contacts[contact]['subcontacts']
    #                     normal = scale_vector(contacts[contact]['normal'], -1)
    #                 else:
    #                     s_dict = contacts[contact]['subcontacts']
    #                     normal = contacts[contact]['normal']
    #                 # get the vertices [x,y,z] of the contact face and create a list
    #                 verts = []
    #                 for sub in s_dict:
    #                     vertex = s_dict[sub]['coordinates']
    #                     verts.append(vertex)
    #                 #compute centroid from the vertex list
    #                 centroid = centroid_points(verts)

    #                 # 3DEC results post-processing 1st part
    #                 for sub in s_dict:
    #                     if s_dict[sub]['normal_force']:
    #                         vertex = s_dict[sub]['coordinates']
    #                         e1_plane = normalize_vector(
    #                             (vertex[0] - centroid[0], vertex[1] - centroid[1], vertex[2] - centroid[2]))
    #                         e2_plane = cross_vectors(normal, e1_plane)
    #                         break
    #                 Mtorque_tot = [0, 0, 0]
    #                 Mtot = [0, 0, 0]
    #                 Ntot = 0
    #                 Stot = [0, 0, 0]

    #                 # list of shear forces used later for pure shear calculation (no transportation couple)
    #                 slist = []
    #                 # 3DEC results post-processing 2nd part
    #                 for sub in s_dict:
    #                     vertex = s_dict[sub]['coordinates']
    #                     ri = ((vertex[0] - centroid[0], vertex[1] -
    #                         centroid[1], vertex[2] - centroid[2]))
    #                     Ni = s_dict[sub]['normal_force']

    #                     # visualise the normal contact forces per subcontact
    #                     rs.CurrentLayer('3dec_normals')
    #                     nnn = scale_vector(normal, Ni)
    #                     Nview = add_vectors(vertex,scale_vector(nnn,scale_factor))
    #                     if distance_point_point(vertex,Nview)>0.00001:
    #                         ln = rs.AddLine(vertex,Nview)
    #                         rs.CurveArrows(ln, 1)

    #                     # 3DEC results post-processing 2nd part
    #                     Mi = cross_vectors(ri, scale_vector(normal, Ni))
    #                     Mtot = sum_vectors([Mtot, Mi])
    #                     Ntot = Ntot + Ni
    #                     # check position of the region(block) to switch shear forces direction
    #                     if contacts[contact]['neighbours'][0] == region:
    #                         Si = (-1 * (s_dict[sub]['shear_force'][0]), -1 * (s_dict[sub]
    #                                                                         ['shear_force'][1]), -1 * (s_dict[sub]['shear_force'][2]))
    #                         Stot = (sum_vectors([Stot, Si]))
    #                         slist.append(Si)

    #                         # visualise the shear contact forces per subcontact
    #                         rs.CurrentLayer('3dec_shear')
    #                         sview = add_vectors(vertex,scale_vector(Si,scale_factor))
    #                         if distance_point_point(vertex,sview)>0.00001:
    #                             ls1 = rs.AddLine(vertex,sview)
    #                             rs.CurveArrows(ls1, 1)

    #                         # calculate torque
    #                         Mtorque_i = cross_vectors(ri, Si)
    #                         Mtorque_tot = sum_vectors([Mtorque_tot, Mtorque_i])

    #                     else:
    #                         Si = s_dict[sub]['shear_force']
    #                         Stot = (sum_vectors([Stot, Si]))
    #                         slist.append(Si)

    #                         # visualise the shear contact forces per subcontact
    #                         rs.CurrentLayer('3dec_shear')
    #                         sview = add_vectors(vertex,scale_vector(Si,scale_factor))
    #                         if distance_point_point(vertex,sview)>0.00001:
    #                             ls2 = rs.AddLine(vertex,sview)
    #                             rs.CurveArrows(ls2, 1)

    #                         # calculate torque
    #                         Mtorque_i = cross_vectors(ri, Si)
    #                         Mtorque_tot = sum_vectors([Mtorque_tot, Mtorque_i])

    #                 # 3DEC results post-processing 3rd part
    #                 if Ntot:
    #                     # contact position (to be checked if this is the pure point from 3DEC or post-processed based on resultant)
    #                     c_pos = contacts[contact]['position']
    #                     cc_pos.append(c_pos)

    #                     # compute the Z-component of the resultant shear contact force
    #                     Svert = dot_vectors(Stot,Vector.Zaxis())
    #                     Svert = scale_vector(Vector.Zaxis(),Svert)
    #                     # compute the third component of the resultant shear contact force after the Z one and the resultant
    #                     Sother = subtract_vectors(Stot,Svert)

    #                     # compute the resultant contact force
    #                     Ftot = sum_vectors([Stot, scale_vector(normal, Ntot)])
    #                     c_forces.append(Ftot)

    #                     NN = scale_vector(normal, Ntot)
    #                     b2 = dot_vectors(Mtot, e1_plane) / Ntot
    #                     b1 = -1 * dot_vectors(Mtot, e2_plane) / Ntot

    #                     # point of application of the resultant contact force
    #                     po = sum_vectors([centroid, scale_vector(
    #                         e1_plane, b1), scale_vector(e2_plane, b2)])
    #                     points.append(po)
    #                     normals.append(normal)

    #                     Mtorquepo = sum_vectors([Mtorque_tot, cross_vectors(
    #                     sum_vectors([centroid, scale_vector(po, -1)]), Stot)])

    #                     # calculation of the S/N ratio

    #                     # si = length_vector(Stot)/length_vector(NN)
    #                     # rs.AddTextDot("%.2f" % si,po)
    #                     # if (si <= 0.1):
    #                     #     rs.CurrentLayer('S/N<=0.1')
    #                     #     rs.AddPoint(po)
    #                     #     rs.AddTextDot("%.2f" % si,po)
    #                     # elif (si > 0.1) and (si <= 0.2):
    #                     #     rs.CurrentLayer('0.1<S/N<=0.2')
    #                     #     rs.AddPoint(po)
    #                     #     rs.AddTextDot("%.2f" % si,po)
    #                     # elif (si > 0.2) and (si <= 0.3):
    #                     #     rs.CurrentLayer('0.2<S/N<=0.3')
    #                     #     rs.AddPoint(po)
    #                     #     rs.AddTextDot("%.2f" % si,po)
    #                     # elif (si > 0.3) and (si <= 0.4):
    #                     #     rs.CurrentLayer('0.3<S/N<=0.4')
    #                     #     rs.AddPoint(po)
    #                     #     rs.AddTextDot("%.2f" % si,po)
    #                     # elif (si > 0.4) and (si <= 0.5):
    #                     #     rs.CurrentLayer('0.4<S/N<=0.5')
    #                     #     rs.AddPoint(po)
    #                     #     rs.AddTextDot("%.2f" % si,po)
    #                     # elif (si > 0.5) and (si <= 0.6):
    #                     #     rs.CurrentLayer('0.5<S/N<=0.6')
    #                     #     rs.AddPoint(po)
    #                     #     rs.AddTextDot("%.2f" % si,po)
    #                     # elif (si > 0.6) and (si <= 0.7):
    #                     #     rs.CurrentLayer('0.6<S/N<=0.7')
    #                     #     rs.AddPoint(po)
    #                     #     rs.AddTextDot("%.2f" % si,po)
    #                     # elif (si > 0.7) and (si <= 0.8):
    #                     #     rs.CurrentLayer('0.7<S/N<=0.8')
    #                     #     rs.AddPoint(po)
    #                     #     rs.AddTextDot("%.2f" % si,po)
    #                     # elif (si > 0.8) and (si <= 0.9):
    #                     #     rs.CurrentLayer('0.8<S/N<=0.9')
    #                     #     rs.AddPoint(po)
    #                     #     rs.AddTextDot("%.2f" % si,po)
    #                     # elif (si > 0.9) and (si <= 1.0):
    #                     #     rs.CurrentLayer('0.9<S/N<=1.0')
    #                     #     rs.AddPoint(po)
    #                     #     rs.AddTextDot("%.2f" % si,po)

    #                     rs.CurrentLayer('Default')
    #                     rs.LayerVisible('3dec_shear', False)

    #                     # calculation of the S/N*mu ratio
    #                     # closeness to limit
    #                     n_mu = (length_vector(NN))*mu
    #                     sil = length_vector(Stot)/n_mu
    #                     # rs.AddTextDot("%.2f" % sil,po)

    #                     if (sil <= 0.1):
    #                         rs.CurrentLayer('S/N*mu<=0.1')
    #                         rs.AddPoint(po)
    #                         rs.AddTextDot("%.2f" % sil,po)
    #                     elif (sil > 0.1) and (sil <= 0.2):
    #                         rs.CurrentLayer('0.1<S/N*mu<=0.2')
    #                         rs.AddPoint(po)
    #                         rs.AddTextDot("%.2f" % sil,po)
    #                     elif (sil > 0.2) and (sil <= 0.3):
    #                         rs.CurrentLayer('0.2<S/N*mu<=0.3')
    #                         rs.AddPoint(po)
    #                         rs.AddTextDot("%.2f" % sil,po)
    #                     elif (sil > 0.3) and (sil <= 0.4):
    #                         rs.CurrentLayer('0.3<S/N*mu<=0.4')
    #                         rs.AddPoint(po)
    #                         rs.AddTextDot("%.2f" % sil,po)
    #                     elif (sil > 0.4) and (sil <= 0.5):
    #                         rs.CurrentLayer('0.4<S/N*mu<=0.5')
    #                         rs.AddPoint(po)
    #                         rs.AddTextDot("%.2f" % sil,po)
    #                     elif (sil > 0.5) and (sil <= 0.6):
    #                         rs.CurrentLayer('0.5<S/N*mu<=0.6')
    #                         rs.AddPoint(po)
    #                         rs.AddTextDot("%.2f" % sil,po)
    #                     elif (sil > 0.6) and (sil <= 0.7):
    #                         rs.CurrentLayer('0.6<S/N*mu<=0.7')
    #                         rs.AddPoint(po)
    #                         rs.AddTextDot("%.2f" % sil,po)
    #                     elif (sil > 0.7) and (sil <= 0.8):
    #                         rs.CurrentLayer('0.7<S/N*mu<=0.8')
    #                         rs.AddPoint(po)
    #                         rs.AddTextDot("%.2f" % sil,po)
    #                     elif (sil > 0.8) and (sil <= 0.9):
    #                         rs.CurrentLayer('0.8<S/N*mu<=0.9')
    #                         rs.AddPoint(po)
    #                         rs.AddTextDot("%.2f" % sil,po)
    #                     elif (sil > 0.9) and (sil <= 1.0):
    #                         rs.CurrentLayer('0.9<S/N*mu<=1.0')
    #                         rs.AddPoint(po)
    #                         rs.AddTextDot("%.2f" % sil,po)

    #                     rs.CurrentLayer('Default')
    #                     rs.LayerVisible('Shear/N*mu', False)

    #                     # contact forces visualisation
    #                     end_point_2 = sum_vectors(
    #                         [po, scale_vector(Ftot, -scale_factor)])
    #                     end_point_4 = sum_vectors(
    #                         [po, scale_vector(NN, -scale_factor)])
    #                     end_point_6 = sum_vectors(
    #                         [po, scale_vector(Stot, -scale_factor)])
    #                     end_point_21 = sum_vectors(
    #                     [po, scale_vector(Mtorquepo, -scale_factor)])

    #                     end_point_Svert = sum_vectors(
    #                         [po, scale_vector(Svert, -scale_factor)])
    #                     end_point_Sother = sum_vectors(
    #                         [po, scale_vector(Sother, -scale_factor)])

    #                     rs.CurrentLayer('Thrust_pt')
    #                     rs.AddPoint(po)

    #                     rs.CurrentLayer('Thrust')
    #                     if distance_point_point(po, end_point_2) > 0.0001:
    #                         th1 = rs.AddLine(po, end_point_2)
    #                         rs.CurveArrows(th1, 1)

    #                     rs.CurrentLayer('Thrust_N')
    #                     if distance_point_point(po, end_point_4) > 0.0001:
    #                         tn1 = rs.AddLine(po, end_point_4)
    #                         rs.CurveArrows(tn1, 1)

    #                     rs.CurrentLayer('Thrust_S')
    #                     if distance_point_point(po, end_point_6) > 0.0001:
    #                         ts1 = rs.AddLine(po, end_point_6)
    #                         rs.CurveArrows(ts1, 1)

    #                     rs.CurrentLayer('Thrust_Svert')
    #                     if distance_point_point(po, end_point_Svert) > 0.0001:
    #                         tsv = rs.AddLine(po, end_point_Svert)
    #                         rs.CurveArrows(tsv, 1)

    #                     rs.CurrentLayer('Thrust_Sother')
    #                     if distance_point_point(po, end_point_Sother) > 0.0001:
    #                         tso = rs.AddLine(po, end_point_Sother)
    #                         rs.CurveArrows(tso, 1)

    #                     rs.CurrentLayer('Torque')
    #                     if distance_point_point(po, end_point_21) > 0.0001:
    #                         to1 = rs.AddLine(po, end_point_21)
    #                         rs.CurveArrows(to1, 1)

    #                     if Shear == True:
    #                         # pure shear visualisation
    #                         mvecs = [0,0,0]
    #                         refvecs = []
    #                         # loop in the vertex, shear forces lists per contact
    #                         for i,l in zip(verts,slist):
    #                             svec = Vector.from_start_end(i,l)
    #                             refvec = subtract_vectors(i,po)
    #                             mvec = cross_vectors(refvec,svec)
    #                             # resultant moment
    #                             mvecs = (sum_vectors([mvecs, mvec]))
    #                             refvecs.append(refvec)
    #                         normal = normalize_vector(cross_vectors(refvecs[1],refvecs[0]))
    #                         d = length_vector(mvecs)/length_vector(Stot)
    #                         dire = normalize_vector(cross_vectors(normal,Stot))
    #                         direc = add_vectors(po,scale_vector(dire,d))
    #                         rr = add_vectors(direc,scale_vector(Stot,scale_factor))

    #                         rs.CurrentLayer('Shear')
    #                         if distance_point_point(direc, rr) > 0.0001:
    #                             sh1 = rs.AddLine(rr, direc)
    #                             rs.CurveArrows(sh1, 2)

    #         rs.CurrentLayer('Default')
    #         rs.LayerVisible('Thrust', False)
    #         rs.LayerVisible('Thrust_N', False)
    #         rs.LayerVisible('Thrust_S', False)
    #         rs.LayerVisible('Thrust_Svert', False)
    #         rs.LayerVisible('Thrust_Sother', False)
    #         rs.LayerVisible('Thrust_pt', False)
    #         rs.LayerVisible('Torque', False)
    #         rs.LayerVisible('3dec_normals', False)
    #         rs.LayerVisible('3dec_shear', False)
    #         rs.LayerVisible('Shear', False)

    #     return [c_forces], [points], [normals], [cc_pos]


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
