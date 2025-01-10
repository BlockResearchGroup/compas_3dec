from compas_model.interactions import Interaction
from compas.geometry import Line, Vector, Point, Polygon  # noqa: F401
from compas.colors import ColorMap, Color
from compas.datastructures import Mesh


class Interaction3dec(Interaction):
    def __init__(
        self,
        name=None,
        type=None,
        normal=None,
        contact_geometry=None,
        forces_per_vertices=None,
        forces_per_contact=None,
    ):
        # type: (str | None, str | None, Vector | list | None, Polygon | Line | Point | None, dict | None, dict | None) -> None
        super().__init__(name)
        self.type = type
        self.normal = normal
        self.contact_geometry = contact_geometry
        self.forces_per_vertices = forces_per_vertices
        self.forces_per_contact = forces_per_contact
        self.normal_force_lines = None
        self.shear_force_lines = None
        self.points = None
        self.mesh_normal_stress = None
        self.mesh_shear_stress = None
        self.resultant_point = None
        self.resultant_force = None
        if contact_geometry:
            self.mesh_contact_geometry = contact_geometry.to_mesh()

    def compute_force_display(self, scale_factor=0.005):
        self.normal_force_lines = []
        self.shear_force_lines = []
        self.points = []
        self.resultant_force = []
        self.resultant_point = []
        self.resultant_point_shear = []
        self.resultant_shear = []
        self.resultant_normal = []
        self.resultant_torque = []
        self.resultant_shear_transported = []

        if "resultant_point" in self.forces_per_contact:
            resultant_point_application = Point(
                self.forces_per_contact["resultant_point"][0],
                self.forces_per_contact["resultant_point"][1],
                self.forces_per_contact["resultant_point"][2],
            )
        else:
            resultant_point_application = Point(0, 0, 0)  # or some other default value
        # resultant_point_application = Point(self.forces_per_contact["resultant_point"][0],self.forces_per_contact["resultant_point"][1],self.forces_per_contact["resultant_point"][2])
        self.resultant_point.append(resultant_point_application)

        if "resultant_point_shear" in self.forces_per_contact:
            resultant_point_application_shear = Point(
                self.forces_per_contact["resultant_point_shear"][0],
                self.forces_per_contact["resultant_point_shear"][1],
                self.forces_per_contact["resultant_point_shear"][2],
            )
        else:
            resultant_point_application_shear = Point(0, 0, 0)  # or some other default value
        # resultant_point_application_shear = Point(self.forces_per_contact["resultant_point_shear"][0],self.forces_per_contact["resultant_point_shear"][1],self.forces_per_contact["resultant_point_shear"][2])
        self.resultant_point_shear.append(resultant_point_application_shear)

        if "resultant_force" in self.forces_per_contact:
            self.resultant_force.append(
                Line.from_point_and_vector(
                    resultant_point_application, Vector(*self.forces_per_contact["resultant_force"]) * scale_factor
                )
            )
            self.resultant_force.append(
                Line.from_point_and_vector(
                    resultant_point_application, -Vector(*self.forces_per_contact["resultant_force"]) * scale_factor
                )
            )

        if "resultant_shear" in self.forces_per_contact:
            self.resultant_shear.append(
                Line.from_point_and_vector(
                    resultant_point_application_shear,
                    Vector(*self.forces_per_contact["resultant_shear"]) * scale_factor,
                )
            )
            self.resultant_shear.append(
                Line.from_point_and_vector(
                    resultant_point_application_shear,
                    -Vector(*self.forces_per_contact["resultant_shear"]) * scale_factor,
                )
            )

        if "resultant_normal" in self.forces_per_contact:
            self.resultant_normal.append(
                Line.from_point_and_vector(
                    resultant_point_application, Vector(*self.forces_per_contact["resultant_normal"]) * scale_factor
                )
            )
            self.resultant_normal.append(
                Line.from_point_and_vector(
                    resultant_point_application, -Vector(*self.forces_per_contact["resultant_normal"]) * scale_factor
                )
            )

        if "resultant_torque" in self.forces_per_contact:
            self.resultant_torque.append(
                Line.from_point_and_vector(
                    resultant_point_application, Vector(*self.forces_per_contact["resultant_torque"]) * scale_factor
                )
            )
            self.resultant_torque.append(
                Line.from_point_and_vector(
                    resultant_point_application, -Vector(*self.forces_per_contact["resultant_torque"]) * scale_factor
                )
            )

        if "resultant_shear" in self.forces_per_contact:
            self.resultant_shear_transported.append(
                Line.from_point_and_vector(
                    resultant_point_application, Vector(*self.forces_per_contact["resultant_shear"]) * scale_factor
                )
            )
            self.resultant_shear_transported.append(
                Line.from_point_and_vector(
                    resultant_point_application, -Vector(*self.forces_per_contact["resultant_shear"]) * scale_factor
                )
            )

        cmap = ColorMap.from_two_colors(Color.white(), Color.red())
        max_normal_stress = 0
        max_shear_stress = 0
        for forces_per_vertex in self.forces_per_vertices:
            position = forces_per_vertex["position"]
            self.points.append(Point(*position))
            max_normal_stress = max(max_normal_stress, forces_per_vertex["normal_stress"])
            max_shear_stress = max(max_shear_stress, forces_per_vertex["shear_stress"])

            normal_force = Vector(*forces_per_vertex["normal_force"])
            self.normal_force_lines.append(Line.from_point_and_vector(position, normal_force * scale_factor))
            self.normal_force_lines.append(Line.from_point_and_vector(position, -normal_force * scale_factor))

            shear_force = Vector(*forces_per_vertex["shear_force"])
            self.shear_force_lines.append(Line.from_point_and_vector(position, shear_force * scale_factor))
            self.shear_force_lines.append(Line.from_point_and_vector(position, -shear_force * scale_factor))

        self.mesh_normal_stress = Mesh.from_vertices_and_faces(*self.contact_geometry.to_vertices_and_faces())
        self.mesh_shear_stress = Mesh.from_vertices_and_faces(*self.contact_geometry.to_vertices_and_faces())

        # for index, force_per_vertex in enumerate(self.forces_per_vertices):
        #     normal_stress = force_per_vertex["normal_stress"]
        #     color_normal_stress = cmap(normal_stress, minval=0, maxval=max_normal_stress)
        #     self.mesh_normal_stress.vertex_attribute(index, "color", color_normal_stress)

        #     shear_stress = force_per_vertex["shear_stress"]
        #     color_shear_stress = cmap(shear_stress, minval=0, maxval=max_shear_stress)
        #     self.mesh_shear_stress.vertex_attribute(index, "color", color_shear_stress)
