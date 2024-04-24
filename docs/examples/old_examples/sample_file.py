# This is a sample Python file generated programmatically
import itasca as it
it.command("""
;21/02/2024 18:22:13
model new
model large-strain on
program call 'geometry.dat'

block contact generate-subcontacts
block property density 2200 range group 'Supports'
block contact property stiffness-normal 150000.0 stiffness-shear 62500.0 friction 35
block contact material-table default property stiffness-normal 150000.0 stiffness-shear 62500.0
block fix range group 'Supports'

block property density 2200 range group 'Blocks'
block contact generate-subcontacts
block contact property stiffness-normal 150000.0 stiffness-shear 62500.0 friction 35
block contact material-table default property stiffness-normal 150000.0 stiffness-shear 62500.0

block mechanical damping global

;_______SAVE ANALYSIS_______________________________________________________
    model save "./init.sav" compress
;___________________________________________________________________________

;_______RESTORE ANALYSIS____________________________________________________
    model restore "./init.sav"
;___________________________________________________________________________

;GRAVITY APPLIED IN 10 STEPS 
;^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
;_____GRAVITY_____ step 1
model gravity 0 0 -0.981
model solve ratio-local 1e-06 time 0.02
;_____GRAVITY_____ step 2
model gravity 0 0 -1.962
model solve ratio-local 1e-06 time 0.02
;_____GRAVITY_____ step 3
model gravity 0 0 -2.943
model solve ratio-local 1e-06 time 0.02
;_____GRAVITY_____ step 4
model gravity 0 0 -3.924
model solve ratio-local 1e-06 time 0.02
;_____GRAVITY_____ step 5
model gravity 0 0 -4.905
model solve ratio-local 1e-06 time 0.02
;_____GRAVITY_____ step 6
model gravity 0 0 -5.886
model solve ratio-local 1e-06 time 0.02
;_____GRAVITY_____ step 7
model gravity 0 0 -6.867
model solve ratio-local 1e-06 time 0.02
;_____GRAVITY_____ step 8
model gravity 0 0 -7.848
model solve ratio-local 1e-06 time 0.02
;_____GRAVITY_____ step 9
model gravity 0 0 -8.829
model solve ratio-local 1e-06 time 0.02
;_____GRAVITY_____ step 10
model gravity 0 0 -9.81
model solve ratio-local 1e-06 time 0.02
model solve ratio-local 1e-06 time 1
;^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

;_______SAVE ANALYSIS_______________________________________________________
    model save "./grav.sav" compress
;___________________________________________________________________________

""")

import os
import vec
import json
import itasca as it
# ==============================================================================
## access 3DEC results and extrapolate data
# ==============================================================================
# list of list (list of blocks, and in each block there is a list of gridpoints)
# BLOCKS LIST

def blocks_3dec_output(name):
    elements = []
    for b in it.block.list():
        element_dict = {
        "id" : b.id()-1,
        "vertices" : [],
        "unbalanced_force"  : [],
        "velocity"          : [],
        "density"           : None,
        "mass"              : None,
        "weight"            : None,
        }
        # vertices list
        gridp_list = it.block.Block.gridpoints(b)
        for g in gridp_list:
            vector_g = it.block.gridpoint.Gridpoint.pos(g)
            vector_g_coord = vec.vec3.x(vector_g), vec.vec3.y(vector_g), vec.vec3.z(vector_g)
            element_dict["vertices"].append(vector_g_coord)

        # unbalanced force
        unbalanced_force = it.block.Block.force_unbal(b)
        unbalanced_force_vec = vec.vec3.x(unbalanced_force), vec.vec3.y(unbalanced_force), vec.vec3.z(unbalanced_force)
        element_dict["unbalanced_force"] = unbalanced_force_vec

        # velocity
        velocity = it.block.Block.velocity(b)
        velocity = vec.vec3.x(velocity), vec.vec3.y(velocity), vec.vec3.z(velocity)
        element_dict["velocity"] = velocity

        # density
        density = it.block.Block.density(b)
        element_dict["density"] = density

        # mass
        mass = it.block.Block.mass(b)
        element_dict["mass"] = mass

        # weight
        weight = (mass * 9.806) / 1000
        element_dict["weight"] = weight

        elements.append(element_dict)

    with open(r"c:\Users\adellend\Code2\compas_3dec\docs\examples\data1.json", "w") as json_file:
        json.dump(elements, json_file)
    return elements

elements = blocks_3dec_output("init")

