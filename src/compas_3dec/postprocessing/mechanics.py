from math import radians
from math import tan

from compas.data import Data
from compas.geometry import Frame
from compas.geometry import Line
from compas.geometry import Plane
from compas.geometry import Point
from compas.geometry import Polygon
from compas.geometry import Transformation
from compas.geometry import add_vectors
from compas.geometry import centroid_points
from compas.geometry import convex_hull_xy
from compas.geometry import cross_vectors
from compas.geometry import dot_vectors
from compas.geometry import length_vector
from compas.geometry import normalize_vector
from compas.geometry import project_point_plane
from compas.geometry import scale_vector
from compas.geometry import subtract_vectors
from compas.geometry import transform_points

from .compas_dem import block_transformation


def _moment_about(point, forces):
    moment = [0.0, 0.0, 0.0]
    for position, force in forces:
        moment = add_vectors(
            moment,
            cross_vectors(subtract_vectors(position, point), force),
        )
    return moment


def _central_axis_point(origin, force, moment):
    denominator = dot_vectors(force, force)
    if denominator <= 1e-30:
        return list(origin)
    return add_vectors(
        origin,
        scale_vector(cross_vectors(force, moment), 1.0 / denominator),
    )


def _contact_geometry(points, origin, normal):
    unique = []
    seen = set()
    for point in points:
        key = tuple(round(float(value), 12) for value in point)
        if key not in seen:
            seen.add(key)
            unique.append([float(value) for value in point])
    if len(unique) == 1:
        return Point(*unique[0])
    if len(unique) == 2:
        return Line(unique[0], unique[1])
    if len(unique) < 3:
        return None

    plane = Plane(origin, normal)
    frame = Frame.from_plane(plane)
    transformation = Transformation.from_frame_to_frame(frame, Frame.worldXY())
    flat = transform_points(unique, transformation)
    hull = convex_hull_xy(flat)
    return Polygon(transform_points(hull, transformation.inverse()))


def _value(item, name, default=None):
    if isinstance(item, dict):
        return item.get(name, default)
    return getattr(item, name, default)


def _friction_parameters(analysis, friction_coefficient, cohesion):
    if friction_coefficient is not None:
        return float(friction_coefficient), float(cohesion or 0.0)

    properties = analysis.contact_properties
    contact_model = _value(properties, "contact_model")
    if contact_model is not None:
        mu = _value(contact_model, "mu")
        if mu is None:
            phi = _value(contact_model, "phi")
            mu = tan(radians(float(phi))) if phi is not None else None
        c = _value(contact_model, "c", 0.0)
        if mu is not None:
            return float(mu), float(c or 0.0)

    # Direct contact properties store the angle used by the 3DEC command.
    phi = _value(properties, "friction")
    if phi is None:
        raise ValueError("A friction coefficient or a contact friction angle is required.")
    c = _value(properties, "cohesion", 0.0)
    return tan(radians(float(phi))), float(c or 0.0)


class ThreeDECPostProcessedResults(Data):
    """Serialisable mechanics derived from native 3DEC records."""

    CURRENT_SCHEMA_VERSION = 1

    def __init__(
        self,
        analysis_id,
        model_id,
        problem_id,
        blocks=None,
        contacts=None,
        metadata=None,
        schema_version=None,
        name=None,
    ):
        super().__init__(name=name)
        self.schema_version = schema_version or self.CURRENT_SCHEMA_VERSION
        self.analysis_id = str(analysis_id)
        self.model_id = str(model_id)
        self.problem_id = str(problem_id)
        self.blocks = list(blocks or [])
        self.contacts = list(contacts or [])
        self.metadata = dict(metadata or {})

    @property
    def __data__(self):
        return {
            "name": self.name,
            "schema_version": self.schema_version,
            "analysis_id": self.analysis_id,
            "model_id": self.model_id,
            "problem_id": self.problem_id,
            "blocks": self.blocks,
            "contacts": self.contacts,
            "metadata": self.metadata,
        }


