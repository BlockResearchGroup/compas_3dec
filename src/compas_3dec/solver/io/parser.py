from pathlib import Path

from ..results import ThreeDECRawResults

PREFIX = "COMPAS3DEC|"

CONTACT_TYPES = {
    0: "null",
    1: "face-face",
    2: "face-edge",
    3: "face-vertex",
    4: "edge-edge",
    5: "edge-vertex",
    6: "vertex-vertex",
    7: "joined",
}


def _float(value):
    return float(value.strip().strip("()"))


def _vector(values):
    return [_float(value) for value in values]


def _contact_resultant(contact):
    vectors = []
    normal = contact["normal"]
    for subcontact in contact["subcontacts"]:
        normal_force = subcontact["force_normal"]
        shear = subcontact["force_shear"]
        vectors.append([normal[index] * normal_force + shear[index] for index in range(3)])
    if not vectors:
        return None
    return [sum(vector[index] for vector in vectors) for index in range(3)]


def parse_results_text(text, name=None):
    """Parse tagged FISH log output into portable raw result records."""
    metadata = {}
    blocks = []
    gridpoints = []
    contacts = []
    contact_by_id = {}
    snapshot_count = 0

    for line_number, line in enumerate(str(text).splitlines(), start=1):
        start = line.find(PREFIX)
        if start < 0:
            continue
        fields = line[start:].strip().split("|")
        record_type = fields[1]

        try:
            if record_type == "META":
                # Logging is append-by-default in 3DEC. Legacy result files may
                # therefore contain several complete snapshots. Every capture
                # starts with META|schema; retain only the most recent one.
                if fields[2] == "schema":
                    snapshot_count += 1
                    if metadata or blocks or gridpoints or contacts:
                        metadata = {}
                        blocks = []
                        gridpoints = []
                        contacts = []
                        contact_by_id = {}
                value = fields[3]
                if fields[2] in ("schema", "fish_version"):
                    value = int(value)
                elif fields[2] in ("ratio_local", "timestep"):
                    value = _float(value)
                metadata[fields[2]] = value

            elif record_type == "BLOCK":
                blocks.append(
                    {
                        "block_id": int(fields[2]),
                        "region": int(fields[3]),
                        "centroid": _vector(fields[4:7]),
                        "mass": _float(fields[7]),
                        "volume": _float(fields[8]),
                        "velocity": _vector(fields[9:12]),
                        "unbalanced_force": _vector(fields[12:15]),
                        "applied_force": _vector(fields[15:18]),
                        "moment": _vector(fields[18:21]),
                    }
                )

            elif record_type == "GRIDPOINT":
                gridpoints.append(
                    {
                        "gridpoint": int(fields[2]),
                        "region": int(fields[3]),
                        "xyz": _vector(fields[4:7]),
                    }
                )

            elif record_type == "CONTACT":
                raw_contact_type = fields[5].strip()
                try:
                    contact_type_code = int(raw_contact_type)
                except ValueError:
                    contact_type_code = None
                contact_type = CONTACT_TYPES.get(
                    contact_type_code,
                    raw_contact_type.lower().replace("_", "-"),
                )
                record = {
                    "contact_id": int(fields[2]),
                    "region_a": int(fields[3]),
                    "region_b": int(fields[4]),
                    "contact_type": contact_type,
                    "contact_type_code": contact_type_code,
                    "point": _vector(fields[6:9]),
                    "normal": _vector(fields[9:12]),
                    "subcontacts": [],
                }
                contacts.append(record)
                contact_by_id[record["contact_id"]] = record

            elif record_type == "SUBCONTACT":
                contact_id = int(fields[3])
                if contact_id not in contact_by_id:
                    raise ValueError("Subcontact references unknown contact {}.".format(contact_id))
                schema = int(metadata.get("schema", 1))
                state = None
                if schema >= 3:
                    stress_shear = _float(fields[16])
                    area = _float(fields[17])
                    state = int(fields[18])
                elif len(fields) >= 20:
                    stress_shear = _vector(fields[16:19])
                    area = _float(fields[19])
                else:
                    stress_shear = _float(fields[16])
                    area = _float(fields[17])

                record = {
                    "subcontact_id": int(fields[2]),
                    "point": _vector(fields[4:7]),
                    "force_normal": _float(fields[7]),
                    "force_shear": _vector(fields[8:11]),
                    "displacement_normal": _float(fields[11]),
                    "displacement_shear": _vector(fields[12:15]),
                    "stress_normal": _float(fields[15]),
                    "stress_shear": stress_shear,
                    "area": area,
                }
                if state is not None:
                    record["state"] = state
                contact_by_id[contact_id]["subcontacts"].append(record)
        except (IndexError, TypeError, ValueError) as error:
            raise ValueError(
                "Invalid {} record on log line {}: {!r}".format(
                    record_type,
                    line_number,
                    line,
                )
            ) from error

    if not blocks and not gridpoints and not contacts and not metadata:
        raise ValueError("The text contains no COMPAS3DEC result records.")

    for contact in contacts:
        contact["resultant_global"] = _contact_resultant(contact)
    metadata["snapshot_count"] = snapshot_count

    return ThreeDECRawResults(
        name=name,
        blocks=blocks,
        gridpoints=gridpoints,
        contacts=contacts,
        metadata=metadata,
    )


def parse_results_file(filepath):
    path = Path(filepath)
    return parse_results_text(
        path.read_text(encoding="utf-8", errors="replace"),
        name=path.stem,
    )


def bind_initial_gridpoints(analysis, raw_results, tolerance=1e-6):
    """Bind initial 3DEC gridpoint IDs to prepared COMPAS mesh vertices."""
    by_region = {}
    for record in raw_results.gridpoints:
        by_region.setdefault(int(record["region"]), {})[int(record["gridpoint"])] = record["xyz"]

    for block in analysis.entity_map.blocks:
        region = block["region"]
        if region not in by_region:
            raise ValueError("Initial 3DEC output has no gridpoints for region {}.".format(region))
        analysis.entity_map.bind_gridpoints(
            node=block["node"],
            gridpoints=by_region[region],
            tolerance=tolerance,
        )
    return analysis.entity_map
