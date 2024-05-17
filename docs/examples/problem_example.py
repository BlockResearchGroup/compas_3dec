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
from compas_3dec.problem3dec import Problem3dec
from compas_model.materials import Concrete
from compas_model.interactions import Interaction

# =============================================================================
# Input
# =============================================================================
arch = Arch(rise=5, span=10, thickness=0.5, depth=0.5, n=20)
meshes = arch.blocks()

# =============================================================================
# model
# =============================================================================
model = Model()

# =============================================================================
# assign elements and materials to the model
# =============================================================================
for m in meshes:
    model.add_element(BlockElement(m))

# =============================================================================
# materials
# =============================================================================
concrete = Concrete(fck=30, name="3DCP", density=2500, Ecm=300000, poisson=0.2)
model.add_material(concrete)

# Uncomment with the new model PR
# neoprene = Plastic(fck=7.5, fctm = 3.0, name="Neoprene", density=1230, Ecm=300000, poisson=0.49)
# model.add_material(neoprene)

# =============================================================================
# sort elements by z-coordinate and select the first two elements for boundaries
# =============================================================================

elements = list(model.elements())
elements[0].is_support = True
elements[-1].is_support = True

for element in model.elements():
    model.assign_material(concrete, element)

model.add_interaction(elements[1], elements[2], interaction=Interaction(name="Rigid"))
model.add_interaction(elements[2], elements[3], interaction=Interaction(name="Rigid"))
model.add_interaction(elements[-2], elements[-3], interaction=Interaction(name="Rigid"))
model.add_interaction(elements[-3], elements[-4], interaction=Interaction(name="Rigid"))
model.add_interaction(elements[-5], elements[-6], interaction=Interaction(name="Rigid"))

# =============================================================================
# problems
# =============================================================================

problem = Problem("3dec", model)

# problem.setup_3dec_one_material(block_material="3DCP", support_material = "3DCP", block_height=0.5, reduction_factor=1, friction_angle=35)
# # problem.setup_3dec_two_materials(block_material="3DCP",support_material = "3DCP", interface_material="Neoprene", block_height=0.5, interface_thickness = 0.01, reduction_factor=1, friction_angle=35)



# problem.run_gravity(blokcs = "3DCP", supports = "3DCP")

# problem.to_geometry_3dec()

# p1 = problem.self_weight()
# p1.run(geo.dat, block.dat,displ.dat)

# self_weight

# displacement

# load
