from operator import eq
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
    """Class representing a 3DEC problem encapsulating hierarchically organized elements and interactions.

    Attributes
    ----------
    input : str, optional
        Input data for the problem.
    groups : list
        Groups of elements in the model.
    blocks : list
        Blocks representing geometry.
    rigid_interactions : list
        Rigid interactions between blocks.
    compounds : list
        Compound structures derived from rigid interactions.
    materials : list
        Materials assigned to the model.
    contact_properties : list
        Properties defining contact behavior.
    working_path : str
        Path to working directory.
    interactions : list
        Interactions between elements.
    boundary_conditions : list
        Boundary conditions of the model.
    executable_path : str
        Path to the 3DEC executable.
    block_map : dict
        Mapping of blocks.
    name : str
        Name of the problem.

    Notes
    -----
    - Model elements are structured in groups, blocks, and compounds.
    - Interactions and hierarchical relationships are independent.
    - The interactions define contact mechanics, while hierarchy defines organization.
    """

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
        boundary_conditions=None,
        executable_path='"C:\\Program Files\\Itasca\\3DEC700\\exe64\\3dec700_console.exe"',
        block_map=None,
        name=None,
    ):
        """
        Initializes a Problem3dec object.

        Parameters
        ----------
        input : str, optional
            Input data for the problem.
        groups : list, optional
            List of groups.
        blocks : list, optional
            List of blocks.
        rigid_interactions : list, optional
            List of rigid interactions.
        compounds : list, optional
            List of compounds.
        materials : list, optional
            List of materials.
        contact_properties : list, optional
            List of contact properties.
        working_path : str, optional
            Working directory path.
        interactions : list, optional
            List of interactions.
        boundary_conditions : list, optional
            List of boundary conditions.
        executable_path : str, optional
            Path to the 3DEC executable.
        block_map : dict, optional
            Mapping of blocks.
        name : str, optional
            Name of the problem.
        """
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
        self.boundary_conditions = boundary_conditions if boundary_conditions is not None else []
        self.block_map = block_map if block_map is not None else {}
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
            "boundary_conditions": [boundary_condition.__data__ for boundary_condition in self.boundary_conditions],
            "block_map": self.block_map,
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
        from .boundary_condition import BoundaryCondition

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
            boundary_conditions=[
                BoundaryCondition.__from_data__(boundary_condition)
                for boundary_condition in data["boundary_conditions"]
            ],
            working_path=data["working_path"],
            executable_path=data["executable_path"],
            name=data["name"],
            block_map=data["block_map"],
            compounds=data["compounds"],
        )
        return problem

    def __str__(self):
        blocks_str = "\n".join(str(block) for block in self.blocks)
        groups_str = "\n".join(str(group) for group in self.groups)
        materials_str = "\n".join(str(material) for material in self.materials)
        interactions_str = "\n".join(str(interaction) for interaction in self.interactions)
        return f"Blocks:\n{blocks_str}\nGroups:\n{groups_str}\nMaterials:\n{materials_str}\nInteractions:\n{interactions_str}"

    @classmethod
    def from_blockmodel(cls, blockmodel, working_path=None):
        """
        Create a new Problem3dec instance from a compas_dem BlockModel.

        Parameters
        ----------
        blockmodel : compas_dem.models.BlockModel
            The block model containing block elements to be converted.
        working_path : str, optional
            The working directory for the new Problem3dec instance. If not provided,
            the default path logic in the constructor will be used.

        Returns
        -------
        Problem3dec
            A new Problem3dec object populated with blocks from the blockmodel.

        Notes
        -----
        - Each block element from the blockmodel is converted to a Block and added to the Problem3dec instance.
        - The `is_support` attribute is set for blocks marked as support in the blockmodel.
        - The working path can be set explicitly for consistent file output behavior, especially in environments like Rhino.

        Examples
        --------
        >>> from compas_3dec.datastructure.problem_3dec import Problem3dec
        >>> from compas_dem.models import BlockModel
        >>> blockmodel = BlockModel.from_json('path/to/blockmodel.json')
        >>> problem = Problem3dec.from_blockmodel(blockmodel, working_path='C:/my/project')
        """
        from .block import Block
        from compas_dem.models import BlockModel

        problem = cls(working_path=working_path)
        blockmodel: BlockModel
        for blockelement in blockmodel.elements():
            block = Block(blockelement.graphnode, mesh=blockelement._geometry, name=blockelement.name)
            problem.blocks.append(block)
            if blockelement.is_support:
                block.is_support = True
        return problem

    def add_group(self, group):
        """
        Add a group to the Problem3dec instance.

        Parameters
        ----------
        group : Group
            The group object to be added.

        Raises
        ------
        ValueError
            If a group with the same name already exists.

        Examples
        --------
        >>> problem = Problem3dec()
        >>> group = Group(name="Supports")
        >>> problem.add_group(group)
        """
        if group.name in [g.name for g in self.groups]:
            raise ValueError(f"Group name '{group.name}' already exists.")
        self.groups.append(group)
        return True

    def get_group_by_name(self, name):
        """
        Retrieve a group from the Problem3dec instance by its name.

        Parameters
        ----------
        name : str
            The name of the group to retrieve.

        Returns
        -------
        Group or None
            The group object with the specified name, or None if no such group exists.

        Raises
        ------
        TypeError
            If the provided name is not a string.

        Examples
        --------
        >>> problem = Problem3dec()
        >>> group = problem.get_group_by_name("Supports")
        >>> if group:
        ...     print("Group found:", group)
        ... else:
        ...     print("Group not found.")
        """
        if not isinstance(name, str):
            raise TypeError("Group name must be a string.")
        for group in self.groups:
            if group.name.lower() == name.lower():
                return group
        return None

    def add_blocks(self, meshes, support_names=None):
        """
        Add multiple blocks to the Problem3dec instance from a list of meshes.

        Parameters
        ----------
        meshes : list[Mesh]
            A list of compas Mesh objects to be added as blocks.
        support_names : list[str], optional
            List of mesh names that should be marked as supports. Default is ["Supports"].

        Examples
        --------
        >>> problem = Problem3dec()
        >>> meshes = [mesh1, mesh2, mesh3]
        >>> problem.add_blocks(meshes, support_names=["Supports", "Base"])
        """
        from .block import Block

        if support_names is None:
            support_names = ["Supports"]

        for i, mesh in enumerate(meshes):
            block_index = i  # Sequential indices: 0, 1, 2, ...
            block = Block(block_index, mesh, name=mesh.name)
            if block.name in support_names:
                block.is_support = True
            self.blocks.append(block)

    # def add_blocks(self, meshes, support_names=None):
    #     """
    #     Add multiple blocks to the Problem3dec instance from a list of meshes.

    #     Parameters
    #     ----------
    #     meshes : list[Mesh]
    #         A list of compas Mesh objects to be added as blocks.
    #     support_names : list[str], optional
    #         List of mesh names that should be marked as supports. Default is ["Supports"].

    #     Examples
    #     --------
    #     >>> problem = Problem3dec()
    #     >>> meshes = [mesh1, mesh2, mesh3]
    #     >>> problem.add_blocks(meshes, support_names=["Supports", "Base"])
    #     """
    #     from .block import Block

    #     if support_names is None:
    #         support_names = ["Supports"]

    #     for i, mesh in enumerate(meshes):
    #         block_index = len(self.blocks) + i
    #         block = Block(block_index, mesh, name=mesh.name)
    #         if block.name in support_names:
    #             block.is_support = True
    #         self.blocks.append(block)

    def add_material(self, name, E, poisson, rho, group=None):
        """
        Add a material to the Problem3dec instance and optionally assign it to groups.

        Parameters
        ----------
        name : str
            Name of the material.
        E : float
            Young's modulus of the material.
        poisson : float
            Poisson's ratio of the material.
        rho : float
            Density of the material.
        group : list[str], optional
            List of group names to assign this material to. If None, the material is not assigned to any group.

        Returns
        -------
        Material
            The created Material object.

        Raises
        ------
        TypeError
            If group is not a list of strings.

        Notes
        -----
        - The material is appended to the model's materials list.
        - If `group` is provided, the material is assigned to all matching groups by name.

        Examples
        --------
        >>> problem = Problem3dec()
        >>> mat = problem.add_material("Stone", 30e9, 0.2, 2500, group=["Blocks", "Supports"])
        """
        from .material import Material

        material = Material(name, E, poisson, rho, group)
        self.materials.append(material)
        if group:
            if not isinstance(group, (list, tuple)) or not all(isinstance(gr, str) for gr in group):
                raise TypeError("group must be a list of strings.")
            for gr in set(group):
                found = False
                for g in self.groups:
                    if g.name == gr:
                        g.material = material
                        found = True
                if not found:
                    print(f"Warning: Group '{gr}' not found in Problem3dec.groups.")
        return material

    def add_contact_property(self, stiffness, failure_criteria, group=None):
        """
        Add a contact property to the Problem3dec instance and optionally assign it to groups.

        Parameters
        ----------
        stiffness : tuple or list
            The normal and shear stiffness values for the contact property.
        failure_criteria : object
            The failure criteria object (e.g., friction, cohesion) for the contact property.
        group : list[str], optional
            List of group names to assign this contact property to. If None, the contact property is not assigned to any group.

        Returns
        -------
        ContactProperty
            The created ContactProperty object.

        Raises
        ------
        TypeError
            If group is not a list of strings.

        Notes
        -----
        - The contact property is appended to the model's contact_properties list.
        - If `group` is provided, the contact property is assigned to all matching groups by name.

        Examples
        --------
        >>> problem = Problem3dec()
        >>> cp = problem.add_contact_property((1e7, 1e6), failure_criteria, group=["Blocks", "Supports"])
        """
        from .contact_property import ContactProperty

        contact_property = ContactProperty(stiffness, failure_criteria, group)
        self.contact_properties.append(contact_property)
        if group:
            if not isinstance(group, (list, tuple)) or not all(isinstance(gr, str) for gr in group):
                raise TypeError("group must be a list of strings.")
            for gr in set(group):
                found = False
                for g in self.groups:
                    if g.name == gr:
                        g.contact_property = contact_property
                        found = True
                if not found:
                    print(f"Warning: Group '{gr}' not found in Problem3dec.groups.")
        return contact_property

    def add_rigid_interactions(self, block_lists):
        """
        Add a rigid interaction to the Problem3dec instance.

        Parameters
        ----------
        block_lists : list[list[int]]
            A list of lists, where each inner list contains block indices that form a rigid interaction.

        Returns
        -------
        RigidInteraction
            The created RigidInteraction object.

        Raises
        ------
        TypeError
            If block_lists is not a list of lists of integers.

        Examples
        --------
        >>> problem = Problem3dec()
        >>> problem.add_rigid_interactions([[0, 1, 2], [3, 4]])
        """
        from .rigid_interaction import RigidInteraction

        if not (
            isinstance(block_lists, list)
            and all(isinstance(lst, list) and all(isinstance(i, int) for i in lst) for lst in block_lists)
        ):
            raise TypeError("block_lists must be a list of lists of integers.")

        rigid = RigidInteraction(block_lists)
        self.rigid_interactions.append(rigid)
        return rigid

    def add_interaction(self, interaction_data):
        """
        Add an interaction to the Problem3dec instance.

        Parameters
        ----------
        interaction_data : Interaction3dec or dict
            The interaction object or data to be added to the model.

        Raises
        ------
        TypeError
            If interaction_data is not an Interaction3dec or dict.

        Notes
        -----
        - The interaction is appended to the model's interactions list.
        - Interactions typically represent contact or mechanical relationships between blocks.

        Examples
        --------
        >>> problem = Problem3dec()
        >>> interaction = Interaction3dec(...)
        >>> problem.add_interaction(interaction)
        """
        # Example type check (adjust as needed for your actual interaction type)
        # from .interaction_3dec import Interaction3dec
        # if not isinstance(interaction_data, (Interaction3dec, dict)):
        #     raise TypeError("interaction_data must be an Interaction3dec or dict.")
        self.interactions.append(interaction_data)
        return True

    def make_compounds(self):
        """
        Generate the list of compounds for the Problem3dec instance.

        Compounds are groups of block indices that represent either rigidly joined blocks
        (from rigid interactions) or individual blocks (if no rigid interactions exist).

        Returns
        -------
        list[list[int]]
            A sorted list of compounds, where each compound is a list of block indices.

        Notes
        -----
        - If rigid interactions exist, compounds are extended with those from each RigidInteraction.
        - Blocks not part of any rigid interaction are added as single-block compounds.
        - If no rigid interactions exist, each block is added as a separate compound.
        - The compounds list is sorted by the first block index in each compound.

        Examples
        --------
        >>> problem = Problem3dec()
        >>> problem.make_compounds()
        [[0], [1], [2], [3, 4]]
        """
        self.compounds = []
        if self.rigid_interactions:
            # Collect all indices in rigid compounds for fast lookup
            rigid_indices = set()
            for interaction in self.rigid_interactions:
                self.compounds.extend(interaction.compounds)
                for compound in interaction.compounds:
                    rigid_indices.update(compound)

            # Add blocks that are not part of any interaction
            for block in self.blocks:
                if block.index not in rigid_indices:
                    self.compounds.append([block.index])

            # Sort compounds
            self.compounds = sorted(self.compounds, key=lambda x: x[0])
        else:
            # If no rigid interactions, add each block as a separate compound
            for block in self.blocks:
                self.compounds.append([block.index])

        return list(self.compounds)

    def to_geometry_3dec(self):
        """
        Export the geometry of blocks and supports to a 3DEC-compatible .dat file.

        This method generates the geometry file for 3DEC by processing all block compounds,
        grouping them as "Blocks" or "Supports" (or by their assigned group), and writing
        their mesh data in the required format. Compounds of joined blocks are recognized,
        enabling the creation of Master/Slave compounds in 3DEC.

        Returns
        -------
        str
            The path to the created geometry file.

        Raises
        ------
        ValueError
            If no blocks are available for export.

        Examples
        --------
        >>> problem = Problem3dec()
        >>> geometry_file = problem.to_geometry_3dec()
        >>> print("Geometry exported to:", geometry_file)
        """
        if not self.blocks:
            raise ValueError("No blocks available for geometry export.")

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
        self._overwrite_file(geometry_path, outputs)
        print(f"Geometry exported to {geometry_path}")
        return geometry_path

    def _to_mesh_string_3dec(self, meshes, indices, group, precision=10, unit_scale=1.0):
        """
        Convert a list of compas meshes to a string readable by 3DEC.

        Parameters
        ----------
        meshes : list[compas.datastructures.Mesh]
            List of compas Mesh objects representing block geometry.
        indices : list[int]
            List of indices corresponding to the meshes from model graph nodes.
        group : str
            3DEC block's group name.
        precision : int, optional
            Number of decimal places for vertex coordinates (default is 10).
        unit_scale : float, optional
            Scale factor for vertex coordinates (default is 1.0).

        Returns
        -------
        str
            String containing 3DEC block creation and join commands for the given meshes.

        Raises
        ------
        ValueError
            If the lengths of meshes and indices do not match.

        Examples
        --------
        >>> mesh1, mesh2 = ... # compas Mesh objects
        >>> indices = [0, 1]
        >>> group = "Blocks"
        >>> s = problem._to_mesh_string_3dec([mesh1, mesh2], indices, group, precision=3)
        >>> print(s)
        """
        if len(meshes) != len(indices):
            raise ValueError("meshes and indices must have the same length.")
        block_description = ""
        for i, mesh in enumerate(meshes):
            face_description = ""
            for face in mesh.faces():
                face_description += "face "
                vertices = list(mesh.face_vertices(face))
                vertices.reverse()
                for vertex in vertices:
                    vertex_coordinates = mesh.vertex_coordinates(vertex)
                    face_description += "{0:.{3}f},{1:.{3}f},{2:.{3}f} ".format(
                        vertex_coordinates[0] / unit_scale,
                        vertex_coordinates[1] / unit_scale,
                        vertex_coordinates[2] / unit_scale,
                        precision,
                    )
            sub_block_description = (
                "block create group " + '"' + str(group) + '"' + " poly %s r=%i" % (face_description, indices[i])
            )
            block_description += sub_block_description + "\n"
        if len(meshes) > 1:
            str_indices = [str(num) for num in indices]
            block_description += "block join range region " + " ".join(str_indices) + "\n"
        return block_description

    def _overwrite_file(self, file_path, replace_string):
        """
        Overwrite the file at file_path with replace_string.
        If the file does not exist, it will be created.

        Parameters
        ----------
        file_path : str
            Path to the file to overwrite.
        replace_string : str
            Content to write to the file.

        Raises
        ------
        PermissionError
            If the file exists but is not writable.
        """
        # Clean up any unwanted prefix
        file_path = file_path.replace("file:\\", "").replace("file:/", "").replace("file:", "")
        file_path = os.path.abspath(file_path)

        if os.path.exists(file_path):
            if os.access(file_path, os.W_OK):
                with open(file_path, "w") as f:
                    f.write(replace_string)
            else:
                raise PermissionError(f"File write access denied: {file_path}")
        else:
            with open(file_path, "w") as f:
                f.write(replace_string)

    # =============================================================================
    # setup 3dec analysis
    # =============================================================================
    def set_joint_stiffness_one_material(self, block_height, reduction_factor, block_length=None, material=None):
        """
        Compute the joint stiffness values for a model with one joint material (dry assembled).

        Parameters
        ----------
        block_height : float
            Height of the block.
        reduction_factor : float
            Reduction factor for the joint stiffness.
        block_length : float, optional
            Length of the block. If not provided, only block_height is used.
        material : Material, optional
            Material object with attributes E (Young's modulus) and G (shear modulus).

        Returns
        -------
        tuple (float, float)
            The computed normal (jkn) and shear (jks) joint stiffness values.

        Raises
        ------
        ValueError
            If material is not provided or does not have E and G attributes.

        Notes
        -----
        - If block_length is provided, the stiffness is averaged using both block_height and block_length.
        - The reduction_factor is applied to both normal and shear stiffness.
        - This function assumes dry joints (no mortar).

        Examples
        --------
        >>> mat = Material(E=30e9, G=12e9)
        >>> problem.set_joint_stiffness_one_material(0.2, 10, block_length=0.4, material=mat)
        (750000000.0, 300000000.0)
        """
        if material is None or not hasattr(material, "E") or not hasattr(material, "G"):
            raise ValueError("A valid material with 'E' and 'G' attributes must be provided.")

        E = material.E
        G = material.G

        if block_length is None:
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
        """
        Compute the joint stiffness values for a model with two joint materials (e.g., stone and mortar).

        Parameters
        ----------
        block_height : float
            Height of the block.
        interface_thickness : float
            Thickness of the interface material (e.g., mortar).
        reduction_factor : float
            Reduction factor for the joint stiffness.
        material0_name : str, optional
            Name of the first material (e.g., stone) stored in self.materials.
        material1_name : str, optional
            Name of the second material (e.g., mortar) stored in self.materials.

        Returns
        -------
        tuple (float, float)
            The computed normal (jkn) and shear (jks) joint stiffness values.

        Raises
        ------
        KeyError
            If either material name is not found in self.materials.
        AttributeError
            If the material does not have E or G attributes.

        Notes
        -----
        - The stiffness is computed using the properties of both materials and the interface thickness.
        - The reduction_factor is applied to both normal and shear stiffness.
        - This function assumes two distinct joint materials.

        Examples
        --------
        >>> problem.set_joint_stiffness_two_materials(0.2, 0.01, 10, material0_name="Stone", material1_name="Mortar")
        (jkn_value, jks_value)
        """
        try:
            E1 = self.materials[material0_name].E
            G1 = self.materials[material0_name].G
            E2 = self.materials[material1_name].E
            G2 = self.materials[material1_name].G
        except KeyError as e:
            raise KeyError(f"Material '{e.args[0]}' not found in self.materials.")
        except AttributeError as e:
            raise AttributeError("Material must have 'E' and 'G' attributes.")

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
        """
        Generate the gravity loading sequence for a 3DEC analysis.

        This method creates a string of 3DEC commands to incrementally apply gravity in multiple steps,
        solving for equilibrium at each step, and then performing a final solve with specified criteria.

        Parameters
        ----------
        steps : int, optional
            Number of gravity loading steps (default is 10).
        keyword : str, optional
            Equilibrium criterion keyword for the 3DEC solver (default is "ratio-local").
        ratio : float, optional
            Solver ratio for each gravity step (default is 1e-06).
        time : float, optional
            Solver time for each gravity step (default is 0.02).
        final_ratio : float, optional
            Solver ratio for the final step (default is 1e-06).
        time_final_step : float, optional
            Solver time for the final step (default is 1).

        Returns
        -------
        str
            String containing the gravity loading and solve commands for 3DEC.

        Examples
        --------
        >>> problem = Problem3dec()
        >>> gravity_string = problem.gravity_equilibrium(steps=5)
        >>> print(gravity_string)
        """
        g = -9.806 / steps
        g = round(g, 3)
        text = ";===========================================================================" + "\n"
        text += ";GRAVITY APPLIED IN " + str(steps) + " STEPS\n"
        text += ";===========================================================================" + "\n"
        for i in range(steps):
            gr = g * (i + 1)
            header = ";======================================================================" + "\n"
            header += ";_____GRAVITY_____ step " + str(i + 1) + "\n"
            header += ";======================================================================" + "\n"
            header += "model gravity 0 0 " + str(gr) + "\n"
            header += "model solve " + str(keyword) + " " + str(ratio) + " time " + str(time) + "\n"
            text += header
        text += "model solve " + str(keyword) + " " + str(final_ratio) + " time " + str(time_final_step) + "\n"
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
        if not all(
            hasattr(group, "contact_property")
            and hasattr(group.contact_property, "stiffness")
            and group.contact_property.stiffness
            for group in self.groups
        ):
            raise ValueError("Missing Joint Stiffness values in one or more groups.")

        main_string = f";{time.strftime('%d/%m/%Y')} {time.strftime('%H:%M:%S')}"
        main_string += """
    model new
    model large-strain on
    program call 'geometry.dat'
    block contact generate-subcontacts
    """
        for group in self.groups:
            group_header = (
                f"\nblock property density {group.material.rho} range group '{group.name}'\n"
                f"block contact property stiffness-normal {group.contact_property.stiffness[0]} "
                f"stiffness-shear {group.contact_property.stiffness[1]} "
                f"friction {group.contact_property.failure_criteria.friction} range group '{group.name}'\n"
                f"block contact material-table default property stiffness-normal {group.contact_property.stiffness[0]} "
                f"stiffness-shear {group.contact_property.stiffness[1]}\n"
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

    def _check_and_delete_gravity_files(self, current_directory, verbose=False):
        """
        Check for and delete gravity-related files in the specified directory.

        Parameters
        ----------
        current_directory : str
            The directory in which to check and delete files.
        verbose : bool, optional
            If True, print messages about deleted or missing files (default is False).

        Returns
        -------
        list[str]
            List of deleted file names.

        Raises
        ------
        OSError
            If a file cannot be deleted due to permission issues.
        """
        files_to_check = ["init_state.txt", "grav_state.txt", "contact_grav.txt"]
        deleted_files = []

        for file_name in files_to_check:
            full_path = os.path.join(current_directory, file_name)
            if os.path.exists(full_path):
                try:
                    os.remove(full_path)
                    deleted_files.append(file_name)
                    if verbose:
                        print(f"Deleted {file_name}")
                except OSError as e:
                    print(f"Error deleting {file_name}: {e}")
            else:
                if verbose:
                    print(f"{file_name} does not exist in {current_directory} and was not deleted")
        return deleted_files

    # =============================================================================
    # load.dat
    # =============================================================================
    def _load_box(self, point, precision, decimals=3):
        """
        Create a bounding box range string around a 3D point for use in 3DEC boundary load commands.

        Parameters
        ----------
        point : list[float] or tuple[float]
            3D coordinates (x, y, z) where the load is applied.
        precision : float
            Distance to add and subtract in each direction to create the bounding box.
        decimals : int, optional
            Number of decimal places for output (default is 3).

        Returns
        -------
        str
            A string specifying the range in x, y, z directions for 3DEC.

        Raises
        ------
        ValueError
            If point is not a sequence of three numbers.
        TypeError
            If precision is not a float or int.

        Examples
        --------
        >>> problem._load_box([1.0, 2.0, 3.0], 0.1)
        'range x 0.900 ,1.100 y 1.900 ,2.100 z 2.900 ,3.100'
        """
        if not (isinstance(point, (list, tuple)) and len(point) == 3):
            raise ValueError("point must be a list or tuple of three numbers.")
        if not isinstance(precision, (float, int)):
            raise TypeError("precision must be a float or int.")

        x1 = point[0] - precision
        x2 = point[0] + precision
        y1 = point[1] - precision
        y2 = point[1] + precision
        z1 = point[2] - precision
        z2 = point[2] + precision
        pl = (
            f"range x {x1:.{decimals}f} ,{x2:.{decimals}f} "
            f"y {y1:.{decimals}f} ,{y2:.{decimals}f} "
            f"z {z1:.{decimals}f} ,{z2:.{decimals}f}"
        )
        return pl

    def _load_along_direction(self, pt1, pt2, load, decimals=3):
        """
        Compute the load components along a direction defined by two points for 3DEC boundary load commands.

        Parameters
        ----------
        pt1 : list[float] or tuple[float]
            Starting point of the direction vector (x, y, z).
        pt2 : list[float] or tuple[float]
            Ending point of the direction vector (x, y, z).
        load : float
            Magnitude of the load to be applied along the direction.
        decimals : int, optional
            Number of decimal places for output (default is 3).

        Returns
        -------
        str
            String specifying the x, y, z components of the load for 3DEC.

        Raises
        ------
        ValueError
            If the direction vector is zero-length.

        Examples
        --------
        >>> problem._load_along_direction([0, 0, 0], [1, 0, 0], 100)
        'xload 100.000 yload 0.000 zload 0.000'
        """
        if not (isinstance(pt1, (list, tuple)) and isinstance(pt2, (list, tuple)) and len(pt1) == 3 and len(pt2) == 3):
            raise ValueError("pt1 and pt2 must be lists or tuples of three numbers.")
        if not isinstance(load, (float, int)):
            raise TypeError("load must be a float or int.")

        vec = Vector.from_start_end(pt1, pt2)
        vec = normalize_vector(vec)
        if all(abs(v) < 1e-12 for v in vec):
            raise ValueError("Direction vector cannot be zero-length.")

        load_components = (
            f"xload {vec[0] * load:.{decimals}f} yload {vec[1] * load:.{decimals}f} zload {vec[2] * load:.{decimals}f}"
        )
        return load_components

    def set_point_load(
        self, application_point, direction_point, load_magnitude, radius, subcontacts_per_point, decimals=3
    ):
        """
        Generate a 3DEC command string to apply a point load at a gridpoint in a specified direction.

        Parameters
        ----------
        application_point : list[float] or tuple[float]
            3D coordinates (x, y, z) where the load is applied.
        direction_point : list[float] or tuple[float]
            3D coordinates (x, y, z) defining the direction of the load.
        load_magnitude : float
            Total magnitude of the load to be applied.
        radius : float
            Radius of the sphere around the application point for the range command.
        subcontacts_per_point : int
            Number of subcontacts at the application point (used to divide the load).
        decimals : int, optional
            Number of decimal places for output (default is 3).

        Returns
        -------
        str
            3DEC command string to apply the point load.

        Raises
        ------
        ValueError
            If application_point or direction_point are not sequences of three numbers.
        TypeError
            If load_magnitude, radius, or subcontacts_per_point are not numbers.

        Examples
        --------
        >>> problem.set_point_load([1, 2, 3], [2, 2, 3], 1000, 0.1, 4)
        'block gridpoint apply force-x ... force-y ... force-z ... range sphere c 1 2 3 r 0.1'
        """
        if not (isinstance(application_point, (list, tuple)) and len(application_point) == 3):
            raise ValueError("application_point must be a list or tuple of three numbers.")
        if not (isinstance(direction_point, (list, tuple)) and len(direction_point) == 3):
            raise ValueError("direction_point must be a list or tuple of three numbers.")
        if not isinstance(load_magnitude, (float, int)):
            raise TypeError("load_magnitude must be a float or int.")
        if not isinstance(radius, (float, int)):
            raise TypeError("radius must be a float or int.")
        if not isinstance(subcontacts_per_point, int) or subcontacts_per_point <= 0:
            raise ValueError("subcontacts_per_point must be a positive integer.")

        magnitude_per_point = load_magnitude / subcontacts_per_point
        load_vector = Vector.from_start_end(application_point, direction_point)
        load_vector = normalize_vector(load_vector)
        load_vector = scale_vector(load_vector, magnitude_per_point)
        string = (
            f"block gridpoint apply force-x {load_vector[0]:.{decimals}f} "
            f"force-y {load_vector[1]:.{decimals}f} "
            f"force-z {load_vector[2]:.{decimals}f} "
            f"range sphere c {application_point[0]:.{decimals}f} {application_point[1]:.{decimals}f} {application_point[2]:.{decimals}f} r {radius:.{decimals}f}\n"
        )
        return string

    def set_points_load(self, points_list, load_magnitude, load_vector, radius, subcontacts_per_point, decimals=3):
        """
        Generate 3DEC command strings to apply point loads at multiple gridpoints.

        Returns
        -------
        str
            Combined command string for all points.
        """
        magnitude_per_point = load_magnitude / subcontacts_per_point
        result = ""
        for point in points_list:
            load_direction = normalize_vector(load_vector)
            load = scale_vector(load_direction, magnitude_per_point)
            result += (
                f"block gridpoint apply force-x {load[0]:.{decimals}f} "
                f"force-y {load[1]:.{decimals}f} "
                f"force-z {load[2]:.{decimals}f} "
                f"range sphere c {point[0]:.{decimals}f} {point[1]:.{decimals}f} {point[2]:.{decimals}f} r {radius:.{decimals}f}\n"
            )
        return result

    def set_load_analysis(
        self,
        load_string,
        total_load,
        load_magnitude_per_step,
        number_of_cycles=35000,
        load_capacity=False,
        solver_ratio=0.00001,
    ):
        """
        Generate and export a 3DEC load analysis sequence to a .dat file.

        Parameters
        ----------
        load_string : str
            3DEC command string to apply the load at each step.
        total_load : float
            Total load to be applied over all steps.
        load_magnitude_per_step : float
            Magnitude of load applied in each step.
        number_of_cycles : int, optional
            Number of solver cycles per step (default is 35000).
        load_capacity : bool, optional
            If True, use a fixed large number of steps (default is False).
        solver_ratio : float, optional
            Solver ratio for equilibrium check (default is 0.00001).

        Returns
        -------
        str
            The filename of the created load .dat file.

        Raises
        ------
        ValueError
            If the gravity file is missing or if input values are invalid.
        """
        gravity_file = os.path.join(self.working_path, "grav_state.txt")
        if not os.path.exists(gravity_file):
            raise ValueError("Missing gravity file: compute gravity first")

        if not isinstance(total_load, (float, int)) or total_load <= 0:
            raise ValueError("total_load must be a positive number.")
        if not isinstance(load_magnitude_per_step, (float, int)) or load_magnitude_per_step <= 0:
            raise ValueError("load_magnitude_per_step must be a positive number.")
        if not isinstance(number_of_cycles, int) or number_of_cycles <= 0:
            raise ValueError("number_of_cycles must be a positive integer.")
        if not isinstance(solver_ratio, (float, int)) or solver_ratio <= 0:
            raise ValueError("solver_ratio must be a positive number.")

        main_string = f";{time.strftime('%d/%m/%Y')} {time.strftime('%H:%M:%S')}\n\n"
        main_string += self.restore_analysis("grav")
        main_string += self.set_damping_global()
        main_string += "\n\n"
        main_string += self.blocks_output()
        main_string += self.contacts_output() + "\n"

        load_steps = int(total_load / load_magnitude_per_step)
        if load_capacity:
            load_steps = 10000

        for step in range(load_steps):
            step_load = (step + 1) * load_magnitude_per_step
            step_name = f"Load_step_{step + 1}_load_magnitude_{step_load} N"
            main_string += ";===========================================================================" + "\n"
            main_string += f"; {step_name}\n"
            main_string += ";===========================================================================" + "\n"
            main_string += load_string
            main_string += f"model cycle {number_of_cycles}\n\n"
            main_string += self.save_blocks_output(step_name)
            step_name_contact = step_name + "_contacts"
            main_string += self.save_contacts_output(step_name_contact)
            main_string += self.save_analysis(step_name)
            main_string += self.check_and_exit(solver_ratio)
            main_string += "\n;exit()\n"

        output_path = self.working_path
        filename = "load.dat"
        with open(os.path.join(output_path, filename), "w") as file:
            file.write(main_string)
        return filename

    # =============================================================================
    # run 3dec in the background
    # =============================================================================
    def run(self, sequence=None, suppress_output=True):
        """
        Run the 3DEC executable with the specified command sequence in the working directory.

        Parameters
        ----------
        sequence : list[str], optional
            List of additional command-line arguments or files to pass to the executable.
        suppress_output : bool, optional
            If True, suppress stdout and stderr output (default is True).

        Returns
        -------
        int
            The return code from the subprocess call.
        """
        import subprocess

        if sequence is None:
            sequence = []

        # Remove quotes from executable_path if present
        executable = self.executable_path.strip('"')
        cmd = [executable] + sequence

        # Prevent black shell window on Windows
        creationflags = 0
        if os.name == "nt":
            creationflags = subprocess.CREATE_NO_WINDOW

        if suppress_output:
            result = subprocess.call(
                cmd,
                cwd=self.working_path,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=creationflags,
            )
        else:
            result = subprocess.call(cmd, cwd=self.working_path, creationflags=creationflags)
        return result

    # =============================================================================
    # displacement.dat
    # =============================================================================
    def get_model_timestep(self):
        """
        Retrieve the model timestep value from the 'grav_state.txt' file.

        Returns
        -------
        float
            The timestep value found in the file.

        Raises
        ------
        FileNotFoundError
            If 'grav_state.txt' does not exist in the working directory.
        ValueError
            If the timestep value is not found or cannot be converted to float.

        Examples
        --------
        >>> timestep = problem.get_model_timestep()
        >>> print("Model timestep:", timestep)
        """
        grav_file = os.path.join(self.working_path, "grav_state.txt")
        if not os.path.exists(grav_file):
            raise FileNotFoundError(f"File not found: {grav_file}")

        timestep = None
        with open(grav_file, "r") as fo:
            for line in fo:
                line = line.strip()
                if not line:
                    continue
                parts = line.split()
                if len(parts) >= 3 and parts[0] == "timestep":
                    try:
                        timestep = float(parts[2])
                        break
                    except ValueError:
                        raise ValueError(f"Could not convert timestep value '{parts[2]}' to float.")
        if timestep is None:
            raise ValueError("No timestep value found in grav_state.txt.")
        return timestep

    def set_block_displacement(self, region=0, displacement_direction=[0, 0, -1], displ_magnitude_per_step=0.001):
        """
        Generate 3DEC command strings to apply block displacement in a specified direction for a region.

        Parameters
        ----------
        region : int, optional
            Region index to which the displacement is applied (default is 0).
        displacement_direction : list[float] or tuple[float], optional
            Direction vector for the displacement (default is [0, 0, -1]).
        displ_magnitude_per_step : float, optional
            Magnitude of the displacement per step (default is 0.001).

        Returns
        -------
        list[str]
            List containing the command strings for applying and resetting displacement.

        Raises
        ------
        ValueError
            If displacement_direction is not a sequence of three numbers.
        TypeError
            If displ_magnitude_per_step is not a float or int.

        Examples
        --------
        >>> problem.set_block_displacement(region=1, displacement_direction=[0, 0, -1], displ_magnitude_per_step=0.002)
        [header_string, equilibrium_string]
        """
        if not (isinstance(displacement_direction, (list, tuple)) and len(displacement_direction) == 3):
            raise ValueError("displacement_direction must be a list or tuple of three numbers.")
        if not isinstance(displ_magnitude_per_step, (float, int)):
            raise TypeError("displ_magnitude_per_step must be a float or int.")

        displacement_direction = normalize_vector(displacement_direction)
        single_displacement_vector = scale_vector(displacement_direction, displ_magnitude_per_step)
        header = (
            f"block apply velocity-x {single_displacement_vector[0]} range region {region}\n"
            f"block apply velocity-y {single_displacement_vector[1]} range region {region}\n"
            f"block apply velocity-z {single_displacement_vector[2]} range region {region}\n"
        )

        equilibrium = (
            f"block apply velocity-x 0.0 range region {region}\n"
            f"block apply velocity-y 0.0 range region {region}\n"
            f"block apply velocity-z 0.0 range region {region}\n"
        )

        from compas_3dec.datastructure.boundary_condition import BoundaryCondition

        boundary = BoundaryCondition()
        boundary.region = region
        boundary.type = "displacement"
        boundary.direction = displacement_direction
        boundary.magnitude = displ_magnitude_per_step
        self.boundary_conditions.append(boundary)

        displacement_data = [header, equilibrium]
        return displacement_data

    def set_blocks_displacement(self, regions, displacement_direction=[0, 0, -1], displ_magnitude_per_step=0.001):
        """
        Generate 3DEC command strings to apply block displacement in a specified direction for multiple regions.

        Parameters
        ----------
        regions : list[int]
            List of region indices to which the displacement is applied.
        displacement_direction : list[float] or tuple[float], optional
            Direction vector for the displacement (default is [0, 0, -1]).
        displ_magnitude_per_step : float, optional
            Magnitude of the displacement per step (default is 0.001).

        Returns
        -------
        list[str]
            List containing the command strings for applying and resetting displacement.

        Raises
        ------
        ValueError
            If displacement_direction is not a sequence of three numbers.
        TypeError
            If displ_magnitude_per_step is not a float or int.
            If regions is not a list of integers.

        Examples
        --------
        >>> problem.set_blocks_displacement([0, 1], displacement_direction=[0, 0, -1], displ_magnitude_per_step=0.002)
        [header_string, equilibrium_string]
        """
        if not (isinstance(displacement_direction, (list, tuple)) and len(displacement_direction) == 3):
            raise ValueError("displacement_direction must be a list or tuple of three numbers.")
        if not isinstance(displ_magnitude_per_step, (float, int)):
            raise TypeError("displ_magnitude_per_step must be a float or int.")
        if not (isinstance(regions, (list, tuple)) and all(isinstance(r, int) for r in regions)):
            raise TypeError("regions must be a list or tuple of integers.")

        displacement_direction = normalize_vector(displacement_direction)
        single_displacement_vector = scale_vector(displacement_direction, displ_magnitude_per_step)
        regions_str = " ".join(str(r) for r in regions)

        header = (
            f"block apply velocity-x {single_displacement_vector[0]} range region {regions_str}\n"
            f"block apply velocity-y {single_displacement_vector[1]} range region {regions_str}\n"
            f"block apply velocity-z {single_displacement_vector[2]} range region {regions_str}\n"
        )

        equilibrium = (
            f"block apply velocity-x 0.0 range region {regions_str}\n"
            f"block apply velocity-y 0.0 range region {regions_str}\n"
            f"block apply velocity-z 0.0 range region {regions_str}\n"
        )

        displacement_data = [header, equilibrium]
        return displacement_data

    def set_displacement_analysis(
        self,
        displacements_list,
        init_dict,
        mapping_dict,
        HERE,
        total_displacement=0.0,
        displ_magnitude_per_step=0.001,
        solver_ratio=0.00001,
        solver_time=3,
        displacement_capacity=False,
    ):
        # Get the model timestep calculated by 3DEC from the gravity file
        timestep = self.get_model_timestep()
        # Number of solver cycles to reach the total displacement
        number_of_cycles = int(displ_magnitude_per_step / (displ_magnitude_per_step * timestep))

        if not os.path.join(self.working_path, "grav_state.txt"):
            raise ValueError("Missing gravity file: compute gravity first")

        displacement_list = []
        displacement_steps = int(total_displacement / displ_magnitude_per_step)
        if displacement_capacity:
            displacement_steps = 10000

        filenames = []
        step_names = []
        equilibrium_steps = []
        collapse_step = []
        for step in range(displacement_steps):
            step_name = (
                "Displacement_step"
                + "_"
                + str(step + 1)
                + "_distance_"
                + "{:.4f}".format((step + 1) * displ_magnitude_per_step)
                + "m"
            )
            step_names.append(step_name)
            step_name_contact = step_name + "_contacts"

            # Initialize the main string for the displacement file
            main_string = ";" + time.strftime("%d/%m/%Y") + " " + time.strftime("%H:%M:%S") + "\n\n"

            # Load the gravity output for the first step, or the previous step's output for subsequent steps
            if step == 0:
                main_string += self.restore_analysis("grav")
            else:
                previous_step_name = (
                    "Displacement_step"
                    + "_"
                    + str(step)
                    + "_distance_"
                    + "{:.4f}".format(step * displ_magnitude_per_step)
                    + "m"
                )
                main_string += self.restore_analysis(previous_step_name)

            main_string += self.set_damping_local() + "\n\n"
            main_string += self.blocks_output()
            main_string += self.contacts_output() + "\n"

            main_string += ";===========================================================================" + "\n"
            main_string += "; " + str(step_name) + "\n"
            main_string += ";===========================================================================" + "\n"

            for displacement in displacements_list:
                main_string += displacement[0]
            main_string += "model cycle " + str(number_of_cycles) + "\n\n"

            main_string += ";===========================================================================" + "\n"
            main_string += "; Equilibrium calculation" + "\n"
            main_string += ";===========================================================================" + "\n"
            for displacement in displacements_list:
                main_string += displacement[1]
            main_string += "model solve unbalanced-maximum {} time".format(solver_ratio) + " " + str(solver_time) + "\n"
            main_string += self.save_blocks_output(step_name)
            main_string += self.save_contacts_output(step_name_contact)
            main_string += self.save_analysis(step_name)
            main_string += "\nexit()\n"

            # Save the displacement file with the name of the current step
            output_path = self.working_path
            filename = f"{step_name}.dat"
            filenames.append(filename)
            with open(os.path.join(output_path, filename), "w") as file:
                file.write(main_string)

        for filename, step_name in zip(filenames, step_names):
            step_name_contact = step_name + "_contacts"
            # Run the displacement file
            self.run([filename])

            # =============================================================================
            # Read results blocks and interactions
            # =============================================================================
            result = self.solve_ratio_check(step_name + ".txt")
            # displ_dict = self.from_3dec_blocks(step_name + ".txt")
            if result == "Equilibrium":
                equilibrium_steps.append(step_name)
                continue
            else:
                collapse_step.append(step_name)
                break

        # displ_dict = self.from_3dec_blocks(equilibrium_steps[-1] + ".txt")
        # self.update_blocks(displ_dict, mapping_dict)
        # output_3dec_per_vertex = self.from_3dec_contacts(equilibrium_steps[-1] + "_contacts")
        # FILE_O = os.path.join(HERE, 'problem_' + equilibrium_steps[-1] + '.json')
        # compas.json_dump(self, FILE_O)

        # if result == "Equilibrium":
        #     displacement_list.append(step_name)
        #     self.update_blocks(displ_dict, mapping_dict)
        #     output_3dec_per_vertex = self.from_3dec_contacts(step_name_contact + ".txt")
        #     FILE_O = os.path.join(HERE, 'problem_' + step_name + '.json')
        #     compas.json_dump(self, FILE_O)
        # else:
        #     print("Not in equilibrium at {}".format(step_name))
        #     self.update_blocks(displ_dict, mapping_dict)
        #     output_3dec_per_vertex = self.from_3dec_contacts(step_name_contact + ".txt")
        #     FILE_O = os.path.join(HERE, 'problem_collapse' + step_name + '.json')
        #     compas.json_dump(self, FILE_O)
        #     break

        return filename, displacement_steps, displ_magnitude_per_step, self, equilibrium_steps, collapse_step

    def show_displacement(self, mapping_dict, equilibrium_steps, collapse_step, HERE):
        """
        Update block geometry and export the current state to a JSON file after equilibrium is reached.

        Parameters
        ----------
        mapping_dict : dict
            Mapping between model vertices and 3DEC output vertices.
        equilibrium_steps : list[str]
            List of step names where equilibrium was reached.
        collapse_step : list[str]
            List of step names where collapse occurred (not used in this function).
        HERE : str
            Directory path where the output JSON file will be saved.

        Returns
        -------
        None

        Notes
        -----
        - Updates block geometry using the last equilibrium step's output.
        - Exports the updated Problem3dec object to a JSON file.
        - Also processes contact data for the last equilibrium step.

        Examples
        --------
        >>> problem.show_displacement(mapping_dict, equilibrium_steps, collapse_step, HERE)
        """
        if not equilibrium_steps:
            raise ValueError("No equilibrium steps provided.")
        step_name = equilibrium_steps[-1]
        displ_dict = self.from_3dec_blocks(f"{step_name}.txt")
        self.update_blocks(displ_dict, mapping_dict)
        output_3dec_per_vertex = self.from_3dec_contacts(f"{step_name}_contacts.txt")
        file_o = os.path.join(HERE, f"problem_{step_name}.json")
        compas.json_dump(self, file_o)
        return

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

            block_map[int(region)] = {}
            # block_map[region] = {}
            for vkey in self.blocks[region].mesh.vertices():
                # for vkey in self.elementlist[region].geometry.vertices():
                xyz = self.blocks[region].mesh.vertex_coordinates(vkey)
                gkey = self.geometric_key(xyz)
                v_index = block_gkey_index[gkey]
                block_map[int(region)][int(vkey)] = int(v_index)
                # block_map[region][vkey] = v_index
        self.block_map = block_map
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
        if self.interactions:
            self.interactions = []
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
                    # output_list.append(output_3dec_per_vertex[gkey])

            elif len(points) == 2:
                contact_geometry = Line(points[0], points[1])
                # output_list = output_3dec_per_vertex.values() if output_3dec_per_vertex else None
            else:
                contact_geometry = points if points else None
                # contact_geometry = "no contact"
                # output_list = output_3dec_per_vertex.values() if output_3dec_per_vertex else None

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
        resultant_points = []
        for block in self.blocks:
            if block.is_support:
                id = block.index
                for interaction in self.interactions:
                    if id in interaction.neighbours:
                        if "resultant_force" in interaction.forces_per_contact:
                            resultant_force = Vector(*interaction.forces_per_contact["resultant_force"])
                            # print("Resultant force: ", resultant_force, id)
                            scaled = scale_vector(resultant_force, scale_factor)
                            resultant_point = Vector(*interaction.forces_per_contact["resultant_point"])
                            resultant = Vector.sum_vectors([resultant_point, scaled])
                            resultant_line = Line(Point(*resultant_point), Point(*resultant))
                            resultants.append(resultant_line)
                            magnitudes.append(str(round(resultant_force.length, 1)) + " kN")
                            comps = [
                                round(resultant_force.x, 3),
                                round(resultant_force.y, 3),
                                round(resultant_force.z, 3),
                            ]
                            components.append(comps)
                            resultant_points.append(resultant_point)
        return resultants, magnitudes, components, resultant_points

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
                        result = "Equilibrium"
                    else:
                        print("Equilibrium NOT reached")
                        print("solve ratio = " + str(solve_r))
                        result = "Collapse"
        return result

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
