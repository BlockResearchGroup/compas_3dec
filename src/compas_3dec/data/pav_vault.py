import os
import compas
from compas.datastructures import Mesh
from compas.geometry import subtract_vectors, angle_vectors, add_vectors, transform_points, Rotation, translate_points, Point, Line, Arc
from compas.scene import Scene
from math import radians

# parameters
side1 = 5.0                      # span of the vault measured at the ends of the middle axis
side2 = 8.0                    # length of the vault perpendiculat to the span
thickness = 0.2               # thickness of the vault
rise = 0.8                      # rise of the vault from 0.0 to middle axis of the vault thickness
block_length = 0.3                    # number of voussoirs in the span direction
block_width = 0.08                # number of voussoirs in the length direction

class PavilionVault:

    def __init__(self, side1, side2, thickness, rise, vou_span, vou_length):
        self.side1 = side1
        self.side2 = side2
        self.thickness = thickness
        self.rise = rise
        self.block_length = vou_span
        self.block_width = vou_length

    def vault_intrados_lines(self):
        radius1 = self.rise/2 + self.side1**2/(8*self.rise)
        radius2 = self.rise/2 + self.side2**2/(8*self.rise)

        

        print(radius1, radius2)




pavilion = PavilionVault(5, 8, 0.2, 0.8, 0.3, 0.08)

radius = pavilion.vault_intrados_lines()




# print(radius)

from compas_viewer import Viewer
viewwer = Viewer()



        # origin = Point(0, 0, 0)
        # pt1 = Point(self.side1, 0, 0)
        # pt2 = Point(0, self.side2, 0)
        # arc1 = Arc(self.rise,)pip 


        # radius = self.rise/2 + self.span**2/(8*self.rise)
        # top = [0, 0, self.rise]
        # left = [-self.span/2, 0, 0]
        # center = [0.0, 0.0, self.rise-radius]
        # vector = subtract_vectors(left, center)
        # springing = angle_vectors(vector, [-1.0, 0.0, 0.0]) 
        # sector = radians(180) - 2 * springing
        # angle = sector / self.vou_span

        # a = [0, 0, self.rise-(self.thickness/2)]
        # d = add_vectors(top, [0, 0, (self.thickness/2)])








# def generate_vault_edges(center, pt1, pt2):
#     """Creates the vault edges as intersections of barrel vaults."""
#     edge1 = Line(center, pt1)
#     edge2 = Line(pt2, center)
#     return edge1, edge2


# def create_vault_surface(edge1, edge2):
#     """Generates the vault surface."""
#     return Mesh.from_vertices_and_faces([edge1.start, edge1.end, edge2.end, edge2.start], [[0, 1, 2, 3]])


# def create_bricks(surface, brick_size, offset_ratio):
#     """Generates bricks for the vault structure."""
#     bricks = []
#     centroid = surface.centroid()
#     div_length = brick_size[1]
#     points = [translate_points([centroid], scale_vector(Vector(0, 1, 0), i * div_length))[0] for i in range(10)]
#     for i, pt in enumerate(points[:-1]):
#         bricks.append(Mesh.from_vertices_and_faces([pt, points[i+1], (pt[0] + brick_size[0], pt[1], pt[2]), (pt[0], pt[1] + brick_size[1], pt[2])], [[0, 1, 2, 3]]))
#     return bricks


# def create_pavilion():
#     """Main function to create the pavilion vault."""
#     center = Point(0, 0, 0)
#     pt1 = Point(4, 0, 0)
#     pt2 = Point(0, 4, 0)
#     height = 2.28

#     arch_data = create_arch(center, pt1, pt2, height)
#     edge1, edge2 = generate_vault_edges(*arch_data[:3])
#     surface = create_vault_surface(edge1, edge2)
#     bricks = create_bricks(surface, (0.24, 0.06, 0.12), 1/3)

#     return bricks

# from compas_viewer import Viewer

# viewer = Viewer()



# if __name__ == "__main__":
#     pavilion_bricks = create_pavilion()
    # for brick in pavilion_bricks:
    #     viewer.scene.add(brick)


