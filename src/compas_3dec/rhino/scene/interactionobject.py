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
            vertexcolors.append(mesh.vertex_attribute(vertex, "color"))
        # vertexcolors = [self.vertexcolor[vertex] for vertex in self.mesh.vertices()]

        attr = self.compile_attributes(name=self.interaction.name)
        geometry = None
        if len(vertexcolors) > 0:
            geometry = mesh_to_rhino(self.interaction.mesh_contact_geometry, vertexcolors=vertexcolors, disjoint=False)  # type: ignore
        else:
            geometry = mesh_to_rhino(self.interaction.mesh_contact_geometry, color=self.facecolor.default, disjoint=False)  # type: ignore

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

        if self.show_resultant_force:
            guids = self.draw_lines(self.interaction.resultant_force, self.color_resultant_force)
            self._guids.extend(guids)

        if self.show_resultant_point:
            guids = self.draw_points(self.interaction.resultant_point, self.color_points)
            self._guids.extend(guids)

        if self.show_resultant_point_shear:
            guids = self.draw_points(self.interaction.resultant_point_shear, self.color_points)
            self._guids.extend(guids)

        if self.show_resultant_force_shear:
            guids = self.draw_lines(self.interaction.resultant_shear, self.color_resultant_force_shear)
            self._guids.extend(guids)

        if self.show_resultant_force_normal:
            guids = self.draw_lines(self.interaction.resultant_normal, self.color_resultant_force_normal)
            self._guids.extend(guids)

        if self.show_resultant_torque:
            guids = self.draw_lines(self.interaction.resultant_torque, self.color_resultant_torque)
            self._guids.extend(guids)

        if self.show_resultant_shear_transported:
            guids = self.draw_lines(
                self.interaction.resultant_shear_transported, self.color_resultant_shear_transported
            )
            self._guids.extend(guids)

        return self._guids


# from __future__ import absolute_import
# from __future__ import division
# from __future__ import print_function

# try:
#     from itertools import zip_longest
# except ImportError:
#     from itertools import izip_longest as zip_longest  # type: ignore

# import Rhino  # type: ignore
# import System  # type: ignore

# from compas.colors import Color
# from compas.datastructures import Mesh
# from compas.geometry import centroid_polygon
# from compas.utilities import pairwise
# from compas_rhino.conversions import vector_to_compas


# def average_color(colors):
#     c = len(colors)
#     r, g, b = zip(*colors)
#     r = sum(r) / c
#     g = sum(g) / c
#     b = sum(b) / c
#     return Color(int(r), int(g), int(b))


# def connected_ngon(face, vertices, rmesh):
#     points = [vertices[index] for index in face]
#     centroid = centroid_polygon(points)

#     c = rmesh.Vertices.Add(*centroid)

#     facets = []
#     for i, j in pairwise(face + face[:1]):
#         facets.append(rmesh.Faces.AddFace(i, j, c))

#     ngon = Rhino.Geometry.MeshNgon.Create(face, facets)  # type: ignore
#     rmesh.Ngons.AddNgon(ngon)


# def disjoint_ngon(face, vertices, rmesh):
#     points = [vertices[vertex] for vertex in face]
#     centroid = centroid_polygon(points)

#     indices = []
#     for point in points:
#         x, y, z = point
#         indices.append(rmesh.Vertices.Add(x, y, z))

#     c = rmesh.Vertices.Add(*centroid)

#     facets = []
#     for i, j in pairwise(indices + indices[:1]):
#         facets.append(rmesh.Faces.AddFace(i, j, c))

#     ngon = Rhino.Geometry.MeshNgon.Create(indices, facets)  # type: ignore
#     rmesh.Ngons.AddNgon(ngon)


# def disjoint_face(face, vertices, rmesh):
#     indices = []
#     for index in face:
#         x, y, z = vertices[index]
#         indices.append(rmesh.Vertices.Add(x, y, z))
#     rmesh.Faces.AddFace(*indices)


# # =============================================================================
# # To Rhino
# # =============================================================================


# def mesh_to_rhino(
#     mesh,
#     color=None,
#     vertexcolors=None,
#     facecolors=None,
#     disjoint=True,
#     face_callback=None,
# ):
#     """Convert a COMPAS Mesh or a Polyhedron to a Rhino mesh object.

#     Parameters
#     ----------
#     mesh : :class:`compas.datastructures.Mesh` | :class:`compas.geometry.Polyhedron`
#         A COMPAS Mesh or a Polyhedron.
#     disjoint : bool, optional
#         If ``True``, each face of the resulting mesh will be independently defined (have a copy of its own vertices).
#     face_callback : callable, optional
#         Called after each face is created with the face as an agrument, useful for custom post-processing.

#     Returns
#     -------
#     :class:`Rhino.Geometry.Mesh`
#         A Rhino mesh object.

#     """
#     vertices, faces = mesh.to_vertices_and_faces()
#     return vertices_and_faces_to_rhino(
#         vertices,
#         faces,
#         color=color,
#         vertexcolors=vertexcolors,
#         facecolors=facecolors,
#         disjoint=disjoint,
#         face_callback=face_callback,
#     )


# polyhedron_to_rhino = mesh_to_rhino


