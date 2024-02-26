import os


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


def threedec7_mesh_description(meshes, indices, group=None, precision=10):
    # create blocks
    # ***************************************************************************
    unit_scale = 1.0
    block_description = ""
    for i, mesh in enumerate(meshes):
        face_description = ""  # should not work with sub_blocks
        for face in mesh.faces():
            # add new face
            face_description += "face "
            # get the vertices of the face in order!
            vertices = mesh.face_vertices(face)
            # reverse vertex order for 3DEC
            vertices.reverse()
            # add the vertices of this face
            for vertex in vertices:
                vertex_coordinates = mesh.vertex_coordinates(vertex)
                face_description += "{0:.{3}f},{1:.{3}f},{2:.{3}f} ".format(
                    vertex_coordinates[0] / unit_scale,
                    vertex_coordinates[1] / unit_scale,
                    vertex_coordinates[2] / unit_scale,
                    precision,
                )
        # add all faces of the block to the block description
        sub_block_description = (
            "block create group " + '"' + str(group) + '"' + " poly %s r=%i" % (face_description, indices[i])
        )
        block_description += sub_block_description + "\n"
    if len(meshes) > 1:
        str_indices = [str(num) for num in indices]
        block_description += "block join range region " + " ".join(str_indices) + "\n"

    #     # join the sub blocks to a compound block by region

    return block_description





import os
import inspect

def check_and_delete_gravity_files(current_directory):
    # Get the current working directory


    # current_directory = os.getcwd()
    print(f"Checking in the current directory: {current_directory}")

    # List of files to check and potentially delete
    files_to_check = ['init_state.txt', 'grav_state.txt', 'contact_grav.txt']

    # Iterate through each file in the list
    for file_name in files_to_check:
        # Construct the full path to the file
        full_path = os.path.join(current_directory, file_name)

        # Check if the file exists
        if os.path.exists(full_path):
            # If the file exists, delete it
            os.remove(full_path)
            print(f"Deleted {file_name}")
        else:
            # If the file does not exist, print a message
            print(f"{file_name} does not exist in the current directory and was not deleted")


