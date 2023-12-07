import os
import time

# from compas_3dec.Utilities import blocks_output
# from compas_3dec.Utilities import save_blocks_output

from compas.geometry import Vector
from compas.geometry import normalize_vector
from compas.geometry import midpoint_point_point
from compas.geometry import scale_vector

from compas_3dec.utilities.fish import blocks_output
from compas_3dec.utilities.fish import save_blocks_output
from compas_3dec.utilities.fish import save_analysis
from compas_3dec.utilities.fish import restore_analysis
from compas_3dec.utilities.fish import contacts_output
from compas_3dec.utilities.fish import save_contacts_output

__all__ = [
    "overwrite_file",
    "threedec7_support_description",
    "threedec7_block_description",
    "get_key",
    "solve_ratio",
    "timestep",
    "displacement_settings",
    "cycle_displ_n",
    "displ_region",
    "displ_region_equ",
    "displacement_concave",
    "displacement_file",
    "remove_duplicate_points",
    "sum_duplicate_dict",
    "sum_duplicate_dict_vectors",
    "find_duplicate_dict",
]


def overwrite_file(file_path, replace_string):
    # Overwrite existing file with replace_string

    if os.path.exists(file_path):
        if os.access(file_path, os.W_OK):
            f = open(file_path, "w+")
            f.write(replace_string)
            f.close()
        else:
            "File write access denied..."
    else:
        with open(file_path, "a+") as f:
            f.write(replace_string)


def threedec7_support_description(support_blocks, node, precision=10):
    # create supports
    # ***************************************************************************
    unit_scale = 1.0
    block_description = ""
    face_description = ""
    # for sub_block in support_blocks:
    for face in support_blocks.faces():
        # add new face
        face_description += "face "
        # get the vertices of the face in order!
        vertices = support_blocks.face_vertices(face)
        # reverse vertex order for 3DEC
        vertices.reverse()
        # add the vertices of this face
        for vertex in vertices:
            vertex_coordinates = support_blocks.vertex_coordinates(vertex)
            face_description += "{0:.{3}f},{1:.{3}f},{2:.{3}f} ".format(
                vertex_coordinates[0] / unit_scale,
                vertex_coordinates[1] / unit_scale,
                vertex_coordinates[2] / unit_scale,
                precision,
            )
        # add all faces of the block to the block description
    sub_block_description = 'block create group "Supports" poly %s r=%i' % (face_description, node)
    block_description += sub_block_description + "\n"
    # print block_description
    # block_description += 'fix range region=%i \n \n' % (region)
    return block_description


# old script
# def threedec7_support_description(support_blocks, material, region, precision=10):
#     # create supports
#     # ***************************************************************************
#     unit_scale = 1.0
#     block_description = ''
#     face_description = ''
#     # for sub_block in support_blocks:
#     for face in support_blocks.faces():
#         # add new face
#         face_description += 'face '
#         # get the vertices of the face in order!
#         vertices = support_blocks.face_vertices(face)
#         # reverse vertex order for 3DEC
#         vertices.reverse()
#         # add the vertices of this face
#         for vertex in vertices:
#             vertex_coordinates = support_blocks.vertex_coordinates(vertex)
#             face_description += '{0:.{3}f},{1:.{3}f},{2:.{3}f} '.format(
#                 vertex_coordinates[0] / unit_scale, vertex_coordinates[1] / unit_scale, vertex_coordinates[2] / unit_scale, precision)
#         # add all faces of the block to the block description
#     sub_block_description = 'block create group "Supports" poly %s r=%i m=%i' % (
#             face_description, region, material)
#     block_description += sub_block_description + '\n'
#     # print block_description
#     # block_description += 'fix range region=%i \n \n' % (region)
#     return block_description