# def vertices_and_faces_to_rhino(
#     vertices,
#     faces,
#     color=None,
#     vertexcolors=None,
#     facecolors=None,
#     disjoint=True,
#     face_callback=None,
# ):
#     """Convert COMPAS vertices and faces to a Rhino mesh object.

#     Parameters
#     ----------
#     vertices : list[[float, float, float] | :class:`compas.geometry.Point`]
#         A list of point locations.
#     faces : list[list[int]]
#         A list of faces as lists of indices into `vertices`.
#     disjoint : bool, optional
#         If ``True``, each face of the resulting mesh will be independently defined (have a copy of its own vertices).
#     face_callback : callable, optional
#         Called after each face is created with the face as an agrument, useful for custom post-processing.

#     Returns
#     -------
#     :class:`Rhino.Geometry.Mesh`
#         A Rhino mesh object.

#     """
#     if disjoint and facecolors:
#         if len(faces) != len(facecolors):
#             raise ValueError("The number of face colors does not match the number of faces.")

#     if not disjoint and vertexcolors:
#         if len(vertices) != len(vertexcolors):
#             raise ValueError("The number of vertex colors does not match the number of vertices.")

#     mesh = Rhino.Geometry.Mesh()

#     if not face_callback:

#         def face_callback(face):
#             pass

#     if disjoint:
#         vertexcolors = []

#         for face, facecolor in zip_longest(faces, facecolors or []):
#             f = len(face)

#             if f < 3:
#                 continue

#             if f > 4:
#                 if Rhino.Geometry.MeshNgon is None:
#                     raise NotImplementedError("MeshNgons are not supported in this version of Rhino.")

#                 disjoint_ngon(face, vertices, mesh)
#                 if facecolor:
#                     for _ in range(f + 1):
#                         vertexcolors.append(facecolor)

#             else:
#                 disjoint_face(face, vertices, mesh)
#                 if facecolor:
#                     for _ in range(f):
#                         vertexcolors.append(facecolor)

#             face_callback(face)

#     else:
#         for x, y, z in vertices:
#             mesh.Vertices.Add(x, y, z)

#         for face in faces:
#             f = len(face)

#             if f < 3:
#                 continue

#             if f > 4:
#                 if Rhino.Geometry.MeshNgon is None:
#                     raise NotImplementedError("MeshNgons are not supported in this version of Rhino.")

#                 connected_ngon(face, vertices, mesh)
#                 if vertexcolors:
#                     vertexcolors.append(average_color([vertexcolors[index] for index in face]))

#             else:
#                 mesh.Faces.AddFace(*face)

#             face_callback(face)

#     if vertexcolors:
#         if len(mesh.Vertices) != len(vertexcolors):
#             raise ValueError("The number of vertex colors does not match the number of vertices.")

#         colors = System.Array.CreateInstance(System.Drawing.Color, len(vertexcolors))
#         for index, color in enumerate(vertexcolors):
#             colors[index] = System.Drawing.Color.FromArgb(*color.rgb255)

#         mesh.VertexColors.SetColors(colors)
#     else:
#         if color:
#             mesh.VertexColors.CreateMonotoneMesh(System.Drawing.Color.FromArgb(*color.rgb255))

#     # mesh.UnifyNormals()
#     mesh.Normals.ComputeNormals()
#     mesh.Compact()

#     return mesh


# # =============================================================================
# # To COMPAS
# # =============================================================================


# def mesh_to_compas(rhinomesh, cls=None):
#     """Convert a Rhino mesh object to a COMPAS mesh.

#     Parameters
#     ----------
#     rhinomesh : :class:`Rhino.Geometry.Mesh`
#         A Rhino mesh object.
#     cls: :class:`compas.datastructures.Mesh`, optional
#         The mesh type.

#     Returns
#     -------
#     :class:`compas.datastructures.Mesh`
#         A COMPAS mesh.

#     """
#     cls = cls or Mesh
#     mesh = cls()
#     mesh.update_default_vertex_attributes(normal=None, color=None)
#     mesh.update_default_face_attributes(normal=None)

#     vertexcolors = rhinomesh.VertexColors
#     if not vertexcolors:
#         vertexcolors = [None] * rhinomesh.Vertices.Count

#     for vertex, normal, color in zip(rhinomesh.Vertices, rhinomesh.Normals, vertexcolors):
#         mesh.add_vertex(
#             x=float(vertex.X),
#             y=float(vertex.Y),
#             z=float(vertex.Z),
#             normal=vector_to_compas(normal),
#             color=Color.from_rgb255(int(color.R), int(color.G), int(color.B)) if color else None,
#         )

#     facenormals = rhinomesh.FaceNormals
#     if not facenormals:
#         facenormals = [None] * rhinomesh.Faces.Count

#     for face, normal in zip(rhinomesh.Faces, facenormals):
#         if face.IsTriangle:
#             vertices = [face.A, face.B, face.C]
#         else:
#             vertices = [face.A, face.B, face.C, face.D]
#         mesh.add_face(vertices, normal=vector_to_compas(normal) if normal else None)

#     for key in rhinomesh.UserDictionary:
#         mesh.attributes[key] = rhinomesh.UserDictionary[key]

#     return mesh

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
