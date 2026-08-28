from math import sqrt
from uuid import uuid4

from compas.datastructures import Mesh
from compas_3dec.solver.config import ThreeDECBlockMaterial
from compas_3dec.solver.config import ThreeDECContactProperties
from compas_3dec.solver.stages import ThreeDECStage

from .analysis import ThreeDECAnalysis
from .mapping import ThreeDECEntityMap


def _elastic_moduli(material):
    """Return the Young and shear moduli of a material."""
    if material is None:
        raise ValueError("A material is required to calculate joint stiffness.")
    young_modulus = getattr(material, "E", None)
    shear_modulus = getattr(material, "G", None)
    if young_modulus is None or shear_modulus is None:
        raise ValueError("The material must define Young's modulus and Poisson's ratio.")
    return float(young_modulus), float(shear_modulus)


def _positive(value, name):
    """Return a positive float or raise a descriptive error."""
    value = float(value)
    if value <= 0.0:
        raise ValueError("{} must be positive.".format(name))
    return value


def _group_name(name):
    """Validate and return one public 3DEC block-group name."""
    name = str(name).strip()
    if not name:
        raise ValueError("Group names cannot be empty.")
    return name


def _load_options(options):
    """Normalise optional load-stage settings and reject spelling mistakes."""
    options = dict(options)
    values = {
        "ratio": options.pop("equilibrium_ratio", 1e-5),
        "keyword": options.pop("ratio_keyword", "ratio-local"),
        "solve_time": options.pop("solve_time", None),
        "cycles": options.pop("cycles", 15000),
        "save_steps": options.pop("save_steps", True),
        "stop_on_nonconvergence": options.pop("stop_on_nonconvergence", True),
        "damping": options.pop("damping", "global"),
    }
    if options:
        names = ", ".join(sorted(options))
        raise TypeError("Unexpected load option{}: {}.".format("s" if len(options) > 1 else "", names))
    return values