def postprocess_raw_results(
    analysis,
    raw_results,
    friction_coefficient=None,
    cohesion=None,
    opening_tolerance=0.0,
    shear_displacement_tolerance=1e-9,
    friction_utilisation_tolerance=1e-9,
    compression_positive=True,
    components=None,
):
    """Derive selected native mechanics from raw 3DEC records.

    ``components`` accepts ``"blocks"``, ``"contacts"``, and ``"failure"``.
    The default computes all three. Contact processing is the canonical force,
    moment, resultant, and application-point calculation shared by the native
    and COMPAS DEM result routes. Failure processing adds friction, sliding,
    opening, crack, and hinge diagnostics.

    3DEC normal force is assumed positive in compression by default. A positive
    normal displacement is classified as opening when it exceeds
    ``opening_tolerance``. Sliding requires both mobilization of the friction
    capacity and a shear displacement larger than
    ``shear_displacement_tolerance``. Hinge candidates are the closed
    subcontact points farthest from the centroid of the opening points; this
    is a geometric indicator, not a fracture-mechanics proof.
    """
    requested = set(components or ("blocks", "contacts", "failure"))
    unknown = requested.difference(("blocks", "contacts", "failure"))
    if unknown:
        raise ValueError("Unknown postprocessing components: {}.".format(", ".join(sorted(unknown))))
    include_blocks = "blocks" in requested
    include_contacts = bool(requested.intersection(("contacts", "failure")))
    include_failure = "failure" in requested
    if include_failure:
        mu, resolved_cohesion = _friction_parameters(
            analysis,
            friction_coefficient,
            cohesion,
        )
    else:
        mu, resolved_cohesion = None, None
    blocks = []
    if include_blocks:
        for record in raw_results.blocks:
            region = int(record["region"])
            blocks.append(
                {
                    "node": analysis.entity_map.node_for_region(region),
                    "region": region,
                    "block_id": record.get("block_id"),
                    "transformation": block_transformation(
                        analysis,
                        raw_results,
                        region,
                    ),
                }
            )

    contacts = []
    for contact in raw_results.contacts if include_contacts else []:
        normal = normalize_vector(contact.get("normal") or [0.0, 0.0, 0.0])
        source_subcontacts = list(contact.get("subcontacts", []) or [])
        points = [subcontact["point"] for subcontact in source_subcontacts]
        origin = centroid_points(points) if points else list(contact.get("point") or [0, 0, 0])
        normal_forces = []
        shear_forces = []
        subcontacts = []
        opened_points = []
        closed_points = []
        total_area = 0.0
        compression = 0.0

        for subcontact in source_subcontacts:
            normal_scalar = float(subcontact["force_normal"])
            normal_vector = scale_vector(normal, normal_scalar)
            shear_vector = [float(value) for value in subcontact["force_shear"]]
            area = float(subcontact.get("area") or 0.0)
            normal_compression = max(normal_scalar, 0.0) if compression_positive else max(-normal_scalar, 0.0)
            shear_magnitude = length_vector(shear_vector)
            shear_displacement = [float(value) for value in subcontact.get("displacement_shear", [0.0, 0.0, 0.0])]
            shear_displacement_magnitude = length_vector(shear_displacement)
            state = subcontact.get("state")
            state = None if state is None else int(state)
            sliding_native = None if state is None else bool(state & 1)
            sliding_past = None if state is None else bool(state & 4)
            sliding_kinematic = shear_displacement_magnitude > float(shear_displacement_tolerance)
            capacity = None
            utilisation = None
            friction_limit_reached = False
            is_sliding = False
            if include_failure:
                capacity = mu * normal_compression + resolved_cohesion * area
                utilisation = shear_magnitude / capacity if capacity > 0.0 else None
                friction_limit_reached = utilisation is not None and utilisation >= 1.0 - float(friction_utilisation_tolerance)
                mechanical_sliding = friction_limit_reached and sliding_kinematic
                is_sliding = mechanical_sliding if sliding_native is None else sliding_native and mechanical_sliding
            opening = float(subcontact.get("displacement_normal") or 0.0)
            is_open = opening > float(opening_tolerance)
            point = [float(value) for value in subcontact["point"]]
            (opened_points if is_open else closed_points).append(point)

            derived = dict(subcontact)
            derived.update(
                {
                    "force_normal_vector": normal_vector,
                    "force_shear_magnitude": shear_magnitude,
                    "sliding": is_sliding,
                    "open": is_open,
                }
            )
            if include_failure:
                derived.update(
                    {
                        "friction_capacity": capacity,
                        "friction_utilisation": utilisation,
                        "friction_margin": capacity - shear_magnitude,
                        "shear_displacement_magnitude": shear_displacement_magnitude,
                        "friction_limit_reached": friction_limit_reached,
                        "sliding_native": sliding_native,
                        "sliding_past": sliding_past,
                        "sliding_kinematic": sliding_kinematic,
                        "sliding_confirmed": is_sliding,
                        "sliding_inconsistent": (
                            sliding_native is not None
                            and len(
                                {
                                    sliding_native,
                                    friction_limit_reached,
                                    sliding_kinematic,
                                }
                            )
                            > 1
                        ),
                        "opening_vector": scale_vector(normal, opening),
                    }
                )
            subcontacts.append(derived)
            normal_forces.append((point, normal_vector))
            shear_forces.append((point, shear_vector))
            total_area += area
            compression += normal_compression

        resultant_normal = [0.0, 0.0, 0.0]
        for _, force in normal_forces:
            resultant_normal = add_vectors(resultant_normal, force)
        resultant_shear = [0.0, 0.0, 0.0]
        for _, force in shear_forces:
            resultant_shear = add_vectors(resultant_shear, force)
        resultant = add_vectors(resultant_normal, resultant_shear)
        if not source_subcontacts and contact.get("resultant_global") is not None:
            resultant = [float(value) for value in contact["resultant_global"]]
            normal_scalar = dot_vectors(resultant, normal)
            resultant_normal = scale_vector(normal, normal_scalar)
            resultant_shear = subtract_vectors(resultant, resultant_normal)

        normal_moment = _moment_about(origin, normal_forces)
        shear_moment = _moment_about(origin, shear_forces)
        total_moment = add_vectors(normal_moment, shear_moment)
        normal_point = project_point_plane(
            _central_axis_point(origin, resultant_normal, normal_moment),
            (origin, normal),
        )
        shear_point = project_point_plane(
            _central_axis_point(origin, resultant_shear, shear_moment),
            (origin, normal),
        )
        total_axis_point = project_point_plane(
            _central_axis_point(origin, resultant, total_moment),
            (origin, normal),
        )
        # Match the legacy Interaction3dec convention: the resultant force is
        # applied at the normal resultant's planar point. The shear component
        # transported to this point leaves a residual torque, stored below.
        resultant_point = normal_point if length_vector(resultant_normal) > 1e-30 else total_axis_point
        torque_at_normal_point = _moment_about(
            normal_point,
            normal_forces + shear_forces,
        )
        residual_torque = _moment_about(
            resultant_point,
            normal_forces + shear_forces,
        )

        hinge_points = []
        if include_failure and opened_points and closed_points:
            opened_centroid = centroid_points(opened_points)
            distances = [(length_vector(subtract_vectors(point, opened_centroid)), point) for point in closed_points]
            maximum = max(distance for distance, _ in distances)
            threshold = max(1e-12, maximum * 1e-9)
            hinge_points = [point for distance, point in distances if maximum - distance <= threshold]

        capacity = mu * compression + resolved_cohesion * total_area if include_failure else None
        shear_magnitude = length_vector(resultant_shear)
        utilisation = shear_magnitude / capacity if include_failure and capacity > 0.0 else None
        friction_limit_reached = include_failure and any(subcontact["friction_limit_reached"] for subcontact in subcontacts)
        sliding = include_failure and any(subcontact["sliding"] for subcontact in subcontacts)
        sliding_native = include_failure and any(subcontact.get("sliding_native") is True for subcontact in subcontacts)
        sliding_past = include_failure and any(subcontact.get("sliding_past") is True for subcontact in subcontacts)
        sliding_inconsistent = include_failure and any(subcontact.get("sliding_inconsistent", False) for subcontact in subcontacts)
        edge = analysis.entity_map.bind_contact(
            contact["region_a"],
            contact["region_b"],
            contact["contact_id"],
        )
        derived_contact = {
            "contact_id": int(contact["contact_id"]),
            "edge": list(edge),
            "regions": [int(contact["region_a"]), int(contact["region_b"])],
            "contact_type": contact.get("contact_type"),
            "normal": normal,
            "origin": origin,
            "geometry": _contact_geometry(points, origin, normal),
            "subcontacts": subcontacts,
            "resultant_force": resultant,
            "resultant_normal": resultant_normal,
            "resultant_shear": resultant_shear,
            "resultant_point": resultant_point,
            "normal_application_point": normal_point,
            "shear_application_point": shear_point,
            "moment_about_origin": total_moment,
            "torque_at_normal_point": torque_at_normal_point,
            "residual_torque": residual_torque,
        }
        if include_failure:
            derived_contact.update(
                {
                    "friction_coefficient": mu,
                    "cohesion": resolved_cohesion,
                    "friction_capacity": capacity,
                    "friction_utilisation": utilisation,
                    "friction_margin": capacity - shear_magnitude,
                    "friction_limit_reached": friction_limit_reached,
                    "sliding": sliding,
                    "sliding_native": sliding_native,
                    "sliding_past": sliding_past,
                    "sliding_inconsistent": sliding_inconsistent,
                    "opening_points": opened_points,
                    "hinge_points": hinge_points,
                    "cracked": bool(opened_points),
                }
            )
        contacts.append(derived_contact)

    metadata = dict(raw_results.metadata)
    metadata.update(
        {
            "postprocessing_schema": ThreeDECPostProcessedResults.CURRENT_SCHEMA_VERSION,
            "postprocessing_components": sorted(requested),
            "opening_tolerance": float(opening_tolerance),
            "shear_displacement_tolerance": float(shear_displacement_tolerance),
            "friction_utilisation_tolerance": float(friction_utilisation_tolerance),
            "compression_positive": bool(compression_positive),
        }
    )
    if include_failure:
        metadata.update(
            friction_coefficient=mu,
            cohesion=resolved_cohesion,
        )
    return ThreeDECPostProcessedResults(
        name="{} post-processing".format(analysis.name),
        analysis_id=analysis.guid,
        model_id=analysis.model_id,
        problem_id=analysis.problem_id,
        blocks=blocks,
        contacts=contacts,
        metadata=metadata,
    )
