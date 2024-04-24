# from compas.scene import Scene
from compas_model.model import Model
from compas_model.elements import BlockElement
from compas.datastructures import Mesh

from compas_3dec.data.arch import Arch
import os

# from compas_viewer import Viewer
from compas.colors import Color
from compas_3dec.interactions_3dec import Interaction3dec
from compas_3dec.rigid_interaction import RigidInteraction
from compas_3dec.problem import Problem
from compas_model.materials import ElasticIsotropic
from compas_3dec.problem3dec import Problem3dec


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
# materials
# =============================================================================
model.add_material(ElasticIsotropic(name="3DCP", rho = 2500, E=300000, v=0.2))
# model.add_material(ElasticIsotropic(name="Neoprene", rho = 1500, E=300000, v=0.2))

# =============================================================================
# assign elements and materials to the model
# =============================================================================
for m in meshes:
    model.add_element(BlockElement(m))

# add other methods for supports selection
model.elementlist[0].is_support = True
model.elementlist[-1].is_support = True

for element in model.elementlist:
    model.assign_material(element, "3DCP")

rigidinteraction = RigidInteraction()
model.add_interaction(model.elementlist[1], model.elementlist[2], rigidinteraction)
model.add_interaction(model.elementlist[2], model.elementlist[3], interaction=RigidInteraction())
model.add_interaction(model.elementlist[-2], model.elementlist[-3], interaction=RigidInteraction())
model.add_interaction(model.elementlist[-3], model.elementlist[-4], interaction=RigidInteraction())
model.add_interaction(model.elementlist[-5], model.elementlist[-6], interaction=RigidInteraction())

# =============================================================================
# problems
# =============================================================================
problem = Problem("3dec", model)

problem.setup_3dec_one_material(block_material="3DCP", support_material = "3DCP", block_height=0.5, reduction_factor=1, friction_angle=35)
# problem.setup_3dec_two_materials(block_material="3DCP",support_material = "3DCP", interface_material="Neoprene", block_height=0.5, interface_thickness = 0.01, reduction_factor=1, friction_angle=35)



# problem.run_gravity(blokcs = "3DCP", supports = "3DCP")

# problem.to_geometry_3dec()

# p1 = problem.self_weight()
# p1.run(geo.dat, block.dat,displ.dat)

# self_weight

# displacement

# load