class ThreeDECAnalysisBuilder:
    """Prepare a portable 3DEC analysis from COMPAS DEM or direct input.

    ``from_dem_problem`` reads a complete ``compas_dem`` problem.
    ``from_meshes`` starts a direct definition without requiring
    ``compas_dem``. Both paths produce the same :class:`ThreeDECAnalysis`
    snapshot.
    """

    def __init__(self, name=None, model_id=None, problem_id=None):
        self.name = name or "Direct 3DEC analysis"
        self.model_id = str(model_id or uuid4())
        self.problem_id = str(problem_id or uuid4())
        self._blocks = []
        self._supports = set()
        self._interfaces = []
        self._boundary_conditions = []
        self._contact_properties = None
        self._contact_property_overrides = []
        self._contact_block_pair_overrides = []
        self._groups = {"block"}
        self._stages = []
        self._solver_configuration = {"name": "3DEC", "parameters": {}}
        self._entity_map = None
        self._source = "direct"
        self._start_new_phase = False

    @classmethod
    def from_meshes(cls, meshes, name=None, **kwargs):
        """Create a direct-input builder from block meshes.

        Parameters
        ----------
        meshes : sequence[:class:`compas.datastructures.Mesh`]
            Closed meshes representing 3DEC blocks.
        name : str, optional
            Analysis name.
        **kwargs : dict, optional
            Additional builder constructor arguments.

        Returns
        -------
        :class:`ThreeDECAnalysisBuilder`
            Builder containing the supplied blocks.
        """
        builder = cls(name=name, **kwargs)
        builder.add_blocks(meshes)
        return builder

    @classmethod
    def from_dem_problem(cls, problem):
        """Prepare a builder from a complete ``compas_dem`` problem.

        Parameters
        ----------
        problem : :class:`compas_dem.problem.Problem`
            Problem with a linked block model, boundary conditions, contact
            properties, and solver configuration.

        Returns
        -------
        :class:`ThreeDECAnalysisBuilder`
            Builder populated from the solver-independent problem.
        """
        return cls.from_analysis(ThreeDECAnalysis.from_dem_problem(problem))

    @classmethod
    def from_blockmodel(cls, model):
        """Prepare a builder from a ``compas_dem`` block model.

        A bare block model contributes geometry, materials, supports, and
        interface topology. Problem-level input such as boundary conditions,
        contact properties, and solver configuration must be added through
        the builder before building or solving the analysis.
        """
        builder = cls(name=getattr(model, "name", None), model_id=model.guid)
        builder._source = "compas_dem_model"
        for element in model.elements():
            node = element.graphnode
            if not isinstance(node, int):
                raise TypeError("COMPAS DEM graph node identifiers must be integers; got {!r}.".format(node))
            builder._blocks.append(
                {
                    "node": node,
                    "element_guid": str(element.guid),
                    "region": node,
                    "name": element.name,
                    "geometry": element.modelgeometry.copy(),
                    "material": element.material,
                    "group": ("supports" if bool(getattr(element, "is_support", False)) else "block"),
                    "is_support": bool(getattr(element, "is_support", False)),
                }
            )
            if getattr(element, "is_support", False):
                builder._supports.add(node)
            builder._groups.add(builder._blocks[-1]["group"])

        for edge in model.graph.edges():
            u, v = int(edge[0]), int(edge[1])
            contacts = model.graph.edge_attribute((u, v), name="contacts") or []
            builder._interfaces.append(
                {
                    "edge": [u, v],
                    "regions": [u, v],
                    "contacts": list(contacts),
                }
            )
        return builder

    @classmethod
    def from_analysis(cls, analysis):
        """Prepare a builder from an existing portable analysis snapshot.

        Parameters
        ----------
        analysis : :class:`ThreeDECAnalysis`
            Existing portable analysis.

        Returns
        -------
        :class:`ThreeDECAnalysisBuilder`
            Mutable builder containing a copy of the analysis input.
        """
        if not isinstance(analysis, ThreeDECAnalysis):
            raise TypeError("from_analysis expects a ThreeDECAnalysis.")
        builder = cls(
            name=analysis.name,
            model_id=analysis.model_id,
            problem_id=analysis.problem_id,
        )
        builder._blocks = [dict(block) for block in analysis.blocks]
        builder._supports = set(analysis.supports)
        builder._interfaces = [dict(interface) for interface in analysis.interfaces]
        builder._boundary_conditions = list(analysis.boundary_conditions)
        builder._contact_properties = analysis.contact_properties
        builder._contact_property_overrides = [dict(item) for item in analysis.contact_property_overrides]
        builder._contact_block_pair_overrides = [dict(item) for item in analysis.contact_block_pair_overrides]
        builder._groups = {block.get("group", "block") for block in builder._blocks}
        builder._stages = list(analysis.stages)
        builder._solver_configuration = analysis.solver_configuration
        builder._entity_map = analysis.entity_map
        builder._source = analysis.source
        return builder

    def add_block(
        self,
        mesh,
        node=None,
        name=None,
        material=None,
        support=False,
        group="block",
    ):
        """Add one rigid block.

        Parameters
        ----------
        mesh : :class:`compas.datastructures.Mesh`
            Closed block mesh.
        node : int, optional
            Stable block identifier. The next index is used by default.
        name : str, optional
            Block name.
        material : :class:`ThreeDECBlockMaterial`, optional
            Block material.
        support : bool, optional
            Whether the block is fixed during gravity.
        group : str, optional
            Public 3DEC block group.

        Returns
        -------
        int
            Assigned block identifier.
        """
        if not isinstance(mesh, Mesh):
            raise TypeError("Direct 3DEC blocks must be COMPAS Mesh objects.")
        node = len(self._blocks) if node is None else int(node)
        if any(block["node"] == node for block in self._blocks):
            raise ValueError("Block node {} is already used.".format(node))
        block = {
            "node": node,
            "element_guid": str(uuid4()),
            "region": node,
            "name": name or "block-{}".format(node),
            "geometry": mesh.copy(),
            "material": material,
            "group": _group_name(group),
            "is_support": bool(support),
        }
        self._blocks.append(block)
        self._groups.add(block["group"])
        self._entity_map = None
        if support:
            self._supports.add(node)
        return node

    def add_blocks(self, meshes):
        """Add multiple rigid blocks.

        Parameters
        ----------
        meshes : sequence[:class:`compas.datastructures.Mesh`]
            Closed block meshes.

        Returns
        -------
        list[int]
            Assigned block identifiers.
        """
        return [self.add_block(mesh) for mesh in meshes]

    def start_new_phase(self):
        """Make the next boundary condition start from a new saved state.

        Consecutive compatible calls are synchronised by default. Call this
        between them when the next load or displacement should restore the
        final ``.sav`` file produced by the preceding phase.
        """
        self._start_new_phase = True
        return self

    def add_group(self, name, nodes=None):
        """Add a block group and optionally assign blocks to it."""
        name = _group_name(name)
        self._groups.add(name)
        if nodes is not None:
            self.assign_blocks_to_group(name, nodes)
        return name

    def assign_blocks_to_group(self, name, nodes):
        """Assign each selected block to exactly one group."""
        name = _group_name(name)
        self._groups.add(name)
        for block in self._selected_blocks(nodes):
            block["group"] = name

    def set_material(
        self,
        density,
        young_modulus,
        poisson_ratio,
        nodes=None,
        name=None,
        group=None,
    ):
        """Assign an isotropic material to selected blocks.

        Parameters
        ----------
        density : float
            Mass density in kilograms per cubic metre.
        young_modulus : float
            Young's modulus in pascals.
        poisson_ratio : float
            Poisson's ratio.
        nodes : sequence[int], optional
            Block identifiers. All blocks are selected by default.
        name : str, optional
            Material name.
        group : str, optional
            Select blocks by group instead of by identifier.

        Returns
        -------
        :class:`ThreeDECBlockMaterial`
            Assigned material.
        """
        if nodes is not None and group is not None:
            raise ValueError("Select material blocks by either nodes or group, not both.")
        material = ThreeDECBlockMaterial(
            density=density,
            young_modulus=young_modulus,
            poisson_ratio=poisson_ratio,
            name=name,
        )
        selected = self._blocks_in_group(group) if group is not None else self._selected_blocks(nodes)
        for block in selected:
            block["material"] = material
        return material

    def set_supports(self, nodes):
        """Replace the set of fixed support blocks.

        Parameters
        ----------
        nodes : sequence[int]
            Block identifiers to fix.
        """
        nodes = {int(node) for node in nodes}
        known = {block["node"] for block in self._blocks}
        unknown = sorted(nodes - known)
        if unknown:
            raise ValueError("Unknown direct block nodes: {}.".format(unknown))
        self._supports = nodes
        for block in self._blocks:
            block["is_support"] = block["node"] in nodes

    def add_interface(self, node_a, node_b):
        """Register an expected interface between two blocks.

        Parameters
        ----------
        node_a : int
            First block identifier.
        node_b : int
            Second block identifier.
        """
        node_a, node_b = int(node_a), int(node_b)
        known = {block["node"] for block in self._blocks}
        if node_a not in known or node_b not in known:
            raise ValueError("Both interface nodes must refer to added blocks.")
        edge = [node_a, node_b]
        if edge not in [record["edge"] for record in self._interfaces]:
            self._interfaces.append({"edge": edge, "regions": edge[:], "contacts": []})
            self._entity_map = None

    def set_contact_properties(
        self,
        kn=100e9,
        kt=70e9,
        friction=35.0,
        cohesion=0.0,
        tension=0.0,
        name=None,
    ):
        """Set the default joint properties for all contacts.

        Parameters
        ----------
        kn : float, optional
            Normal joint stiffness in pascals per metre.
        kt : float, optional
            Shear joint stiffness in pascals per metre.
        friction : float, optional
            Friction angle in degrees.
        cohesion : float, optional
            Cohesion in pascals.
        tension : float, optional
            Tensile strength in pascals.
        name : str, optional
            Property-set name.

        Returns
        -------
        :class:`ThreeDECContactProperties`
            Assigned default properties.
        """
        self._contact_properties = ThreeDECContactProperties(
            stiffness_normal=kn,
            stiffness_shear=kt,
            friction=friction,
            cohesion=cohesion,
            tension=tension,
            name=name,
        )
        return self._contact_properties

    def set_contact_properties_between_groups(
        self,
        group_a,
        group_b,
        kn=100e9,
        kt=70e9,
        friction=35.0,
        cohesion=0.0,
        tension=0.0,
        name=None,
    ):
        """Override contact properties where two block groups intersect.

        This direct-input configuration generates both an override for
        existing contacts and a material-table entry for contacts that form
        later during a large-strain calculation.
        """
        if self._source == "compas_dem":
            raise ValueError("Group-intersection contact properties are currently available only for direct or bare-blockmodel analyses.")
        group_a = self._require_group(group_a)
        group_b = self._require_group(group_b)
        if group_a == group_b:
            raise ValueError("Select two distinct block groups.")
        properties = ThreeDECContactProperties(
            stiffness_normal=kn,
            stiffness_shear=kt,
            friction=friction,
            cohesion=cohesion,
            tension=tension,
            name=name,
        )
        pair = tuple(sorted((group_a, group_b)))
        self._contact_property_overrides = [item for item in self._contact_property_overrides if tuple(sorted((item["group_a"], item["group_b"]))) != pair]
        self._contact_property_overrides.append({"group_a": pair[0], "group_b": pair[1], "properties": properties})
        return properties

    def set_contact_properties_between_blocks(
        self,
        node_a,
        node_b,
        kn=100e9,
        kt=70e9,
        friction=35.0,
        cohesion=0.0,
        tension=0.0,
        name=None,
    ):
        """Override contact properties between exactly two blocks.

        The generated 3DEC input assigns reserved identity groups in the
        ``COMPAS_ID`` slot. These internal tags do not change the block's one
        public structural group.
        """
        if self._source == "compas_dem":
            raise ValueError("Block-pair contact properties are currently available only for direct or bare-blockmodel analyses.")
        node_a, node_b = int(node_a), int(node_b)
        if node_a == node_b:
            raise ValueError("Select two distinct block nodes.")
        known = {block["node"] for block in self._blocks}
        unknown = sorted({node_a, node_b} - known)
        if unknown:
            raise ValueError("Unknown direct block nodes: {}.".format(unknown))
        properties = ThreeDECContactProperties(
            stiffness_normal=kn,
            stiffness_shear=kt,
            friction=friction,
            cohesion=cohesion,
            tension=tension,
            name=name,
        )
        pair = tuple(sorted((node_a, node_b)))
        self._contact_block_pair_overrides = [item for item in self._contact_block_pair_overrides if tuple(sorted((item["node_a"], item["node_b"]))) != pair]
        self._contact_block_pair_overrides.append({"node_a": pair[0], "node_b": pair[1], "properties": properties})
        return properties

    @staticmethod
    def calculate_joint_stiffness_one_material(
        material,
        block_height,
        reduction_factor=1.0,
        block_length=None,
    ):
        """Calculate joint stiffness for dry-jointed blocks of one material.

        Parameters
        ----------
        material : :class:`ThreeDECBlockMaterial`
            Block material providing Young's and shear moduli.
        block_height : float
            Representative block height in metres.
        reduction_factor : float, optional
            Divisor applied to both calculated stiffnesses.
        block_length : float, optional
            Representative block length in metres. When provided, stiffness
            contributions based on height and length are averaged.

        Returns
        -------
        tuple[float, float]
            Normal and shear joint stiffness in pascals per metre.
        """
        E, G = _elastic_moduli(material)
        height = _positive(block_height, "block_height")
        reduction = _positive(reduction_factor, "reduction_factor")
        kn = E / height
        kt = G / height
        if block_length is not None:
            length = _positive(block_length, "block_length")
            kn = 0.5 * (kn + E / length)
            kt = 0.5 * (kt + G / length)
        return kn / reduction, kt / reduction

    @staticmethod
    def calculate_joint_stiffness_two_materials(
        block_material,
        interface_material,
        block_height,
        interface_thickness,
        reduction_factor=1.0,
    ):
        """Calculate joint stiffness for blocks with an interface material.

        Parameters
        ----------
        block_material : :class:`ThreeDECBlockMaterial`
            Material of the blocks.
        interface_material : :class:`ThreeDECBlockMaterial`
            Material of the interface, for example mortar.
        block_height : float
            Representative block height in metres.
        interface_thickness : float
            Interface thickness in metres.
        reduction_factor : float, optional
            Divisor applied to both calculated stiffnesses.

        Returns
        -------
        tuple[float, float]
            Normal and shear joint stiffness in pascals per metre.
        """
        E1, G1 = _elastic_moduli(block_material)
        E2, G2 = _elastic_moduli(interface_material)
        height = _positive(block_height, "block_height")
        thickness = _positive(interface_thickness, "interface_thickness")
        reduction = _positive(reduction_factor, "reduction_factor")
        kn = (E1 * E2) / (height * E2 + thickness * E1)
        kt = (G1 * G2) / (height * G2 + thickness * G1)
        return kn / reduction, kt / reduction

    def set_contact_properties_from_material(self, material, block_height, reduction_factor=1.0, block_length=None, **contact_options):
        """Calculate and assign contact properties for one material."""
        kn, kt = self.calculate_joint_stiffness_one_material(
            material=material,
            block_height=block_height,
            reduction_factor=reduction_factor,
            block_length=block_length,
        )
        return self.set_contact_properties(kn=kn, kt=kt, **contact_options)

    def set_contact_properties_from_materials(self, block_material, interface_material, block_height, interface_thickness, reduction_factor=1.0, **contact_options):
        """Calculate and assign contact properties for two materials."""
        kn, kt = self.calculate_joint_stiffness_two_materials(
            block_material=block_material,
            interface_material=interface_material,
            block_height=block_height,
            interface_thickness=interface_thickness,
            reduction_factor=reduction_factor,
        )
        return self.set_contact_properties(kn=kn, kt=kt, **contact_options)

    def add_gravity(
        self,
        g=9.81,
        gravity_steps=10,
        ratio=1e-5,
        ratio_keyword="ratio-local",
        time=1.0,
    ):
        """Add or replace the mandatory first gravity stage.

        Parameters
        ----------
        g : float, optional
            Gravitational acceleration in metres per second squared.
        gravity_steps : int, optional
            Number of gravity ramp increments.
        ratio : float, optional
            Target local equilibrium ratio.
        ratio_keyword : str, optional
            3DEC solve-ratio keyword.
        time : float, optional
            Mechanical time used to ramp gravity.
        """
        g = _positive(g, "g")
        gravity_steps = int(gravity_steps)
        ratio = _positive(ratio, "ratio")
        time = _positive(time, "time")
        if gravity_steps <= 0:
            raise ValueError("gravity_steps must be positive.")
        options = {
            "gravity_steps": gravity_steps,
            "ratio": ratio,
            "ratio_keyword": str(ratio_keyword),
            "time": time,
        }
        self._stages = [stage for stage in self._stages if stage.kind != "gravity"]
        self._stages.insert(
            0,
            ThreeDECStage(
                name="gravity",
                kind="gravity",
                gravity=g,
                options=options,
            ),
        )
        self._solver_configuration["parameters"].update(options)

    def add_point_load(
        self,
        magnitude,
        direction,
        steps,
        point,
        radius=0.01,
        block=None,
        distribution_count=None,
        name=None,
        equilibrium_ratio=1e-5,
        ratio_keyword="ratio-local",
        solve_time=None,
        cycles=15000,
        save_steps=True,
        stop_on_nonconvergence=True,
        damping="global",
    ):
        """Add a stepped concentrated load selected by a spherical range.

        ``magnitude`` is the total global force reached after ``steps``. The
        force direction is normalised. By default the distribution count is
        calculated from the input block vertices inside the sphere. ``cycles``
        is the maximum number of cycles allowed per increment; the solve stops
        earlier when ``equilibrium_ratio`` is reached. ``solve_time`` may add
        an optional mechanical-time limit.
        """
        load = self._point_load(
            kind="sphere",
            magnitude=magnitude,
            direction=direction,
            steps=steps,
            point=point,
            radius=radius,
            block=block,
            distribution_count=distribution_count,
            name=name,
        )
        self._add_load_stage(
            load,
            equilibrium_ratio,
            ratio_keyword,
            solve_time,
            cycles,
            save_steps,
            stop_on_nonconvergence,
            damping,
        )
        return load

    def add_point_loads(self, points, magnitude, direction, steps, radius=0.01, blocks=None, **options):
        """Add the same stepped spherical point load at multiple points."""
        points = list(points)
        if not points:
            raise ValueError("Provide at least one load application point.")
        if blocks is None or isinstance(blocks, (int, str)):
            targets = [blocks] * len(points)
        else:
            targets = list(blocks)
            if len(targets) != len(points):
                raise ValueError("blocks must contain one target per application point.")
        return [
            self.add_point_load(magnitude=magnitude, direction=direction, steps=steps, point=point, radius=radius, block=block, **options) for point, block in zip(points, targets)
        ]

    def add_load_capacity(self, magnitude_increment, direction, point=None, blocks=None, radius=0.01, block=None, distribution_count=None, max_steps=100, name=None, **options):
        """Increase a point or centroid load until equilibrium is lost.

        Exactly one of ``point`` and ``blocks`` must be provided. The former
        uses a spherical gridpoint range; the latter applies the force at each
        selected rigid-block centroid. ``max_steps`` is a safety limit for a
        structure that remains stable throughout the requested range.
        """
        increment = _positive(magnitude_increment, "magnitude_increment")
        maximum = int(max_steps)
        if maximum <= 0:
            raise ValueError("max_steps must be a positive integer.")
        if (point is None) == (blocks is None):
            raise ValueError("Provide exactly one of point or blocks.")
        capacity_options = dict(options)
        capacity_options["save_steps"] = True
        capacity_options["stop_on_nonconvergence"] = True
        if point is not None:
            item = self.add_point_load(
                magnitude=increment * maximum,
                direction=direction,
                steps=maximum,
                point=point,
                radius=radius,
                block=block,
                distribution_count=distribution_count,
                name=name or "point-load capacity",
                **capacity_options,
            )
        else:
            item = self.add_centroid_load(
                magnitude=increment * maximum, direction=direction, steps=maximum, blocks=blocks, name=name or "centroid-load capacity", **capacity_options
            )
        item.update(
            capacity=True,
            capacity_increment=increment,
            capacity_max_steps=maximum,
        )
        return item

    def add_centroid_load(
        self,
        magnitude,
        direction,
        steps,
        blocks,
        name=None,
        equilibrium_ratio=1e-5,
        ratio_keyword="ratio-local",
        solve_time=None,
        cycles=15000,
        save_steps=True,
        stop_on_nonconvergence=True,
        damping="global",
    ):
        """Apply the specified stepped force to every selected block centroid.

        ``cycles`` is a per-increment maximum, not a fixed number that must be
        executed. Equilibrium can stop the solve earlier.
        """
        nodes = [block["node"] for block in self._selected_blocks(blocks)]
        load = self._point_load(
            kind="centroid",
            magnitude=magnitude,
            direction=direction,
            steps=steps,
            blocks=nodes,
            name=name,
        )
        self._add_load_stage(
            load,
            equilibrium_ratio,
            ratio_keyword,
            solve_time,
            cycles,
            save_steps,
            stop_on_nonconvergence,
            damping,
        )
        return load

    def add_face_stress(self, block, face, stress, steps=1, name=None, range_tolerance=None, **options):
        """Apply a stepped global stress tensor to one block face.

        Parameters
        ----------
        block : int
            Block node identifier.
        face : int
            Face key of the block mesh.
        stress : sequence[float]
            ``[xx, yy, zz, xy, yz, zx]`` in Pa. Compression is negative.
        steps : int, optional
            Number of equal stress increments.
        range_tolerance : float, optional
            Expansion of the 3DEC Cartesian face-selection range. By default
            this is derived from the block size.
        """
        item = self._surface_stress(
            block,
            face,
            stress=stress,
            steps=steps,
            name=name,
            range_tolerance=range_tolerance,
        )
        self._add_load_stage(item, collection="surface_loads", **_load_options(options))
        return item

    def add_surface_load(self, block, face, load, steps=1, name=None, range_tolerance=None, **options):
        """Apply a stepped traction vector to one block face.

        ``load`` is a global traction vector in Pa, matching COMPAS DEM's
        ``SurfaceLoad`` contract. A minimum symmetric stress tensor satisfying
        ``stress * face_normal == load`` is generated for 3DEC.
        """
        block_item = self._selected_blocks([block])[0]
        mesh = block_item["geometry"]
        normal = [float(value) for value in mesh.face_normal(face)]
        traction = [float(value) for value in load]
        if len(traction) != 3:
            raise ValueError("Surface load must have three traction components.")
        dot = sum(traction[i] * normal[i] for i in range(3))
        tensor = [[traction[i] * normal[j] + normal[i] * traction[j] - dot * normal[i] * normal[j] for j in range(3)] for i in range(3)]
        stress = [tensor[0][0], tensor[1][1], tensor[2][2], tensor[0][1], tensor[1][2], tensor[2][0]]
        item = self._surface_stress(
            block,
            face,
            stress=stress,
            traction=traction,
            steps=steps,
            name=name,
            range_tolerance=range_tolerance,
        )
        self._add_load_stage(item, collection="surface_loads", **_load_options(options))
        return item

    def add_surface_load_capacity(self, block, face, load_increment, max_steps=100, name=None, range_tolerance=None, **options):
        """Increase a face traction until equilibrium is lost.

        ``load_increment`` is the global traction increment in Pa applied at
        every step. ``max_steps`` prevents an unbounded run if collapse is not
        reached.
        """
        increment = [float(value) for value in load_increment]
        if len(increment) != 3 or sqrt(sum(value * value for value in increment)) <= 1e-30:
            raise ValueError("load_increment must be a nonzero three-component vector.")
        maximum = int(max_steps)
        if maximum <= 0:
            raise ValueError("max_steps must be a positive integer.")
        capacity_options = dict(options)
        capacity_options["save_steps"] = True
        capacity_options["stop_on_nonconvergence"] = True
        item = self.add_surface_load(
            block=block,
            face=face,
            load=[value * maximum for value in increment],
            steps=maximum,
            name=name or "surface-load capacity",
            range_tolerance=range_tolerance,
            **capacity_options,
        )
        item.update(
            capacity=True,
            capacity_increment=increment,
            capacity_max_steps=maximum,
        )
        return item

    def _surface_stress(self, block, face, stress, steps, name=None, traction=None, range_tolerance=None):
        block_item = self._selected_blocks([block])[0]
        mesh = block_item["geometry"]
        if face not in list(mesh.faces()):
            raise ValueError("Unknown face {} for block {}.".format(face, block_item["node"]))
        stress = [float(value) for value in stress]
        if len(stress) != 6:
            raise ValueError("Stress must contain [xx, yy, zz, xy, yz, zx].")
        steps = int(steps)
        if steps <= 0:
            raise ValueError("Load steps must be a positive integer.")
        vertices = [list(mesh.vertex_coordinates(vertex)) for vertex in mesh.face_vertices(face)]
        normal = [float(value) for value in mesh.face_normal(face)]
        if traction is None:
            xx, yy, zz, xy, yz, zx = stress
            traction = [
                xx * normal[0] + xy * normal[1] + zx * normal[2],
                xy * normal[0] + yy * normal[1] + yz * normal[2],
                zx * normal[0] + yz * normal[1] + zz * normal[2],
            ]
        coordinates = list(mesh.vertices_attributes("xyz"))
        size = max(max(row[i] for row in coordinates) - min(row[i] for row in coordinates) for i in range(3))
        tolerance = float(range_tolerance) if range_tolerance is not None else max(size * 1e-6, 1e-9)
        return {
            "kind": "surface_stress",
            "name": name or "face stress",
            "block": block_item["node"],
            "face": face,
            "stress": stress,
            "traction": list(traction),
            "steps": steps,
            "face_vertices": vertices,
            "face_center": list(mesh.face_center(face)),
            "face_normal": normal,
            "face_area": float(mesh.face_area(face)),
            "range_tolerance": tolerance,
        }

    def add_displacement(
        self,
        blocks,
        magnitude,
        direction,
        steps,
        name=None,
        motion_time=1.0,
        source_state="auto",
        equilibrium_ratio=1e-5,
        ratio_keyword="ratio-local",
        equilibrium_time=None,
        equilibrium_cycles=15000,
        save_steps=True,
        stop_on_nonconvergence=True,
        damping="local",
        constrain_other_translations=True,
    ):
        """Prescribe a cumulative rigid-block translation in synchronised steps.

        The displacement phase derives its cycle count from the current 3DEC
        mechanical timestep. Each phase is followed by zero prescribed
        velocity and a separate equilibrium solve before the next increment.
        Call this method repeatedly to prescribe different translations on
        different blocks in the same displacement stage.
        """
        nodes = [block["node"] for block in self._selected_blocks(blocks)]
        magnitude = float(magnitude)
        steps = int(steps)
        motion_time = float(motion_time)
        if magnitude < 0.0:
            raise ValueError("Displacement magnitude must be nonnegative; use direction for its sign.")
        if steps <= 0:
            raise ValueError("Displacement steps must be a positive integer.")
        if motion_time <= 0.0:
            raise ValueError("motion_time must be positive.")
        vector = [float(value) for value in direction]
        if len(vector) != 3:
            raise ValueError("Displacement direction must have three components.")
        length = sqrt(sum(value * value for value in vector))
        if length <= 1e-30:
            raise ValueError("Displacement direction cannot be zero-length.")
        direction = [value / length for value in vector]
        item = {
            "kind": "translation",
            "name": name or "prescribed translation",
            "blocks": nodes,
            "magnitude": magnitude,
            "direction": direction,
            "steps": steps,
            "active_components": [True, True, True] if constrain_other_translations else [abs(value) > 1e-30 for value in direction],
        }
        options = {
            "motion_time": motion_time,
            "source_state": str(source_state),
            "ratio": float(equilibrium_ratio),
            "ratio_keyword": str(ratio_keyword),
            "equilibrium_time": None if equilibrium_time is None else float(equilibrium_time),
            "equilibrium_cycles": None if equilibrium_cycles is None else int(equilibrium_cycles),
            "save_steps": bool(save_steps),
            "stop_on_nonconvergence": bool(stop_on_nonconvergence),
            "damping": str(damping),
        }
        if options["equilibrium_cycles"] is not None and options["equilibrium_cycles"] <= 0:
            raise ValueError("equilibrium_cycles must be positive.")
        if options["equilibrium_time"] is not None and options["equilibrium_time"] <= 0.0:
            raise ValueError("equilibrium_time must be positive.")
        if options["equilibrium_cycles"] is None and options["equilibrium_time"] is None:
            raise ValueError("Provide equilibrium_cycles or equilibrium_time.")
        stage = self._stages[-1] if self._stages and self._stages[-1].kind == "displacements" and not self._start_new_phase else None
        if stage is None:
            index = 1 + sum(stage.kind == "displacements" for stage in self._stages)
            stage = ThreeDECStage(
                name="displacements" if index == 1 else "displacements-{}".format(index),
                kind="displacements",
                displacements=[],
                options=options,
            )
            self._stages.append(stage)
        else:
            stage.options.update(options)
        stage.displacements.append(item)
        self._start_new_phase = False
        return item

    def add_displacement_capacity(self, blocks, magnitude_increment, direction, max_steps=100, name=None, **options):
        """Increase prescribed translation until equilibrium is lost.

        The translation increment is applied, prescribed motion is stopped,
        and equilibrium is checked at every step. ``max_steps`` is the safety
        termination criterion when the structure remains stable.
        """
        increment = _positive(magnitude_increment, "magnitude_increment")
        maximum = int(max_steps)
        if maximum <= 0:
            raise ValueError("max_steps must be a positive integer.")
        capacity_options = dict(options)
        capacity_options["save_steps"] = True
        capacity_options["stop_on_nonconvergence"] = True
        item = self.add_displacement(blocks=blocks, magnitude=increment * maximum, direction=direction, steps=maximum, name=name or "displacement capacity", **capacity_options)
        item.update(
            capacity=True,
            capacity_increment=increment,
            capacity_max_steps=maximum,
        )
        return item

    def _point_load(self, kind, magnitude, direction, steps, **data):
        magnitude = float(magnitude)
        steps = int(steps)
        if magnitude < 0.0:
            raise ValueError("Load magnitude must be nonnegative; use direction for its sign.")
        if steps <= 0:
            raise ValueError("Load steps must be a positive integer.")
        vector = [float(value) for value in direction]
        if len(vector) != 3:
            raise ValueError("Load direction must have three components.")
        length = sqrt(sum(value * value for value in vector))
        if length <= 1e-30:
            raise ValueError("Load direction cannot be zero-length.")
        load = {
            "kind": kind,
            "name": data.pop("name", None) or "{} load".format(kind),
            "magnitude": magnitude,
            "direction": [value / length for value in vector],
            "steps": steps,
        }
        if kind == "sphere":
            point = [float(value) for value in data.pop("point")]
            if len(point) != 3:
                raise ValueError("Load application point must have three coordinates.")
            radius = float(data.pop("radius"))
            count = data.pop("distribution_count")
            if radius <= 0.0:
                raise ValueError("Load radius must be positive.")
            block = data.pop("block")
            if block is not None:
                block = self._selected_blocks([block])[0]["node"]
            if count is None:
                count = self._vertices_in_sphere(point, radius, block)
            count = int(count)
            if count <= 0:
                raise ValueError("The load sphere does not contain a block vertex. Increase radius or correct the point.")
            load.update(point=point, radius=radius, block=block, distribution_count=count)
        else:
            load.update(blocks=list(data.pop("blocks")))
        return load

    def _vertices_in_sphere(self, point, radius, block=None):
        blocks = self._blocks if block is None else self._selected_blocks([block])
        radius_squared = float(radius) ** 2
        return sum(
            1 for item in blocks for vertex in item["geometry"].vertices_attributes("xyz") if sum((float(vertex[i]) - point[i]) ** 2 for i in range(3)) <= radius_squared + 1e-24
        )

    def _add_load_stage(self, load, ratio, keyword, solve_time, cycles, save_steps, stop_on_nonconvergence, damping, collection="point_loads"):
        stage = self._stages[-1] if self._stages and self._stages[-1].kind == "loads" and not self._start_new_phase else None
        options = {
            "ratio": float(ratio),
            "ratio_keyword": str(keyword),
            "solve_time": None if solve_time is None else float(solve_time),
            "cycles": None if cycles is None else int(cycles),
            "save_steps": bool(save_steps),
            "stop_on_nonconvergence": bool(stop_on_nonconvergence),
            "damping": str(damping),
        }
        if options["cycles"] is not None and options["cycles"] <= 0:
            raise ValueError("cycles must be a positive integer.")
        if options["solve_time"] is not None and options["solve_time"] <= 0.0:
            raise ValueError("solve_time must be positive.")
        if options["cycles"] is None and options["solve_time"] is None:
            raise ValueError("Provide solve_time or cycles for load-step equilibrium.")
        if stage is None:
            index = 1 + sum(stage.kind == "loads" for stage in self._stages)
            stage = ThreeDECStage(
                name="loads" if index == 1 else "loads-{}".format(index),
                kind="loads",
                point_loads=[],
                options=options,
            )
            self._stages.append(stage)
        else:
            stage.options.update(options)
        getattr(stage, collection).append(load)
        self._start_new_phase = False

    def build(self):
        """Validate and create a portable analysis snapshot.

        Returns
        -------
        :class:`ThreeDECAnalysis`
            Prepared, serialisable analysis input.

        Raises
        ------
        ValueError
            If required geometry, materials, contact properties, or gravity
            configuration is missing or inconsistent.
        """
        if not self._blocks:
            raise ValueError("Add at least one mesh before building the analysis.")
        missing_material = [block["node"] for block in self._blocks if block["material"] is None]
        if self._source != "compas_dem" and missing_material:
            raise ValueError("No material is assigned to block nodes {}.".format(missing_material))
        if self._source != "compas_dem" and self._contact_properties is None:
            raise ValueError("Set contact properties before building the analysis.")

        gravity_indices = [index for index, stage in enumerate(self._stages) if stage.kind == "gravity"]
        boundary_indices = [index for index, stage in enumerate(self._stages) if stage.kind in ("loads", "displacements")]
        if boundary_indices and gravity_indices != [0]:
            raise ValueError("Analyses with loads or displacements require exactly one gravity stage, and gravity must be first.")
        for index, stage in enumerate(self._stages[:-1]):
            items = list(stage.point_loads or []) + list(stage.surface_loads or [])
            items += list(stage.displacements or [])
            if any(item.get("capacity") for item in items):
                raise ValueError("A capacity stage cannot be followed by another boundary-condition stage because its terminal state may be non-equilibrated.")

        entity_map = self._entity_map
        if entity_map is None:
            entity_map = ThreeDECEntityMap(name="{} entity map".format(self.name))
            for block in self._blocks:
                mesh = block["geometry"]
                entity_map.add_block(
                    node=block["node"],
                    element_guid=block["element_guid"],
                    region=block["region"],
                    vertices=[(vertex, mesh.vertex_coordinates(vertex)) for vertex in mesh.vertices()],
                )
            for interface in self._interfaces:
                entity_map.add_edge(tuple(interface["edge"]), source=self._source)

        return ThreeDECAnalysis(
            name=self.name,
            model_id=self.model_id,
            problem_id=self.problem_id,
            blocks=self._blocks,
            interfaces=self._interfaces,
            supports=self._supports,
            boundary_conditions=self._boundary_conditions,
            stages=self._stages,
            contact_properties=self._contact_properties,
            contact_property_overrides=self._contact_property_overrides,
            contact_block_pair_overrides=self._contact_block_pair_overrides,
            solver_configuration=self._solver_configuration,
            entity_map=entity_map,
            source=self._source,
        )

    def _selected_blocks(self, nodes):
        if nodes is None or nodes == "all":
            return self._blocks
        nodes = {int(node) for node in nodes}
        selected = [block for block in self._blocks if block["node"] in nodes]
        found = {block["node"] for block in selected}
        unknown = sorted(nodes - found)
        if unknown:
            raise ValueError("Unknown direct block nodes: {}.".format(unknown))
        return selected

    def _require_group(self, name):
        name = _group_name(name)
        if name not in self._groups:
            raise ValueError("Unknown block group {!r}.".format(name))
        return name

    def _blocks_in_group(self, name):
        name = self._require_group(name)
        blocks = [block for block in self._blocks if block["group"] == name]
        if not blocks:
            raise ValueError("Block group {!r} is empty.".format(name))
        return blocks
