import time
start = time.time()
from compas_3dec.datastructures.problem3dec import Problem3dec, Group, MohrCoulomb, Interaction3dec
from compas_3dec.data.arch import Arch

# =============================================================================
# Input geometry
# =============================================================================
arch = Arch(rise=5, span=10, thickness=0.5, depth=0.5, n=20)
meshes = arch.blocks()

# =============================================================================
# Init Problem3dec
# =============================================================================
problem = Problem3dec(working_path='C:\\Users\\adellend\\Code2\\compas_3dec\\docs\\examples')
# problem.interactions = []
# =============================================================================
# add blocks
# =============================================================================
problem.add_blocks(meshes)

# =============================================================================
# add supports
# =============================================================================
problem.blocks[0].is_support = True
problem.blocks[-1].is_support = True

# =============================================================================
# add/assign groups
# =============================================================================
problem.add_group("Blocks")
problem.add_group("Supports")

for b in problem.blocks:
    if not b.is_support:
        b.group = problem.get_group_by_name("Blocks")
    else:
        b.group = problem.get_group_by_name("Supports")

# =============================================================================
# add compounds
# =============================================================================
# problem.add_rigid_interactions([[3,4,5],[7,8]])

# =============================================================================
# add material
# =============================================================================
concrete = problem.add_material(name="Concrete", E=30e9, poisson=0.2, rho=2400, group = ["Blocks", "Supports"])

# =============================================================================
# add contact_properties
# =============================================================================
stiffness_1 = problem.set_joint_stiffness_one_material(
    block_height=0.5,
    reduction_factor=1,
    block_length=None,
    material_name="Concrete")

failure_criteria = MohrCoulomb(friction=35)

contact_property = problem.add_contact_property(stiffness_1, failure_criteria, ["Blocks","Supports"])

# =============================================================================
# create geometry.dat
# =============================================================================
problem.to_geometry_3dec()

# =============================================================================
# create gravity.dat
# =============================================================================
gravity_file = problem.gravity()

# =============================================================================
# run 3DEC
# =============================================================================
problem.run([gravity_file])

# =============================================================================
# read results
# =============================================================================
init_dict = problem.from_3dec_blocks("init_state.txt")
mapping_dict = problem.mapping(init_dict)
grav_dict = problem.from_3dec_blocks("grav_state.txt")
problem.solve_ratio_check("grav_state.txt")
problem.update_blocks(grav_dict,mapping_dict)


# # output_3dec_per_vertex = model.from_3dec_contacts("contact_grav.txt")
output_3dec_per_vertex = problem.from_3dec_contacts("contact_grav.txt")

# for gro in problem.groups:
#     print(gro.name)

# for block in problem.blocks:
#     print(block.unbalanced_force_ratio)





# for interaction in problem.interactions:
#     geometry = interaction.display_resultant_forces(scale_factor=0.005, resultant=True)





# =============================================================================
# view
# =============================================================================
from compas.scene import Scene
from compas.colors import Color
# import rhinoscriptsyntax as rs
# rs.DeleteObjects(rs.AllObjects())
scene = Scene()

for interaction in problem.interactions:
    if interaction.forces_per_contact:
        application_point = interaction.display_resultant_application_point()
        application_point_shear = interaction.display_resultant_shear_application_point()
        resultant_force = interaction.display_resultant_force(scale_factor=0.005)
        resultant_normal = interaction.display_resultant_normal(scale_factor=0.005)
        resultant_shear = interaction.display_resultant_shear(scale_factor=0.005)
        resultant_shear_transported = interaction.display_resultant_shear_transported(scale_factor=0.005)
        resultant_torque = interaction.display_resultant_torque(scale_factor=0.005)

        for line in resultant_force:
            scene.add(line, color= Color.from_rgb255(0, 166, 12))
        for line in resultant_normal:
            scene.add(line, color= Color.from_rgb255(0, 47, 167))
        for line in resultant_shear_transported:
            scene.add(line, color= Color.from_rgb255(166, 0, 62))
        for line in resultant_shear:
            scene.add(line, color= Color.from_rgb255(166, 0, 62))
        for line in resultant_torque:
            scene.add(line, color= Color.from_rgb255(166, 118, 0))
        scene.add(application_point)
        scene.add(application_point_shear)

for block in problem.blocks:
    # scene.add(block.mesh)
    scene.add(block.mesh, color = block.color_equilibrium)
scene.draw()



end = time.time()
print("analysis_3dec time", end - start)