def threedec7_block_description(compound_blocks, group, node, precision=10):
    # create blocks
    # ***************************************************************************
    unit_scale = 1.0
    block_description = ""
    # for sub_block in compound_blocks:
    face_description = ""  # should not work with sub_blocks
    for face in compound_blocks.faces():
        # add new face
        face_description += "face "
        # get the vertices of the face in order!
        vertices = compound_blocks.face_vertices(face)
        # reverse vertex order for 3DEC
        vertices.reverse()
        # add the vertices of this face
        for vertex in vertices:
            vertex_coordinates = compound_blocks.vertex_coordinates(vertex)
            face_description += "{0:.{3}f},{1:.{3}f},{2:.{3}f} ".format(
                vertex_coordinates[0] / unit_scale,
                vertex_coordinates[1] / unit_scale,
                vertex_coordinates[2] / unit_scale,
                precision,
            )
    # add all faces of the block to the block description
    sub_block_description = "block create group " + '"' + str(group) + '"' + " poly %s r=%i" % (face_description, node)
    block_description += sub_block_description + "\n"
    # if len(compound_blocks) > 1:
    #     # join the sub blocks to a compound block by region
    # block_description += 'join range region=%i \n \n' % (node)
    return block_description


# old_script
# def threedec7_block_description(compound_blocks, material, region, precision=10):
#     # create blocks
#     # ***************************************************************************
#     unit_scale = 1.0
#     block_description = ''
#     # for sub_block in compound_blocks:
#     face_description = ''  # should not work with sub_blocks
#     for face in compound_blocks.faces():
#         # add new face
#         face_description += 'face '
#         # get the vertices of the face in order!
#         vertices = compound_blocks.face_vertices(face)
#         # reverse vertex order for 3DEC
#         vertices.reverse()
#         # add the vertices of this face
#         for vertex in vertices:
#             vertex_coordinates = compound_blocks.vertex_coordinates(vertex)
#             face_description += '{0:.{3}f},{1:.{3}f},{2:.{3}f} '.format(
#                 vertex_coordinates[0] / unit_scale, vertex_coordinates[1] / unit_scale, vertex_coordinates[2] / unit_scale, precision)
#     # add all faces of the block to the block description
#     sub_block_description = 'block create poly %s r=%i m=%i' % (
#         face_description, region, material)
#     block_description += sub_block_description + '\n'
#     # if len(compound_blocks) > 1:
#     #     # join the sub blocks to a compound block by region
#     #     block_description += 'join range region=%i \n \n' % (region)
#     return block_description

def get_key(my_dict, val):
    for key, value in my_dict.items():
        if val == value:
            return key


def solve_ratio(filename):
    with open(str(filename), "r") as fo:
        for line in fo:
            line = line.strip()
            if not line:
                continue
            parts = line.split()
            if not len(parts):
                continue
            if parts[0] == "solve":
                solve_r = float(parts[3])
                if solve_r <= 1.0000e-06:
                    print("Equilibrium reached")
                    print("solve ratio = " + str(solve_r))
                else:
                    print("Equilibrium NOT reached")
                    print("solve ratio = " + str(solve_r))
    return


def timestep(filename):
    with open(str(filename), "r") as fo:
        for line in fo:
            line = line.strip()
            if not line:
                continue
            parts = line.split()
            if not len(parts):
                continue
            if parts[0] == "timestep":
                times = float(parts[2])
                # print ('timestep = ' + str(times))
    return times


def displacement_settings():
    import compas_rhino
    import rhinoscriptsyntax as rs
    from compas_rhino.geometry import RhinoMesh
    from compas_rhino.geometry import RhinoPoint
    from compas_rhino.utilities import select_mesh
    from compas_rhino.utilities import select_point

    region = compas_rhino.rs.GetString("Input Block's number")
    b_to_move = select_mesh("Select block to be moved")
    b_to_move = RhinoMesh.from_guid(b_to_move)
    b_to_move = b_to_move.to_compas()
    centroid = b_to_move.centroid()
    end_vec = select_point("Select end vector point")
    end_vec = RhinoPoint.from_guid(end_vec)
    end_vec = end_vec.to_compas()
    rs.AddLayer("Displacement")
    rs.CurrentLayer("Displacement")
    d_line = rs.AddLine(centroid, end_vec)
    rs.CurveArrows(d_line, 2)
    displ_dir = normalize_vector(Vector.from_start_end(centroid, end_vec))
    displacement = compas_rhino.rs.GetString("Input total displacement")
    n_step = compas_rhino.rs.GetString("Input number of steps")
    text = str(displacement) + " m"
    d_tag = rs.AddTextDot(text, midpoint_point_point(centroid, end_vec))
    displ_step = float(displacement) / float(n_step)
    displ_dir = scale_vector(displ_dir, displ_step)
    return displacement, displ_step, n_step, displ_dir, region

    # print ('x ' + str(vec[0])+' y '+ str(vec[1])+' z '+ str(vec[2]))


