import os
import time
import inspect


class ContactProperty(object):

    def __init__(self, stiffness, failure_criteria):
        self.stiffness = None  # type: tuple[float, float]
        self.failure_criteria = None  # type MohrCoulomb | None


class MohrCoulomb(object):

    def __init__(self,
                 friction=None,  # type: float
                 cohesion=0,  # type: float
                 dilation=0,  # type: float
                 tension=0,  # type: float
                 ):

        self.friction = friction
        self.cohesion = cohesion
        self.dilation = dilation
        self.tension = tension


class Problem3dec(object):
    def __init__(self, input, working_path=None, executable_path='"C:\\Program Files\\Itasca\\3DEC700\\exe64\\3dec700_console.exe"'):
        self.input = input
        self.executable_path = executable_path

        self.working_path = working_path
        
        if not self.working_path:
            caller_frame = inspect.stack()[-1]
            caller_filename = caller_frame.filename
            self.working_path = os.path.dirname(os.path.abspath(caller_filename))

        # self.jkn = None
        # self.jks = None
        # self.friction_angle = None
        # # self.block_material = None
        # # self.support_material = None
        # self.interface_material = None

    @staticmethod
    def from_model(model):
        from compas_3dec.datastructures.conversion import from_model
        input = from_model(model)
        return Problem3dec(input)

    def to_geometry_3dec(self):
        """Create the .dat files of the Blocks and Supports geometry for 3DEC from an
        Assembly_3DEC object. This function recognises compounds of joined blocks (e.g.
        a group of 3D convex meshes joined together forming a concave shape) enabling
        the creation of Master/Slave compounds in 3DEC.
        """

        outputs = ""
        for indices in self.input.compounds:
            name = "Supports" if self.input.is_support[indices[0]] else "Blocks"
            outputs += ";__create " + str(name) + "__" + "\n"

            meshes = []
            for index in indices:
                meshes.append(self.input.meshes[index])

            outputs += self._to_mesh_string_3dec(meshes, indices, name, precision=10)

        # elements = list(self.model.elements())
        # outputs = ""
        # for indices in self.model.graph.connected_nodes():
            
        #     name = "Supports" if elements[indices[0]].is_support else "Blocks"
        #     outputs += ";__create " + str(name) + "__" + "\n"
        #     meshes = []
        #     for index in indices:
        #         meshes.append(elements[index].geometry)
        #     outputs += self._to_mesh_string_3dec(meshes, indices, name, precision=10)
        geometry_path = os.path.join(self.working_path, "geometry.dat")
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

    # =============================================================================
    # setup 3dec analysis
    # =============================================================================
     
    def set_joint_stiffness_one_material(self, block_height, reduction_factor,  block_length=None, material_name=None):
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

        E = self.input.materials[material_name].E
        G = self.input.materials[material_name].G

        if not block_length:
            jkn = E / block_height
            jks = G / block_height
        else:
            jkn = ((E / block_height) + (E / block_length)) / 2
            jks = ((G / block_height) + (G / block_length)) / 2

        jkn = jkn / reduction_factor
        jks = jks / reduction_factor

        return (jkn, jks)

    def set_joint_stiffness_two_materials(self, block_height, interface_thickness, reduction_factor, material0_name=None, material1_name=None
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

        E1 = self.input.materials[material0_name].E
        G1 = self.input.materials[material0_name].G
        E2 = self.input.materials[material1_name].E
        G2 = self.input.materials[material1_name].G

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
                header = ";_____GRAVITY_____" + " " + "step" + " " + str(i + 1) + "\n"
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

    def run_gravity(
        self,
        steps=10,
        keyword="ratio-local",
        ratio=1e-06,
        time_step=0.02,
        final_ratio=1e-05,
        time_final_step=1,
        ):

        self._check_and_delete_gravity_files(self.working_path)
        if not self.jkn or not self.jks:
            raise ValueError("Missing Joint Stiffness values")

        main_string = ";" + time.strftime("%d/%m/%Y") + " " + time.strftime("%H:%M:%S")
        create_header = """
    model new
    model large-strain on
    program call 'geometry.dat'

    block contact generate-subcontacts
    block property density {0} range group 'Supports'
    block contact property stiffness-normal {1} stiffness-shear {2} friction {3}
    block contact material-table default property stiffness-normal {1} stiffness-shear {2}
    block fix range group 'Supports'

    block property density {0} range group 'Blocks'
    block contact generate-subcontacts
    block contact property stiffness-normal {1} stiffness-shear {2} friction {3}
    block contact material-table default property stiffness-normal {1} stiffness-shear {2}
    {4}
    """.format(
            self.model.materials[material_name].density,
            self.jkn,
            self.jks,
            self.friction_angle,
            self.set_damping_global(),
        )
        main_string += create_header
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
        output_path = self.model.working_path
        filename = "gravity.dat"
        with open(os.path.join(output_path, filename), "w") as file:
            file.write(main_string)
        return filename

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


    def set_damping_local(self,  custom = False, f=None):
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

    def gravity(self):
        pass

    # def load(self, load, point, additionals=None):
    #     pass


# class SelfWeight(Problem3dec):
#     def __init__(self, model):
#         self.model = model

#     def run(self):
#         pass
