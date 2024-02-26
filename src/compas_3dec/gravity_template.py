import os

def gravity_template(config, path):
    content = """# This is a sample Python file generated programmatically
import itasca as it
it.command(\"\"\"
{0}
\"\"\")

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
        element_dict = {{
        "id" : b.id()-1,
        "vertices" : [],
        "unbalanced_force"  : [],
        "velocity"          : [],
        "density"           : None,
        "mass"              : None,
        "weight"            : None,
        }}
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

    with open(r"{1}", "w") as json_file:
        json.dump(elements, json_file)
    return elements

elements = blocks_3dec_output("init")

    """.format(config,path)
    return content
