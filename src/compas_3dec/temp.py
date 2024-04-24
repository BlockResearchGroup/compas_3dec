import os
from compas.geometry import scale_vector, cross_vectors, centroid_points, normalize_vector, transform_points, convex_hull_xy, sum_vectors, dot_vectors
from compas.geometry import Plane, Frame, Transformation,  Point, Line, Polygon




def from_3dec_contacts_resultant(self, filename, precision='1f'):
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
                    contacts[id]["subcontacts"][ids]["normal_force"] = normal_force/1000
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
            contact_normal = contact["normal"]

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
                        "is_combined" : False,
                    }

            MtorqueG = [0, 0, 0]
            Mtot = [0, 0, 0]
            Ntot = 0
            Stot = [0, 0, 0]

            points = []
            output_list = []
            for key, value in output_3dec_per_vertex.items():
                points.append(value["position"])

            centroid = centroid_points(points)

            for key, value in output_3dec_per_vertex.items():
                e1_plane = normalize_vector([value["position"][0] - centroid[0], value["position"][1] - centroid[1], value["position"][2] - centroid[2]])
                e2_plane = cross_vectors(contact_normal, e1_plane)
                break

            resultant_force = []
            resultant_points = []

            for key, value in output_3dec_per_vertex.items():
                vertex = value["position"]
                ri = [vertex[0] - centroid[0], vertex[1] - centroid[1], vertex[2] - centroid[2]]
                Ni = value["normal_force"][2]
                Mi = cross_vectors(ri, scale_vector(contact_normal, Ni))
                Mtot = sum_vectors([Mtot, Mi])
                Ntot = Ntot + Ni
                Si = value["shear_force"]
                Stot = (sum_vectors([Stot, Si]))
                MtorqueGi = cross_vectors(ri, Si)
                MtorqueG = sum_vectors([MtorqueG, MtorqueGi])

            if Ntot:
                Ftot = sum_vectors([Stot, scale_vector(contact_normal, Ntot)])
                NN = scale_vector(contact_normal, Ntot)
                b1 = -1 * dot_vectors(MtorqueG, e2_plane) / Ntot
                b2 = dot_vectors(Mtot, e1_plane) / Ntot
                po = sum_vectors([centroid,scale_vector(e1_plane,b1),scale_vector(e2_plane,b2)])

                output_3dec_per_vertex["resultant_force"] = Ftot
                output_3dec_per_vertex["resultant_point"] = po

                # resultant_force.append(Ftot)
                # resultant_points.append(po)
                # Mtorquepo = sum_vectors([MtorqueG, cross_vectors(sum_vectors([centroid,scale_vector(po, -1)]), Stot)])

            if len(points) > 2:
                normal = contact["normal"]
                position = contact["position"]
                plane = Plane(position, normal)
                frame = Frame.from_plane(plane)
                transformation = Transformation.from_frame_to_frame(frame, Frame.worldXY())
                points = transform_points(points, transformation)
                #ToDo: to be verified based on contact conditions (hinge)
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
        return output_3dec_per_vertex