def cycle_displ_n(displacement, timestep):
    """Calculate cycles needed to achieve a certain displacement.
    displacement: float
        displacement in meters to apply at the block.

    velocity: float
        velocity of the displacement in m/s.

    timestep: float
        timestep from 3DEC after running 1 cycle. It depends from the model
        and from the joint stiffness.
    """
    velocity = displacement
    cycle = displacement / (velocity * timestep)
    cycle = int(cycle)
    # print ('cycle =', cycle)
    return cycle


def displ_region(d_vector, region):
    # define displacement in mm
    x_vel = d_vector[0]
    y_vel = d_vector[1]
    z_vel = d_vector[2]
    # apply displacement to region
    header = "block apply velocity-x " + str(x_vel) + " range id " + str(region) + "\n"
    header += "block apply velocity-y " + str(y_vel) + " range id " + str(region) + "\n"
    header += "block apply velocity-z " + str(z_vel) + " range id " + str(region) + "\n"
    return header


def displ_region_equ(region):
    # define displacement in m
    x_vel = 0
    y_vel = 0
    z_vel = 0
    # apply displacement to region
    header = "block apply velocity-x " + str(x_vel) + " range id " + str(region) + "\n"
    header += "block apply velocity-y " + str(y_vel) + " range id " + str(region) + "\n"
    header += "block apply velocity-z " + str(z_vel) + " range id " + str(region) + "\n"
    return header


def displacement_concave(
    x_dis,
    y_dis,
    z_dis,
    n_of_regions,
    step,
    equ_time,
    cycle,
    d_vector,
    region,
    equil_check=False,
    block_centroid_result=True,
    contact=False,
):
    # generate step name
    step_name = (
        "x"
        + "_"
        + str(x_dis * step)
        + "mm"
        + "_"
        + "y"
        + "_"
        + str(y_dis * step)
        + "mm"
        + "_"
        + "z"
        + "_"
        + str(z_dis * step)
        + "mm"
    )
    header = ";____________________________________________________________________" + "\n"
    header += ";_____DISPLACEMENT_____" + " " + "Step" + "_" + str(step) + "___" + step_name + "\n"
    header += ";____________________________________________________________________" + "\n"
    header += displ_region(d_vector, region)
    header += "model cycle " + str(int(cycle)) + "\n"
    header += ";_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ " + "\n"
    header += ";FISH FUNCTIONS" + "\n"

    if block_centroid_result:
        text = save_blocks_output("step" + "_" + "0" + str(step) + "___" + step_name)
        header += text
        header += 2 * "\n"

    if contact:
        text1 = save_contacts_output("step" + "_contact_" + "0" + str(step) + "___" + step_name)
        header += text1
        header += 2 * "\n"

    if equil_check:
        header += ";_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ " + "\n"
        header += ";_____EQUILIBRIUM_CHECK_____" + "\n"
        header += displ_region_equ(region)
        header += "model solve unbalanced-maximum 0.00001 time" + " " + str(equ_time) + "\n"

    if block_centroid_result:
        text2 = save_blocks_output("step" + "_" + "0" + str(step) + "_equ__" + step_name)
        header += text2
        header += 2 * "\n"

    if contact:
        text3 = save_contacts_output("step" + "_contact_equ_" + "0" + str(step) + "__" + step_name)
        header += text3
        header += 2 * "\n"

    header += ";_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ " + "\n"
    name = str("step" + "_equ_" + "0" + str(step) + "__" + step_name)
    header += save_analysis(name, "d") + "\n"
    header += ";~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~" + "\n"
    return header


