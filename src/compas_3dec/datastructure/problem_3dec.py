import os
import time
import inspect
import compas
from compas.data import Data
from subprocess import call
from compas.datastructures import Mesh
from compas.geometry import Plane, Frame, Transformation, Line, Polygon, Vector, Point, convex_hull_xy, transform_points
from compas.geometry import (
    norm_vector,
    centroid_points,
    normalize_vector,
    cross_vectors,
    scale_vector,
    sum_vectors,
    dot_vectors,
)
from compas.colors import Color, ColorMap


class Problem3dec(Data):
    def __init__(
        self,
        input=None,
        groups=None,
        blocks=None,
        rigid_interactions=None,
        compounds=None,
        materials=None,
        contact_properties=None,
        working_path=None,
        interactions=None,
        executable_path='"C:\\Program Files\\Itasca\\3DEC700\\exe64\\3dec700_console.exe"',
        name=None,
    ):
        super().__init__(name)
        self.input = input
        self.groups = groups if groups is not None else []
        self.executable_path = executable_path
        self.working_path = working_path
        self.blocks = blocks if blocks is not None else []
        self.rigid_interactions = rigid_interactions if rigid_interactions is not None else []
        self.compounds = compounds if compounds is not None else []
        self.materials = materials if materials is not None else []
        self.contact_properties = contact_properties if contact_properties is not None else []
        self.interactions = interactions if interactions is not None else []
        self.name = name

        if not self.working_path:
            caller_frame = inspect.stack()[-1]
            caller_filename = caller_frame.filename
            self.working_path = os.path.dirname(os.path.abspath(caller_filename))
        else:
            if self.working_path.startswith("file:"):
                self.working_path = self.working_path[5:]  # Remove the 'file:' prefix
            if "C:\\Program Files\\Rhino 8\\System\\" in self.working_path:
                self.working_path = self.working_path.split("C:\\Program Files\\Rhino 8\\System\\")[-1]
            self.working_path = os.path.abspath(self.working_path)

    @property
    def __data__(self):
        return {
            "input": self.input,
            "groups": [group.__data__ for group in self.groups],
            "executable_path": self.executable_path,
            "working_path": self.working_path,
            "blocks": [block.__data__ for block in self.blocks],
            "rigid_interactions": [interaction.__data__ for interaction in self.rigid_interactions],
            "compounds": self.compounds,
            "materials": [material.__data__ for material in self.materials],
            "contact_properties": [contact_property.__data__ for contact_property in self.contact_properties],
            "interactions": [interaction.__data__ for interaction in self.interactions],
            "name": self.name,
        }

    @classmethod
    def __from_data__(cls, data):
        from .group import Group
        from .block import Block
        from .rigid_interaction import RigidInteraction
        from .material import Material
        from .contact_property import ContactProperty
        from .interaction_3dec import Interaction3dec

        problem = cls(
            input=data.get("input"),
            materials=[Material.__from_data__(material) for material in data["materials"]],
            groups=[Group.__from_data__(group) for group in data["groups"]],
            rigid_interactions=[
                RigidInteraction.__from_data__(interaction) for interaction in data["rigid_interactions"]
            ],
            contact_properties=[
                ContactProperty.__from_data__(contact_property) for contact_property in data["contact_properties"]
            ],
            blocks=[Block.__from_data__(block) for block in data["blocks"]],
            interactions=[Interaction3dec.__from_data__(interaction) for interaction in data["interactions"]],
            working_path=data["working_path"],
            executable_path=data["executable_path"],
            name=data["name"],
            compounds=data["compounds"],
        )
        return problem

    def __str__(self):
        blocks_str = "\n".join(str(block) for block in self.blocks)
        groups_str = "\n".join(str(group) for group in self.groups)
        materials_str = "\n".join(str(material) for material in self.materials.values())
        interactions_str = "\n".join(str(interaction) for interaction in self.interactions)
        return f"Blocks:\n{blocks_str}\nGroups:\n{groups_str}\nMaterials:\n{materials_str}\nInteractions:\n{interactions_str}"

    @staticmethod
    def from_model(model):
        from compas_3dec.datastructures.conversion import from_model

        input = from_model(model)
        return Problem3dec(input)

    def add_group(self, group):
        if group.name in [group.name for group in self.groups]:
            pass
            # raise ValueError("Group name already exists")
        else:
            self.groups.append(group)

    def get_group_by_name(self, name):
        for group in self.groups:
            if group.name == name:
                return group
        return None

    def add_blocks(self, meshes):
        from .block import Block

        for i, mesh in enumerate(meshes):
            self.blocks.append(Block(i, mesh))

    def add_material(self, name, E, poisson, rho, group=None):
        from .material import Material

        material = Material(name, E, poisson, rho, group)
        self.materials.append(material)
        if group:
            for gr in group:
                for g in self.groups:
                    if g.name == gr:
                        g.material = material
        return material

    def add_contact_property(self, stiffness, failure_criteria, group=None):
        from .contact_property import ContactProperty

        contact_property = ContactProperty(stiffness, failure_criteria, group)
        self.contact_properties.append(contact_property)
        if group:
            for gr in group:
                for g in self.groups:
                    if g.name == gr:
                        g.contact_property = contact_property
        return contact_property

    def add_rigid_interactions(self, block_lists):
        for blocks in block_lists:
            self.rigid_interactions.append(blocks)

    def add_interaction(self, interaction_data):
        self.interactions.append(interaction_data)

    def make_compounds(self):
        if self.rigid_interactions:
            self.compounds.extend(self.rigid_interactions)
            for block in self.blocks:
                if not any(block.index in interaction for interaction in self.rigid_interactions):
                    self.compounds.append([block.index])
            self.compounds = sorted(self.compounds, key=lambda x: x[0])
        else:
            for block in self.blocks:
                self.compounds.append([block.index])
        return self.compounds

    def to_geometry_3dec(self):
        """Create the .dat files of the Blocks and Supports geometry for 3DEC from an
        Assembly_3DEC object. This function recognises compounds of joined blocks (e.g.
        a group of 3D convex meshes joined together forming a concave shape) enabling
        the creation of Master/Slave compounds in 3DEC.
        """
        self.make_compounds()
        outputs = ""
        for indices in self.compounds:
            block = self.blocks[indices[0]]
            if block.is_support:
                group = "Supports"
            elif block.group is None:
                group = "Blocks"
            else:
                group = block.group
            outputs += ";__create " + str(group) + "__" + "\n"

            meshes = []
            for index in indices:
                meshes.append(self.blocks[index].mesh)
            outputs += self._to_mesh_string_3dec(meshes, indices, group, precision=3)

        geometry_path = os.path.join(self.working_path, "geometry.dat")

        # print('geometry_path',geometry_path)
        self._overwrite_file(geometry_path, outputs)

    def _to_mesh_string_3dec(self, meshes, indices, group, precision=10):
        """Convert compas meshes to string readable by 3dec.

        Parameters
        ----------
        meshes : list[compas.datastractures.Mesh]
            List of compas meshes.
        indices : list[int]
            List of indices of the meshes from model graph nodes.
        group : str
           3dec block's group name.
        precision : int, optional
            Set vertex coordinates rounding, by default 10.

        Returns
        -------
        str
            Single string reprensenting the group name and the block geometry.
        """
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

    def assign_material(self, material_name, group_name):
        self.input.materials[material_name].group = group_name
        # for key,value in self.input.materials.items():
        #     if key == material_name:
        #         self.input.materials.group = group_name
        print(self.input.materials)

    # =============================================================================
    # setup 3dec analysis
    # =============================================================================

    def set_joint_stiffness_one_material(self, block_height, reduction_factor, block_length=None, material=None):
        """Compute the joint stiffness values for a model with one joint material (dry assembled).

        Parameters
        ----------
        block_height : float
            Block height.
        reduction_factor : float
            Reduction factor for the joint stiffness.
        block_length : float, optional
            Block length, by default None.
        material_name : str, optional
            Material name, by default None.
        """
        # E = self.materials[material_name].E
        # G = self.materials[material_name].G
        E = material.E
        G = material.G
        # E = self.input.materials[material_name].E
        # G = self.input.materials[material_name].G

        if not block_length:
            jkn = E / block_height
            jks = G / block_height
        else:
            jkn = ((E / block_height) + (E / block_length)) / 2
            jks = ((G / block_height) + (G / block_length)) / 2

        jkn = jkn / reduction_factor
        jks = jks / reduction_factor

        return (jkn, jks)

    def set_joint_stiffness_two_materials(
        self, block_height, interface_thickness, reduction_factor, material0_name=None, material1_name=None
    ):
        """Compute the joint stiffness values for a model with two joints materials (i.e. stone and mortar).

        Parameters
        ----------
        block_height : float
            Block height.
        interface_thickness : float
            Interface material thickness.
        reduction_factor : float
            Reduction factor for the joint stiffness.
        material0_name : str, optional
            Material name stored in the input.
        material1_name : str, optional
            Material name stored in the input.
        """

        E1 = self.materials[material0_name].E
        G1 = self.materials[material0_name].G
        E2 = self.materials[material1_name].E
        G2 = self.materials[material1_name].G

        # E1 = self.input.materials[material0_name].E
        # G1 = self.input.materials[material0_name].G
        # E2 = self.input.materials[material1_name].E
        # G2 = self.input.materials[material1_name].G

        jkn = (E1 * E2) / ((block_height * E2) + (interface_thickness * E1))
        jks = (G1 * G2) / ((block_height * G2) + (interface_thickness * G1))

        self.jkn = jkn / reduction_factor
        self.jks = jks / reduction_factor

        return (jkn, jks)

    # =============================================================================
    # gravity
    # =============================================================================
    def gravity_equilibrium(
        self, steps=10, keyword="ratio-local", ratio=1e-06, time=0.02, final_ratio=1e-06, time_final_step=1
    ):
        """_summary_

        Parameters
        ----------
        steps : _type_
            _description_
        keyword : _type_
            _description_
        ratio : _type_
            _description_
        time : _type_
            _description_
        final_ratio : _type_
            _description_
        time_final_step : _type_
            _description_

        Returns
        -------
        _type_
            _description_
        """

        g = -9.806 / steps
        g = round(g, 3)
        text = ";===========================================================================" + "\n"
        text += ";GRAVITY APPLIED IN" + " " + str(steps) + " " + "STEPS " + "\n"
        text += ";===========================================================================" + "\n"
        for i in range(steps):
            gr = g * (i + 1)
            # header = ';^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^' + '\n'
            header = ";======================================================================" + "\n"
            header += ";_____GRAVITY_____" + " " + "step" + " " + str(i + 1) + "\n"
            header += ";======================================================================" + "\n"
            header += "model gravity" + " " + "0" + " " + "0" + " " + str(gr) + "\n"
            header += "model solve" + " " + str(keyword) + " " + str(ratio) + " " + "time" + " " + str(time) + "\n"
            text += header
        text += (
            "model solve"
            + " "
            + str(keyword)
            + " "
            + str(final_ratio)
            + " "
            + "time"
            + " "
            + str(time_final_step)
            + "\n"
        )
        return text

    def gravity(
        self,
        steps=10,
        keyword="ratio-local",
        ratio=1e-06,
        time_step=0.02,
        final_ratio=1e-05,
        time_final_step=1,
    ):

        self._check_and_delete_gravity_files(self.working_path)
        # if not self.contact_property.stiffness:
        # # if not self.jkn or not self.jks:
        #     raise ValueError("Missing Joint Stiffness values")

        main_string = ";" + time.strftime("%d/%m/%Y") + " " + time.strftime("%H:%M:%S")
        main_string += """
    model new
    model large-strain on
    program call 'geometry.dat'
    block contact generate-subcontacts
    """
        for group in self.groups:
            group_header = """
    block property density {0} range group '{1}'
    block contact property stiffness-normal {2} stiffness-shear {3} friction {4} range group '{1}'
    block contact material-table default property stiffness-normal {2} stiffness-shear {3}
        """.format(
                group.material.rho,
                group.name,
                group.contact_property.stiffness[0],
                group.contact_property.stiffness[1],
                group.contact_property.failure_criteria.friction,
            )
            if group.name == "Supports":
                group_header += "block fix range group 'Supports'\n"
            main_string += group_header
        main_string += self.set_damping_global()

        main_string += self.blocks_output()
        main_string += self.contacts_output()
        main_string += self.save_blocks_output("init_state")
        main_string += self.save_analysis("init")
        main_string += self.restore_analysis("init")
        main_string += "\n"
        main_string += self.gravity_equilibrium(steps, keyword, ratio, time_step, final_ratio, time_final_step)
        main_string += self.save_blocks_output("grav_state")
        main_string += self.save_contacts_output("contact_grav")
        main_string += self.save_analysis("grav")
        main_string += "exit()"
        output_path = self.working_path
        filename = "gravity.dat"
        with open(os.path.join(output_path, filename), "w") as file:
            file.write(main_string)
        return filename

    # =============================================================================
    # load.dat
    # =============================================================================
    def _load_box(self, point, precision):
        """Create a bounding box range around a point 3D adding +/- the precision
            which can be used after the command 'boundary load' in 3DEC.
        point: xyz
            3D point where to apply the point load.
        precision: float
            dimension to add and subtract in x,y,z direction to the point 3D
            to create the box.
        """
        x1 = point[0] - precision
        x2 = point[0] + precision
        y1 = point[1] - precision
        y2 = point[1] + precision
        z1 = point[2] - precision
        z2 = point[2] + precision
        pl = "range x " + str(x1) + " ," + str(x2) + " y " + str(y1) + " ," + str(y2) + " z " + str(z1) + " ," + str(z2)
        return pl

    def _load_along_direction(self, pt1, pt2, load):
        vec = Vector.from_start_end(pt1, pt2)
        vec = normalize_vector(vec)
        load_components = (
            "xload " + str(vec[0] * load) + " yload " + str(vec[1] * load) + " zload " + str(vec[2] * load)
        )
        return load_components

    def set_point_load(self, application_point, direction_point, load_magnitude, radius, subcontacts_per_point):
        magnitude_per_point = load_magnitude / subcontacts_per_point
        load_vector = Vector.from_start_end(application_point, direction_point)
        load_vector = normalize_vector(load_vector)
        load_vector = scale_vector(load_vector, magnitude_per_point)
        string = (
            "block gridpoint apply force-x "
            + str(load_vector[0])
            + " force-y "
            + str(load_vector[1])
            + " force-z "
            + str(load_vector[2])
            + " range sphere c "
            + str(application_point[0])
            + " "
            + str(application_point[1])
            + " "
            + str(application_point[2])
            + " r "
            + str(radius)
            + "\n"
        )
        return string

    # def set_points_load(self, points_list, load_magnitude, load_vector, radius, subcontacts_per_point):
    #     magnitude_per_point = load_magnitude / subcontacts_per_point
    #     for point in points_list:
    #         load_direction = normalize_vector(load_vector)
    #         load = scale_vector(load_direction, magnitude_per_point)
    #         string = "block gridpoint force-x " + str(load[0]) + " range sphere c " + str(point[0]) + " " + str(point[1]) + " " + str(point[2]) + " r " + str(radius) + "\n"
    #         string += "block gridpoint force-y " + str(load[1]) + " range sphere c " + str(point[0]) + " " + str(point[1]) + " " + str(point[2]) + " r " + str(radius) + "\n"
    #         string += "block gridpoint force-z " + str(load[2]) + " range sphere c " + str(point[0]) + " " + str(point[1]) + " " + str(point[2]) + " r " + str(radius) + "\n"
    #     return string

    def set_points_load(self, points_list, load_magnitude, load_vector, radius, subcontacts_per_point):
        magnitude_per_point = load_magnitude / subcontacts_per_point
        for point in points_list:
            load_direction = normalize_vector(load_vector)
            load = scale_vector(load_direction, magnitude_per_point)
            string = (
                "block gridpoint apply force-x "
                + str(load[0])
                + "force-y "
                + str(load[1])
                + "block gridpoint force-z "
                + str(load[2])
                + " range sphere c "
                + str(point[0])
                + " "
                + str(point[1])
                + " "
                + str(point[2])
                + " r "
                + str(radius)
                + "\n"
            )
            # string += "block gridpoint force-y " + str(load[1]) + " range sphere c " + str(point[0]) + " " + str(point[1]) + " " + str(point[2]) + " r " + str(radius) + "\n"
            # string += "block gridpoint force-z " + str(load[2]) + " range sphere c " + str(point[0]) + " " + str(point[1]) + " " + str(point[2]) + " r " + str(radius) + "\n"
        return string

    def set_load_analysis(
        self,
        load_string,
        total_load,
        load_magnitude_per_step,
        number_of_cycles=35000,
        load_capacity=False,
        solver_ratio=0.00001,
    ):

        if not os.path.join(self.working_path, "grav_state.txt"):
            raise ValueError("Missing gravity file: compute gravity first")

        main_string = ";" + time.strftime("%d/%m/%Y") + " " + time.strftime("%H:%M:%S")
        main_string += 2 * "\n"
        main_string += self.restore_analysis("grav")
        main_string += self.set_damping_global()
        main_string += 2 * "\n"
        main_string += self.blocks_output()
        main_string += self.contacts_output() + "\n"

        load_steps = int(total_load / load_magnitude_per_step)
        if load_capacity:
            load_steps = 10000
        for step in range(load_steps):
            step_name = (
                "Load_step"
                + "_"
                + str(step + 1)
                + "_load_magnitude_"
                + str((step + 1) * load_magnitude_per_step)
                + " N"
            )
            main_string += ";===========================================================================" + "\n"
            main_string += "; " + str(step_name) + "\n"
            main_string += ";===========================================================================" + "\n"
            main_string += load_string
            main_string += "model cycle " + str(number_of_cycles) + "\n"
            main_string += "\n"
            main_string += self.save_blocks_output(step_name)
            step_name_contact = step_name + "_contacts"
            main_string += self.save_contacts_output(step_name_contact)
            main_string += self.save_analysis(step_name)
            main_string += self.check_and_exit(solver_ratio)
            main_string += "\n"
            main_string += ";exit()"
            output_path = self.working_path
            filename = "load.dat"
            with open(os.path.join(output_path, filename), "w") as file:
                file.write(main_string)
        return filename

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
            for vkey in self.blocks[region].mesh.vertices():
                # for vkey in self.elementlist[region].geometry.vertices():
                xyz = self.blocks[region].mesh.vertex_coordinates(vkey)
                gkey = self.geometric_key(xyz)
                v_index = block_gkey_index[gkey]
                block_map[region][vkey] = v_index
        return block_map

    def update_blocks(self, step_dict, mapping_dict):
        for index, block_element in enumerate(self.blocks):
            for vkey, attr in block_element.mesh.vertices(True):
                vertex_3dec = mapping_dict[index][vkey]
                xyz = step_dict[index]["vertices"][vertex_3dec]
                attr["x"] = xyz[0]
                attr["y"] = xyz[1]
                attr["z"] = xyz[2]

                if not block_element.is_support:
                    unbal_force_ratio = norm_vector(step_dict[index]["force"]) / (step_dict[index]["mass"] * 9.806)
                    block_element.unbalanced_force_ratio = unbal_force_ratio
                    if unbal_force_ratio <= 0.001:
                        block_element.color_equilibrium = Color.from_rgb255(190, 190, 190)
                    elif unbal_force_ratio > 0.001 and unbal_force_ratio <= 0.005:
                        block_element.color_equilibrium = Color.from_rgb255(255, 230, 231)
                    elif unbal_force_ratio > 0.005 and unbal_force_ratio <= 0.01:
                        block_element.color_equilibrium = Color.from_rgb255(253, 204, 207)
                    elif unbal_force_ratio > 0.01 and unbal_force_ratio <= 0.05:
                        block_element.color_equilibrium = Color.from_rgb255(250, 179, 183)
                    elif unbal_force_ratio > 0.05 and unbal_force_ratio <= 0.1:
                        block_element.color_equilibrium = Color.from_rgb255(245, 153, 159)
                    elif unbal_force_ratio > 0.1 and unbal_force_ratio <= 0.5:
                        block_element.color_equilibrium = Color.from_rgb255(239, 126, 136)
                    elif unbal_force_ratio > 0.5 and unbal_force_ratio <= 1:
                        block_element.color_equilibrium = Color.from_rgb255(231, 98, 113)
                    elif unbal_force_ratio > 1:
                        block_element.color_equilibrium = Color.from_rgb255(222, 66, 91)

    # =============================================================================
    # get and process CONTACT data from 3dec
    # =============================================================================
    def from_3dec_contacts(self, filename, precision="3f"):
        from compas_3dec.datastructure.interaction_3dec import Interaction3dec

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
            contact_position = contact["position"]
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
                    # output_3dec_per_vertex[position]["normal_displacement"] = [
                    #     x + y
                    #     for x, y in zip(output_3dec_per_vertex[position]["normal_displacement"], normal_displacement)
                    # ]
                    # output_3dec_per_vertex[position]["shear_displacement"] = [
                    #     x + y
                    #     for x, y in zip(output_3dec_per_vertex[position]["shear_displacement"], shear_displacement)
                    # ]
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
                    s1 = 0
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
                for point in points:
                    gkey = self.geometric_key(point, precision)
                    output_list.append(output_3dec_per_vertex[gkey])

            elif len(points) == 2:
                contact_geometry = Line(points[0], points[1])
                output_list = output_3dec_per_vertex.values()
            else:
                # contact_geometry = Point(points[0])
                # contact_geometry = "no contact"
                output_list = output_3dec_per_vertex.values()

            contact_type = contact["type"]
            if contact_type == 0:
                type = "null"
            elif contact_type == 1:
                type = "face-face"
            elif contact_type == 2:
                type = "face-edge"
            elif contact_type == 3:
                type = "face-vertex"
            elif contact_type == 4:
                type = "edge-edge"
            elif contact_type == 5:
                type = "edge-vertex"
            elif contact_type == 6:
                type = "vertex-vertex"
            elif contact_type == 7:
                type = "joined"

            interaction = Interaction3dec(
                type=type,
                normal=contact_normal,
                position=contact_position,
                neighbours=neighbours,
                contact_geometry=contact_geometry,
                forces_per_vertices=output_list,
                forces_per_contact=output_3dec_per_contact,
            )
            self.add_interaction(interaction)
        return output_3dec_per_vertex

    def support_resultants(self, scale_factor):
        from compas.geometry import scale_vector

        resultants = []
        magnitudes = []
        components = []
        for block in self.blocks:
            if block.is_support:
                id = block.index
                for interaction in self.interactions:
                    if id in interaction.neighbours:
                        resultant_force = Vector(*interaction.forces_per_contact["resultant_force"])
                        scaled = scale_vector(resultant_force, scale_factor)
                        resultant_point = Vector(*interaction.forces_per_contact["resultant_point"])
                        resultant = Vector.sum_vectors([resultant_point, scaled])
                        resultant_line = Line(Point(*resultant_point), Point(*resultant))
                        resultants.append(resultant_line)
                        magnitudes.append(str(round(resultant_force.length, 3)) + " kN")
                        comps = [round(resultant_force.x, 3), round(resultant_force.y, 3), round(resultant_force.z, 3)]
                        components.append(comps)
        return resultants, magnitudes, components

    def check_resultant_points(self):
        polygons = []
        resultant_points = []
        points_out = []
        points_not_polygon = []
        for interaction in self.interactions:
            geometry = interaction.contact_geometry
            if isinstance(geometry, Polygon):
                polygons.append(geometry.copy())
                normal = geometry.normal
                centroid = geometry.centroid
                plane = Plane(centroid, normal)
                frame = Frame.from_plane(plane)
                projection = Transformation.from_frame_to_frame(frame, Frame.worldXY())
                geometry.transform(projection)
                point = Point(*interaction.forces_per_contact["resultant_point"])
                contact_point = point.copy()
                point.transform(projection)
                if point.in_polygon(geometry):
                    resultant_points.append(contact_point)
                else:
                    print(contact_point, " is outside")
                    points_out.append(contact_point)
            else:
                print(
                    "The interface is not a polygon",
                    " contact point " + str(interaction.forces_per_contact["resultant_point"]),
                )
                points_not_polygon.append(interaction.forces_per_contact["resultant_point"])

        return polygons, resultant_points, points_out, points_not_polygon



    # =============================================================================
    # displacement.dat
    # =============================================================================

    def get_model_timestep(self):
        with open(os.path.join(self.working_path, "grav_state.txt"), "r") as fo:
            for line in fo:
                line = line.strip()
                if not line:
                    continue
                parts = line.split()
                if not len(parts):
                    continue
                if parts[0] == "timestep":
                    timestep = float(parts[2])
        return timestep

    def set_block_displacement(self, region=0, displacement_direction=[0, 0, -1], displ_magnitude_per_step=0.001):
        displacement_direction = normalize_vector(displacement_direction)
        single_displacement_vector = scale_vector(displacement_direction, displ_magnitude_per_step)
        header = "block apply velocity-x " + str(single_displacement_vector[0]) + " range region " + str(region) + "\n"
        header += "block apply velocity-y " + str(single_displacement_vector[1]) + " range region " + str(region) + "\n"
        header += "block apply velocity-z " + str(single_displacement_vector[2]) + " range region " + str(region) + "\n"

        equilibrium = "block apply velocity-x 0.0 range region " + str(region) + "\n"
        equilibrium += "block apply velocity-y 0.0 range region " + str(region) + "\n"
        equilibrium += "block apply velocity-z 0.0 range region " + str(region) + "\n"

        displacement_data = [header, equilibrium]
        return [displacement_data]

    def set_blocks_displacement(self, regions, displacement_direction=[0, 0, -1], displ_magnitude_per_step=0.001):
        displacement_direction = normalize_vector(displacement_direction)
        single_displacement_vector = scale_vector(displacement_direction, displ_magnitude_per_step)
        regions_str = " ".join(str(r) for r in regions)
        header = "block apply velocity-x " + str(single_displacement_vector[0]) + " range region " + regions_str + "\n"
        header += "block apply velocity-y " + str(single_displacement_vector[1]) + " range region " + regions_str + "\n"
        header += "block apply velocity-z " + str(single_displacement_vector[2]) + " range region " + regions_str + "\n"

        equilibrium = "block apply velocity-x 0.0 range region " + regions_str + "\n"
        equilibrium += "block apply velocity-y 0.0 range region " + regions_str + "\n"
        equilibrium += "block apply velocity-z 0.0 range region " + regions_str + "\n"

        displacement_data = [header, equilibrium]
        return displacement_data

    def set_displacement_analysis(
        self,
        displacements_list,
        total_displacement=0.0,
        displ_magnitude_per_step=0.001,
        solver_ratio=0.00001,
        solver_time=3,
        displacement_capacity=False,
    ):
        # get the model timestep calculated by 3DEC from the gravity file
        timestep = self.get_model_timestep()
        # number of solver cycles to reach the total displacement
        number_of_cycles = int(displ_magnitude_per_step / (displ_magnitude_per_step * timestep))

        if not os.path.join(self.working_path, "grav_state.txt"):
            raise ValueError("Missing gravity file: compute gravity first")

        main_string = ";" + time.strftime("%d/%m/%Y") + " " + time.strftime("%H:%M:%S")
        main_string += 2 * "\n"
        main_string += self.restore_analysis("grav")
        main_string += self.set_damping_local()
        main_string += 2 * "\n"
        main_string += self.blocks_output()
        main_string += self.contacts_output() + "\n"

        displacement_steps = int(total_displacement / displ_magnitude_per_step)
        if displacement_capacity:
            displacement_steps = 10000
        for step in range(displacement_steps):
            step_name = (
                "Displacement_step"
                + "_"
                + str(step + 1)
                + "_distance_"
                + str((step + 1) * displ_magnitude_per_step)
                + "m"
            )
            main_string += ";===========================================================================" + "\n"
            main_string += "; " + str(step_name) + "\n"
            main_string += ";===========================================================================" + "\n"

            for displacement in displacements_list:
                main_string += displacement[0]
            main_string += "model cycle " + str(number_of_cycles) + "\n"
            main_string += "\n"
            main_string += ";===========================================================================" + "\n"
            main_string += "; Equilibrium calculation" + "\n"
            main_string += ";===========================================================================" + "\n"
            for displacement in displacements_list:
                main_string += displacement[1]
            main_string += "model solve unbalanced-maximum {} time".format(solver_ratio) + " " + str(solver_time) + "\n"
            main_string += self.save_blocks_output(step_name)
            step_name_contact = step_name + "_contacts"
            main_string += self.save_contacts_output(step_name_contact)
            main_string += self.save_analysis(step_name)
            main_string += self.check_and_exit(solver_ratio)
            main_string += "\n"
            main_string += "exit()"

            output_path = self.working_path
            filename = "displacement.dat"
            with open(os.path.join(output_path, filename), "w") as file:
                file.write(main_string)
        return filename

    # =============================================================================
    # utilities
    # =============================================================================

    def check_and_exit(self, solve_ratio):

        check_and_exit = """
;===========================================================================
; check equilibrium
;===========================================================================
fish define check_and_exit
    local ratio = mech.solve('ratio-local')
    if ratio > {} then
        system.command('exit')
    endif
end
@check_and_exit
    """.format(
            solve_ratio
        )
        return check_and_exit

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

    # =============================================================================
    # FISH output functions
    # =============================================================================
    def blocks_output(self):
        """FISH function: get blocks data from 3DEC analysis:

        Returns
        -------
        per block:
            region n in 3DEC
                int
            centroid
                x,y,z (precision = 18)
            mass
                float [Kg]
            volume
                float [mc]
            out of balance force
                fx,fy,fz [N]
            moments
                mx,my,mz [Nm]
            loads
                lx,ly,lz [N]
            velocity
                (vx,vy,vz) [m/s]
            list of vertices (coordinates)
                x,y,z (precision = 18)
        """

        blocks_output = """

;===========================================================================
; get blocks data
;===========================================================================
fish define blocks_output
    ii = io.out('solve ratio = '+' '+string(mech.solve('ratio-local')))
    ii = io.out('timestep = '+' '+string(mech.timestep))
    ii=io.out(' centr - result - veloc')
    ic = block.contact.head
    loop foreach ib block.list
        bid = block.id(ib)
        br=block.region(ib)
    ii=io.out('block '+string(bid))
    ii=io.out('region '+string(br))
    ii=io.out('centroid'+' '+'='+' '+string(block.pos.x(ib))+','+string(block.pos.y(ib))+','+string(block.pos.z(ib))+' '+string(br))
    ii=io.out('mass '+' '+string(block.mass(ib)))
    ii=io.out('volume '+' '+string(block.vol(ib)))
    vel=block.vel(ib)
    rx=block.force.unbal.x(ib)
    ry=block.force.unbal.y(ib)
    rz=block.force.unbal.z(ib)
    lx=block.force.app.x(ib)
    ly=block.force.app.y(ib)
    lz=block.force.app.z(ib)
    ; if there is gravity, the block weight should be added
    rz=block.force.unbal.z(ib)+block.mass(ib)*global.gravity.z
    ii=io.out('forces'+' '+'='+' '+string(rx)+','+string(ry)+','+string(rz)+' '+string(br))
    ii=io.out('moment'+' '+'='+' '+string(block.moment.x(ib))+','+string(block.moment.y(ib))+','+string(block.moment.z(ib))+' '+string(br))
    ii=io.out('loads'+' '+'='+' '+string(lx)+','+string(ly)+','+string(lz)+' '+string(br))
    ii=io.out('velocity'+' '+'='+' '+string(vel)+' '+string(br))
    loop foreach vi block.gplist(ib)
        ii = io.out('vertex'+' '+'='+' '+string(block.gp.pos(vi))+' '+string(block.region(block.gp.hostblock(vi))))
        vi = block.gp.next(vi)
    endloop
    ib = block.next(ib)
    endloop
end
    """

        return blocks_output

    def save_blocks_output(self, state):
        save_blocks_output = """
;===========================================================================
; save blocks output
;===========================================================================
log on
log-file '{}.txt'
@blocks_output
log off
    """.format(
            state
        )
        return save_blocks_output

    def contacts_output(self):
        """FISH function: get contacts data from 3DEC analysis:

        Returns
        -------

        """
        contacts_output = """
;===========================================================================
; get contacts data
;===========================================================================
fish define contacts_output
loop foreach ic block.contact.list()
ii=io.out('contact'+' '+'='+' '+string(ic)+' '+string(block.contact.type(ic))+' '+string(block.region(block.contact.b1(ic)))+' '+string(block.region(block.contact.b2(ic)))+' '+string(block.contact.pos(ic))+' '+string(block.contact.normal(ic)))
    loop foreach si block.contact.subcontactlist(ic)
        ii=io.out('subcontact'+' '+'='+' '+string(block.subcontact.pos(si))+' '+string(block.subcontact.force.norm(si))+' '+string(block.subcontact.force.shear(si))+' '+string(si)+' '+string(block.subcontact.disp.norm(si))+' '+string(block.subcontact.disp.shear(si))+' '+string(block.subcontact.stress.norm(si))+' '+string(block.subcontact.stress.shear(si))+' '+string(block.subcontact.area(si)))
        fi = block.subcontact.face(si)
;        if fi then
;            fo = block.face.bface(fi)
;            ii = io.out('face centroid'+' '+'='+' '+string(block.face.pos(fo)))
;        endif
        si = block.subcontact.next(si)
    endloop
ic = block.contact.next(ic)
endloop
end

    """
        return contacts_output

    def save_contacts_output(self, state):
        save_contacts_output = """
;===========================================================================
; save contacts output
;===========================================================================
log on
log-file '{}.txt'
@contacts_output
log off
    """.format(
            state
        )
        return save_contacts_output

    # =============================================================================
    # analysis utilities
    # =============================================================================
    def save_analysis(self, stage):
        """
        Stages:     init
                    grav
                    step
        """
        save_analysis = """
;===========================================================================
; save analysis
;===========================================================================
model save "./{}.sav" compress
""".format(
            stage
        )
        return save_analysis

    def restore_analysis(self, stage):
        """
        Stages:     init
                    grav
                    step
        """
        restore_analysis = """
;===========================================================================
; restore analysis
;===========================================================================
model restore "./{}.sav"
""".format(
            stage
        )
        return restore_analysis

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

    def _check_and_delete_gravity_files(self, current_directory):
        # Get the current working directory
        # current_directory = os.getcwd()
        print(f"Checking in the current directory: {current_directory}")

        # List of files to check and potentially delete
        files_to_check = ["init_state.txt", "grav_state.txt", "contact_grav.txt"]

        # Iterate through each file in the list
        for file_name in files_to_check:
            # Construct the full path to the file
            full_path = os.path.join(current_directory, file_name)

            # Check if the file exists
            if os.path.exists(full_path):
                # If the file exists, delete it
                os.remove(full_path)
                print(f"Deleted {file_name}")
            else:
                # If the file does not exist, print a message
                print(f"{file_name} does not exist in the current directory and was not deleted")

    # =============================================================================
    # damping
    # =============================================================================
    # refer to this link for documentation:
    # https://docs.itascacg.com/3dec700/3dec/block/doc/manual/block_manual/block_commands/block/cmd_block.mechanical.html#block.mechanical

    def set_damping_global(self, fac=False, f1=None, f2=None):
        header = "block mech damping global"

        if fac:
            header = "block mech damping global" + " " + str(fac) + " " + str(f1) + " " + str(f2)
        return header

    def set_damping_local(self, custom=False, f=None):
        header = "block mech damping local"

        if custom:
            header = "block mech damping local" + " " + str(f)
        return header

    def set_damping_contact(self, damping_value):
        pass

    def set_damping_combined(self, damping_value):
        pass

    def set_damping_maxwell(self, damping_value):
        pass

    def set_damping_rayleigh(self, f1, f2, keyword):
        """This form of the command is normally used for dynamic calculations when a
        certain fraction of critical damping is required over a given frequency range.
        This type of damping is known as Rayleigh damping, where f1 = the fraction of
        critical damping operating at the center frequency of f2. See below for further
        discussion.
        keywords:
            mass = Restrict the damping to mass-proportional only.
            stiffness = Restrict the damping to stiffness-proportional only.
        """
        header = "block mech damping rayleigh" + " " + str(f1) + " " + str(f2) + " " + str(keyword)
        return header
