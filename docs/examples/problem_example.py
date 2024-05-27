# from compas.scene import Scene
from compas_model.models import Model
from compas_model.elements import BlockElement
from compas.datastructures import Mesh

from compas_3dec.data.arch import Arch
import os

# from compas_viewer import Viewer
from compas.colors import Color
from compas_3dec.problem import Problem
# from compas_model.materials import ElasticIsotropic
from compas_3dec.problem3dec_old import Problem3dec
from compas_model.materials import Concrete
from compas_model.interactions import Interaction
from compas_3dec.datastructures.input import Material, Input

# =============================================================================
# Input
# =============================================================================
arch = Arch(rise=5, span=10, thickness=0.5, depth=0.5, n=20)
meshes = arch.blocks()

# =============================================================================
# Create a Model with Elements.
# =============================================================================
model = Model()

for m in meshes:
    model.add_element(BlockElement(m))

elements = list(model.elements())



# =============================================================================
# User Interface
# =============================================================================

supports = [0, len(elements) - 1]
rigid_interaction_indices = [[1, 2], [2, 3], [-2, -3], [-3, -4], [-5, -6]]

# ToDo:
# a) Selection to define supports
# b) Iterative selection for rigid interactions
# c) Add indices of the elements:
# import rhinoscriptsyntax as rs
# for i in model.elementlist:
#     centroid = i.geometry.centroid()
#     node = i.graph_node
#     rs.AddTextDot(node, centroid)

# =============================================================================
# Assign Supports
# =============================================================================
for support in supports:
    elements[support].is_support = True

# =============================================================================
# Rigid Interactions
# =============================================================================
for i in rigid_interaction_indices:
    model.add_interaction(elements[i[0]], elements[i[1]], interaction=Interaction(name="Rigid"))

# =============================================================================
# materials
# =============================================================================
concrete = Concrete(fck=30, name="3DCP", density=2500, Ecm=300000, poisson=0.2)
model.add_material(concrete)

# Change in PR
neoprene = Concrete(fck=7.5, name="Neoprene", density=1230, Ecm=300000, poisson=0.49)
model.add_material(neoprene)

for element in model.elements():
    model.assign_material(concrete, element)

# =============================================================================
# problems
# =============================================================================

print(str(concrete))
# problem = Problem.from_model("3dec", model)
# problem = Problem.from_obj("3dec", model, materials)
# problem = Problem.from_meshes("3dec", model, materials)

# problem.setup_3dec_one_material(block_material="3DCP", support_material="3DCP", block_height=0.5, reduction_factor=1, friction_angle=35)
# # problem.setup_3dec_two_materials(block_material="3DCP",support_material = "3DCP", interface_material="Neoprene", block_height=0.5, interface_thickness = 0.01, reduction_factor=1, friction_angle=35)

# problem.run_gravity(blokcs = "3DCP", supports = "3DCP")

# problem.to_geometry_3dec()

# p1 = problem.self_weight()
# p1.run(geo.dat, block.dat,displ.dat)

# self_weight

# displacement

# load
