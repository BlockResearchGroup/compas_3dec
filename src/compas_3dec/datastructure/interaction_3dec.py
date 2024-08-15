from compas.colors import Color, ColorMap
from compas.data import Data
from compas.datastructures import Mesh
from compas.geometry import Point, Vector, Line, Polygon


class Interaction3dec(Data):
    def __init__(
        self,
        neighbours=None,  # type: list | None
        type=None,  # type: int | None
        normal=None,  # type: Vector | list | None
        position=None,  # type: Vector | list | None
        contact_geometry=None,  # type: Polygon | Line | Point | None
        forces_per_vertices=None,  # type: dict | None
        forces_per_contact=None,  # type: dict | None
    ):
        super().__init__()
        self.type = type
        self.neighbours = neighbours
        self.normal = normal
        self.position = position
        self.contact_geometry = contact_geometry
        self.forces_per_vertices = forces_per_vertices
        self.forces_per_contact = forces_per_contact

    @property
    def __data__(self):
        # type: () -> dict
        return {
            "type": self.type,
            "neighbours": self.neighbours,
            "normal": self.normal,
            "position": self.position,
            "contact_geometry": self.contact_geometry,
            "forces_per_vertices": self.forces_per_vertices,
            "forces_per_contact": self.forces_per_contact,
        }

    @classmethod
    def __from_data__(cls, data):
        return cls(
            neighbours=data["neighbours"],
            type=data["type"],
            normal=data["normal"],
            position=data["position"],
            contact_geometry=data["contact_geometry"],
            forces_per_vertices=data["forces_per_vertices"],
            forces_per_contact=data["forces_per_contact"],
        )

    def __repr__(self):
        return f"[type: {self.type}, neighbours: {self.neighbours}, normal: {self.normal}, position: {self.position}, contact_geometry: {self.contact_geometry}, forces_per_vertices: {self.forces_per_vertices}, forces_per_contact: {self.forces_per_contact}]"

    def display_resultant_force(self, scale_factor=0.005):
        # if not self.type == "null":
        if self.forces_per_contact:
            if "resultant_point" in self.forces_per_contact:
                application_point = Point(*self.forces_per_contact["resultant_point"])
                resultant = self.create_lines(application_point, "resultant_force", scale_factor)
                return resultant

    def display_resultant_application_point(self):
        # if not self.type == "null":
        if self.forces_per_contact:
            if "resultant_point" in self.forces_per_contact:
                application_point = Point(*self.forces_per_contact["resultant_point"])
                return application_point

    def display_resultant_shear_application_point(self):
        # if not self.type == "null":
        if self.forces_per_contact:
            if "resultant_point_shear" in self.forces_per_contact:
                application_point = Point(*self.forces_per_contact["resultant_point_shear"])
                return application_point

    def display_resultant_normal(self, scale_factor=0.005):
        if self.forces_per_contact:
            application_point = Point(*self.forces_per_contact["resultant_point"])
            resultant = self.create_lines(application_point, "resultant_normal", scale_factor)
            return resultant

    def display_resultant_shear_transported(self, scale_factor=0.005):
        if self.forces_per_contact:
            application_point = Point(*self.forces_per_contact["resultant_point"])
            resultant = self.create_lines(application_point, "resultant_shear", scale_factor)
            return resultant

    def display_resultant_shear(self, scale_factor=0.005):
        if self.forces_per_contact:
            application_point = Point(*self.forces_per_contact["resultant_point_shear"])
            resultant = self.create_lines(application_point, "resultant_shear", scale_factor)
            return resultant

    def display_resultant_torque(self, scale_factor=0.005):
        if self.forces_per_contact:
            application_point = Point(*self.forces_per_contact["resultant_point"])
            resultant = self.create_lines(application_point, "resultant_torque", scale_factor)
            return resultant

    def create_lines(self, point, force_key, scale_factor):
        vector = Vector(*self.forces_per_contact[force_key]) * scale_factor
        return Line.from_point_and_vector(point, vector), Line.from_point_and_vector(point, -vector)

    def display_resultant_forces(
        self,
        scale_factor=0.005,
        resultant=False,
        application_point=False,
        normal=False,
        shear_and_torque=False,
        shear=False,
        application_point_shear=False,
    ):
        resultant_forces = []
        application_points = []
        application_points_shear = []
        resultant_normal_forces = []
        resultant_shear_forces = []
        resultant_torque_forces = []
        resultant_shear_forces_transported = []
        return_list = []

        if not self.type == "null":
            resultant_point_application = Point(
                self.forces_per_contact["resultant_point"][0],
                self.forces_per_contact["resultant_point"][1],
                self.forces_per_contact["resultant_point"][2],
            )
            application_points.append(resultant_point_application)
            if application_point:
                return_list.append(application_points)

            resultant_point_application_shear = Point(
                self.forces_per_contact["resultant_point_shear"][0],
                self.forces_per_contact["resultant_point_shear"][1],
                self.forces_per_contact["resultant_point_shear"][2],
            )
            application_points_shear.append(resultant_point_application_shear)
            if application_point_shear:
                return_list.append(application_points_shear)

            if resultant:
                resultant_forces.append(
                    Line.from_point_and_vector(
                        resultant_point_application, Vector(*self.forces_per_contact["resultant_force"]) * scale_factor
                    )
                )
                resultant_forces.append(
                    Line.from_point_and_vector(
                        resultant_point_application, -Vector(*self.forces_per_contact["resultant_force"]) * scale_factor
                    )
                )
                return_list.append(resultant_forces)

            if normal:
                resultant_normal_forces.append(
                    Line.from_point_and_vector(
                        resultant_point_application, Vector(*self.forces_per_contact["resultant_normal"]) * scale_factor
                    )
                )
                resultant_normal_forces.append(
                    Line.from_point_and_vector(
                        resultant_point_application,
                        -Vector(*self.forces_per_contact["resultant_normal"]) * scale_factor,
                    )
                )
                return_list.append(resultant_normal_forces)

            if shear:
                resultant_shear_forces.append(
                    Line.from_point_and_vector(
                        resultant_point_application_shear,
                        Vector(*self.forces_per_contact["resultant_shear"]) * scale_factor,
                    )
                )
                resultant_shear_forces.append(
                    Line.from_point_and_vector(
                        resultant_point_application_shear,
                        -Vector(*self.forces_per_contact["resultant_shear"]) * scale_factor,
                    )
                )
                return_list.append(resultant_shear_forces)

            if shear_and_torque:
                resultant_torque_forces.append(
                    Line.from_point_and_vector(
                        resultant_point_application, Vector(*self.forces_per_contact["resultant_torque"]) * scale_factor
                    )
                )
                resultant_torque_forces.append(
                    Line.from_point_and_vector(
                        resultant_point_application,
                        -Vector(*self.forces_per_contact["resultant_torque"]) * scale_factor,
                    )
                )
                return_list.append(resultant_torque_forces)

                resultant_shear_forces_transported.append(
                    Line.from_point_and_vector(
                        resultant_point_application, Vector(*self.forces_per_contact["resultant_shear"]) * scale_factor
                    )
                )
                resultant_shear_forces_transported.append(
                    Line.from_point_and_vector(
                        resultant_point_application, -Vector(*self.forces_per_contact["resultant_shear"]) * scale_factor
                    )
                )
                return_list.append(resultant_shear_forces_transported)

            return return_list

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
