import scriptcontext as sc  # type: ignore
import compas.datastructures  # noqa: F401
import compas.geometry  # noqa: F401
from compas_rhino.conversions import mesh_to_rhino, line_to_rhino, point_to_rhino
from compas_rhino.conversions import transformation_to_rhino
from compas.geometry import Polygon
from compas.geometry import earclip_polygon

# from .interactionobject import ThreeinteractionObject
from compas_rhino.scene import RhinoSceneObject
from compas_3dec.scene.interactionobject import InteractionObject


class RhinoInteractionObject(RhinoSceneObject, InteractionObject):
    """Scene object for drawing block objects."""

    def __init__(self, interaction, **kwargs):
        super().__init__(interaction=interaction, **kwargs)


    def draw_points(self, points, color):
        guids = []
        attr = self.compile_attributes(color=color)
        for point in points:
            geometry = point_to_rhino(point)
            geometry.Transform(transformation_to_rhino(self.worldtransformation))
            guids.append(sc.doc.Objects.AddPoint(geometry, attr))
        return guids


    def draw_lines(self, lines, color, scale_factor=1):
        guids = []
        attr = self.compile_attributes(color=color)
        for line in lines:
            geometry = line_to_rhino(line)
            geometry.Transform(transformation_to_rhino(self.worldtransformation))
            guids.append(sc.doc.Objects.AddLine(geometry, attr))
        return guids


    def draw_mesh(self, mesh):
        guids = []
        vertexcolors = []
        for vertex, attr in mesh.vertices(True):
            vertexcolors.append(mesh.vertex_attribute(vertex, 'color'))
        # vertexcolors = [self.vertexcolor[vertex] for vertex in self.mesh.vertices()]

        attr = self.compile_attributes(name=self.interaction.name)
        geometry = None
        if len(vertexcolors)>0:
            geometry = mesh_to_rhino(self.interaction.mesh_contact_geometry, vertexcolors=vertexcolors, disjoint = False)  # type: ignore
        else:
            geometry = mesh_to_rhino(self.interaction.mesh_contact_geometry, color=self.facecolor.default, disjoint = False)  # type: ignore

        geometry.Transform(transformation_to_rhino(self.worldtransformation))
        guids.append(sc.doc.Objects.AddMesh(geometry, attr))
        return guids


    def draw(self):
        self._guids = []
        if self.show_normal_force_lines:
            self._guids.extend(self.draw_lines(self.interaction.normal_force_lines, self.color_normal_force_lines))

        if self.show_shear_force_lines:
            self._guids.extend(self.draw_lines(self.interaction.shear_force_lines, self.color_shear_force_lines))

        if self.show_points:
            self._guids.extend(self.draw_points(self.interaction.points, self.color_points))

        if self.show_mesh_normal_stress:
            self._guids.extend(self.draw_mesh(self.interaction.mesh_normal_stress))

        if self.show_mesh_shear_stress:
            self._guids.extend(self.draw_mesh(self.interaction.mesh_shear_stress))

        return self._guids

    # def draw_mesh(self, mesh, color=None):
    #     """Draw the mesh associated with the scene object.

    #     Returns
    #     -------
    #     list[three.Mesh, three.LineSegments]
    #         List of pythreejs objects created.

    #     """
    #     guids = []

    #     vertices = list(mesh.vertices())  # type: ignore
    #     faces = list(mesh.faces())  # type: ignore
    #     edges = list(mesh.edges())  # type: ignore

    #     # transformation = self.interaction.worldtransformation

    #     # if transformation:
    #     #     matrix = (  # noqa: F841  # type: ignore
    #     #         numpy.array(transformation.matrix, dtype=numpy.float32).transpose().ravel().tolist()
    #     #     )

    #     vertex_xyz = {vertex: mesh.vertex_attributes(vertex, "xyz") for vertex in vertices}  # type: ignore

    #     # =============================================================================
    #     # Vertices
    #     # =============================================================================

    #     if self.show_vertices:
    #         if self.show_vertices is not True:
    #             vertices = self.show_vertices

    #         positions = [vertex_xyz[vertex] for vertex in vertices]
    #         positions = numpy.array(positions, dtype=numpy.float32)

    #         colors = [self.vertexcolor[vertex] for vertex in vertices]  # type: ignore
    #         colors = numpy.array(colors, dtype=numpy.float32)

    #         geometry = three.BufferGeometry(
    #             attributes={
    #                 "position": three.BufferAttribute(positions, normalized=False),
    #                 "color": three.BufferAttribute(colors, normalized=False, itemSize=3),
    #             }
    #         )
    #         material = three.PointsMaterial(
    #             size=self.vertexsize,
    #             vertexColors="VertexColors",
    #         )

    #         threeobject = three.Points(geometry, material)
    #         # threeobject.matrix = matrix
    #         # threeobject.matrixAutoUpdate = False

    #         guids.append(threeobject)

    #     # =============================================================================
    #     # Edges
    #     # =============================================================================

    #     if self.show_edges:
    #         if self.show_edges is not True:
    #             edges = self.show_edges

    #         positions = []
    #         colors = []

    #         for u, v in edges:
    #             positions.append(vertex_xyz[u])
    #             positions.append(vertex_xyz[v])
    #             colors.append(self.edgecolor[u, v])
    #             colors.append(self.edgecolor[u, v])

    #         positions = numpy.array(positions, dtype=numpy.float32)
    #         colors = numpy.array(colors, dtype=numpy.float32)

    #         geometry = three.BufferGeometry(
    #             attributes={
    #                 "position": three.BufferAttribute(positions, normalized=False),
    #                 "color": three.BufferAttribute(colors, normalized=False, itemSize=3),
    #             }
    #         )
    #         material = three.LineBasicMaterial(vertexColors="VertexColors")

    #         threeobject = three.LineSegments(geometry, material)
    #         # threeobject.matrix = matrix
    #         # threeobject.matrixAutoUpdate = False

    #         guids.append(threeobject)

    #     # =============================================================================
    #     # Faces
    #     # =============================================================================

    #     if self.show_faces:
    #         if self.show_faces is not True:
    #             faces = self.show_faces

    #         positions = []
    #         colors = []

    #         for face in faces:
    #             vertices = mesh.face_vertices(face)  # type: ignore
    #             c = self.facecolor[face]  # type: ignore

    #             if len(vertices) == 3:
    #                 positions.append(vertex_xyz[vertices[0]])
    #                 positions.append(vertex_xyz[vertices[1]])
    #                 positions.append(vertex_xyz[vertices[2]])
    #                 colors.append(c)
    #                 colors.append(c)
    #                 colors.append(c)

    #             elif len(vertices) == 4:

    #                 positions.append(vertex_xyz[vertices[0]])
    #                 positions.append(vertex_xyz[vertices[1]])
    #                 positions.append(vertex_xyz[vertices[2]])
    #                 colors.append(mesh.vertex_attribute(vertices[0], "color"))
    #                 colors.append(mesh.vertex_attribute(vertices[1], "color"))
    #                 colors.append(mesh.vertex_attribute(vertices[2], "color"))
    #                 positions.append(vertex_xyz[vertices[0]])
    #                 positions.append(vertex_xyz[vertices[2]])
    #                 positions.append(vertex_xyz[vertices[3]])
    #                 colors.append(mesh.vertex_attribute(vertices[0], "color"))
    #                 colors.append(mesh.vertex_attribute(vertices[2], "color"))
    #                 colors.append(mesh.vertex_attribute(vertices[3], "color"))

    #             else:
    #                 polygon = Polygon([vertex_xyz[v] for v in vertices])
    #                 ears = earclip_polygon(polygon)
    #                 for ear in ears:  # type: ignore
    #                     positions.append(vertex_xyz[vertices[ear[0]]])
    #                     positions.append(vertex_xyz[vertices[ear[1]]])
    #                     positions.append(vertex_xyz[vertices[ear[2]]])
    #                     colors.append(mesh.vertex_attribute(vertices[0], "color"))
    #                     colors.append(mesh.vertex_attribute(vertices[1], "color"))
    #                     colors.append(mesh.vertex_attribute(vertices[2], "color"))

    #         positions = numpy.array(positions, dtype=numpy.float32)
    #         colors = numpy.array(colors, dtype=numpy.float32)

    #         geometry = three.BufferGeometry(
    #             attributes={
    #                 "position": three.BufferAttribute(positions, normalized=False),
    #                 "color": three.BufferAttribute(colors, normalized=False, itemSize=3),
    #             }
    #         )
    #         material = three.MeshBasicMaterial(
    #             side="DoubleSide",
    #             vertexColors="VertexColors",
    #         )

    #         threeobject = three.Mesh(geometry, material)
    #         # threeobject.matrix = matrix
    #         # threeobject.matrixAutoUpdate = False

    #         guids.append(threeobject)

    #     return guids

    # def draw_lines(self, lines, color, scale_factor=1):
    #     guids = []
    #     positions = []
    #     colors = []

    #     for line in lines:
    #         positions.append(line.start)
    #         positions.append(line.end)
    #         colors.append(color)
    #         colors.append(color)

    #     positions = numpy.array(positions, dtype=numpy.float32)
    #     colors = numpy.array(colors, dtype=numpy.float32)

    #     geometry = three.BufferGeometry(
    #         attributes={
    #             "position": three.BufferAttribute(positions, normalized=False),
    #             "color": three.BufferAttribute(colors, normalized=False, itemSize=3),
    #         }
    #     )
    #     material = three.LineBasicMaterial(vertexColors="VertexColors", linewidth=self.thickness_lines)

    #     threeobject = three.LineSegments(geometry, material)
    #     # threeobject.matrix = matrix
    #     # threeobject.matrixAutoUpdate = False

    #     guids.append(threeobject)
    #     return guids

    # def draw_points(self, points, color):
    #     guids = []
    #     geometry = three.BufferGeometry(
    #         attributes={
    #             "position": three.BufferAttribute(points, normalized=False),
    #             "color": three.BufferAttribute(color, normalized=False, itemSize=3),
    #         }
    #     )
    #     material = three.PointsMaterial(
    #         size=self.vertexsize * 0.1,
    #         vertexColors="VertexColors",
    #     )

    #     threeobject = three.Points(geometry, material)
    #     guids.append(threeobject)

    #     return guids

    # def draw(self):
    #     """Draw the mesh associated with the scene object.

    #     Returns
    #     -------
    #     list[three.Mesh, three.LineSegments]
    #         List of pythreejs objects created.

    #     """
    #     self._guids = []

    #     if self.show_normal_force_lines:
    #         guids = self.draw_lines(self.interaction.normal_force_lines, self.color_normal_force_lines)
    #         self._guids.extend(guids)

    #     if self.show_shear_force_lines:
    #         guids = self.draw_lines(self.interaction.shear_force_lines, self.color_shear_force_lines)
    #         self._guids.extend(guids)

    #     if self.show_points:
    #         guids = self.draw_points(self.interaction.points, self.color_points)
    #         self._guids.extend(guids)

    #     if self.show_mesh_normal_stress:
    #         guids = self.draw_mesh(self.interaction.mesh_normal_stress)
    #         self._guids.extend(guids)

    #     if self.show_mesh_shear_stress:
    #         guids = self.draw_mesh(self.interaction.mesh_shear_stress)
    #         self._guids.extend(guids)

    #     return self.guids