def displacement_file(
    writepath, n_steps, displ_x, displ_y, displ_z, n_region, equ_time, cycle, d_vector, title, region
):
    file_path = os.path.join(writepath, "displacement.dat")
    # Title
    main_string = ";Test" + " " + time.strftime("%d/%m/%Y") + " " + time.strftime("%H:%M:%S")
    main_string += 2 * "\n"
    # Import geometry
    main_string += restore_analysis(title, "grav")
    main_string += "block mechanical damping local"
    main_string += 2 * "\n"
    main_string += blocks_output()
    main_string += contacts_output()
    # displacement
    disp_step = list(range(1, int(n_steps) + 1, 1))
    for i in disp_step:
        main_string += displacement_concave(
            displ_x, displ_y, displ_z, n_region, i, equ_time, cycle, d_vector, region, True, True, True
        )
        main_string += 2 * "\n"
    # save file
    main_string += save_analysis(title, "displ")
    main_string += 2 * "\n"
    main_string += "exit()"
    overwrite_file(file_path, main_string)
    return


def remove_duplicate_points(points, tolerance=0.00001):
    unique_points = []
    for point in points:
        is_unique = True
        for existing_point in unique_points:
            distance = sum((a - b) ** 2 for a, b in zip(point, existing_point)) ** 0.5
            if distance < tolerance:
                is_unique = False
                break
        if is_unique:
            unique_points.append(point)
    return unique_points


def sum_duplicate_dict(k, v):
    dict_name = {}
    for key, value in zip(k, v):
        if key in dict_name:
            dict_name[key] += value
        else:
            dict_name[key] = value
    return dict_name


def sum_duplicate_dict_vectors(k, v):
    dict_name = {}
    for key, value in zip(k, v):
        if key in dict_name:
            dict_name[key] = tuple(a + b for a, b in zip(dict_name[key], value))
        else:
            dict_name[key] = value
    return dict_name


def draw_forces(self, scale=1.0, tol=1e-3):
    """Draw the contact (normal) forces at the interfaces between the blocks of the assembly.

    Parameters
    ----------
    scale : float, optional
        Scale factor for the length of the vectors.
    tol : float, optional
        Minimum length requirement for displaying vectors.

    Returns
    -------
    list[System.Guid]

    """
    layer = "{}::Forces".format(self.layer or self.assembly.name)
    guids = []
    tension = Color.red().rgb255
    compression = Color.blue().rgb255
    friction = Color.cyan().rgb255
    for edge in self.edges:
        interfaces = self.assembly.edge_interfaces(edge)
        lines = []
        for interface in interfaces:
            for force in interface.compressionforces:
                vector = force.vector * scale * 0.5
                if vector.length > tol * 0.5:
                    point = force.midpoint
                    lines.append(
                        {
                            "start": list(point - vector),
                            "end": list(point + vector),
                            "color": compression,
                        }
                    )
            for force in interface.tensionforces:
                vector = force.vector * scale * 0.5
                if vector.length > tol * 0.5:
                    point = force.midpoint
                    lines.append(
                        {
                            "start": list(point - vector),
                            "end": list(point + vector),
                            "color": tension,
                        }
                    )
            for force in interface.frictionforces:
                vector = force.vector * scale * 0.5
                if vector.length > tol * 0.5:
                    point = force.midpoint
                    lines.append(
                        {
                            "start": list(point - vector),
                            "end": list(point + vector),
                            "color": friction,
                        }
                    )
        guids += compas_rhino.draw_lines(lines, layer=layer, clear=False, redraw=False)
    return guids


def find_duplicate_dict(block_dict):
    group_values = {}
    for block_name, group_name in block_dict.items():
        block_name_str = str(block_name)
        if group_name in group_values:
            # If yes, append the block name to the existing list
            group_values[group_name].append(block_name_str)
        else:
            # If no, create a new list with the current block name
            group_values[group_name] = [block_name_str]
    join = []
    for group_name, block_names in group_values.items():
        if len(block_names) > 1:
            joined_block_names = " ".join(block_names)
            join.append(joined_block_names)
    return join
