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
from compas_model.materials import Concrete
from compas_model.interactions import Interaction, ContactInterface
from compas_3dec.datastructures.input import Material, Input
from compas_3dec.datastructures.problem3dec import Problem3dec, ContactProperty
from compas_3dec.datastructures.problem3dec import MohrCoulomb
from compas_3dec.datastructures.conversion import from_model

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
    model.add_interaction(elements[i[0]], elements[i[1]], Interaction())

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
# convert model to problem
# =============================================================================
input = from_model(model)
print(input)
problem = Problem3dec(input)

# =============================================================================
# Viewer
# =============================================================================

# =============================================================================
# set contact property/ies
# =============================================================================
stiffness = problem.set_joint_stiffness_one_material(
    block_height=0.5,
    reduction_factor=1,
    block_length=None,
    material_name="3DCP")

stiffness = problem.set_joint_stiffness_two_materials(
    block_height=0.5,
    interface_thickness=1,
    reduction_factor=1,
    material0_name="3DCP",
    material1_name="3DCP")

failure_criteria = MohrCoulomb(friction=35)

contact_property_supports = ContactProperty(stiffness, failure_criteria, "Supports")

problem.assign_group_to_meshes([3,4],"Test")

# =============================================================================
# 3DEC geometry generation
# =============================================================================
problem.to_geometry_3dec()

# =============================================================================
# Run Different Analyses
# =============================================================================



# problem.run_gravity(blokcs = "3DCP", supports = "3DCP")

# problem.to_geometry_3dec()

# p1 = problem.self_weight()
# p1.run(geo.dat, block.dat,displ.dat)

# self_weight

# displacement

# load

# =============================================================================
# convert Problem to Model for Vizualization
# =============================================================================
