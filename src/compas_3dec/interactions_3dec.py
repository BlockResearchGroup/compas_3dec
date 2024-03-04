from compas_model.interactions import Interaction
from compas.geometry import add_vectors, scale_vector, Line, Vector, Point, Polygon
from compas.colors import ColorMap, Color
from compas.datastructures import Mesh


class Interaction3dec(Interaction):
    def __init__(self, name=None, type=None, normal=None, contact_geometry=None, forces_per_vertices=None):
        # type: (str | None, str | None, Vector | list | None, Polygon | Line | Point | None, dict | None) -> None
        super().__init__(name)
        self.type = type
        self.normal = normal
        self.contact_geometry = contact_geometry
        self.forces_per_vertices = forces_per_vertices



    def vector_force_display(self, scale_factor):
        normal_force_lines = []
        shear_force_lines = []
        points = []

        cmap = ColorMap.from_two_colors(Color.white(), Color.red())
        n = 100
        max_normal_stress = 0
        max_shear_stress = 0
        for forces_per_vertex in self.forces_per_vertices:
            position = forces_per_vertex["position"]
            points.append(Point(*position))
            max_normal_stress = max(max_normal_stress,forces_per_vertex["normal_stress"])
            max_shear_stress = max(max_shear_stress,forces_per_vertex["shear_stress"])

            normal_force = Vector(*forces_per_vertex["normal_force"])
            normal_force_lines.append(Line.from_point_and_vector(position, normal_force*scale_factor))
            normal_force_lines.append(Line.from_point_and_vector(position, -normal_force*scale_factor))

            shear_force = Vector(*forces_per_vertex["shear_force"])
            shear_force_lines.append(Line.from_point_and_vector(position, shear_force*scale_factor))
            shear_force_lines.append(Line.from_point_and_vector(position, -shear_force*scale_factor))


        mesh_normal_stress = Mesh.from_vertices_and_faces(*self.contact_geometry.to_vertices_and_faces())
        mesh_shear_stress = Mesh.from_vertices_and_faces(*self.contact_geometry.to_vertices_and_faces())

        for index,force_per_vertex in enumerate(self.forces_per_vertices):
            normal_stress = force_per_vertex["normal_stress"]
            color_normal_stress = cmap(normal_stress, minval=0, maxval=max_normal_stress)
            mesh_normal_stress.vertex_attribute(index, "color",color_normal_stress)

            shear_stress = force_per_vertex["shear_stress"]
            color_shear_stress = cmap(shear_stress, minval=0, maxval=max_shear_stress)
            mesh_shear_stress.vertex_attribute(index, "color",color_shear_stress)

        return normal_force_lines, shear_force_lines, points, mesh_normal_stress, mesh_shear_stress





