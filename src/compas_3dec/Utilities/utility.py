import os
import time
# from compas_3dec.Utilities import blocks_output
# from compas_3dec.Utilities import save_blocks_output

from compas_3dec.Utilities.fish import blocks_output
from compas_3dec.Utilities.fish import save_blocks_output
from compas_3dec.Utilities.fish import save_analysis
from compas_3dec.Utilities.fish import restore_analysis
from compas_3dec.Utilities.fish import contacts_output
from compas_3dec.Utilities.fish import save_contacts_output

__all__ = ['overwrite_file',
           'threedec7_support_description',
           'threedec7_block_description',
           'main_file'
           ]


def overwrite_file(file_path, replace_string):
    # Overwrite existing file with replace_string

    if os.path.exists(file_path):
        if os.access(file_path, os.W_OK):
            f = open(file_path, 'w+')
            f.write(replace_string)
            f.close()
        else:
            "File write access denied..."
    else:
        with open(file_path, 'a+') as f:
            f.write(replace_string)



def threedec7_support_description(support_blocks, node, precision=10):
    # create supports
    # ***************************************************************************
    unit_scale = 1.0
    block_description = ''
    face_description = ''
    # for sub_block in support_blocks:
    for face in support_blocks.faces():
        # add new face
        face_description += 'face '
        # get the vertices of the face in order!
        vertices = support_blocks.face_vertices(face)
        # reverse vertex order for 3DEC
        vertices.reverse()
        # add the vertices of this face
        for vertex in vertices:
            vertex_coordinates = support_blocks.vertex_coordinates(vertex)
            face_description += '{0:.{3}f},{1:.{3}f},{2:.{3}f} '.format(
                vertex_coordinates[0] / unit_scale, vertex_coordinates[1] / unit_scale, vertex_coordinates[2] / unit_scale, precision)
        # add all faces of the block to the block description
    sub_block_description = 'block create group "Supports" poly %s r=%i' % (
            face_description, node)
    block_description += sub_block_description + '\n'
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
    block_description = ''
    # for sub_block in compound_blocks:
    face_description = ''  # should not work with sub_blocks
    for face in compound_blocks.faces():
        # add new face
        face_description += 'face '
        # get the vertices of the face in order!
        vertices = compound_blocks.face_vertices(face)
        # reverse vertex order for 3DEC
        vertices.reverse()
        # add the vertices of this face
        for vertex in vertices:
            vertex_coordinates = compound_blocks.vertex_coordinates(vertex)
            face_description += '{0:.{3}f},{1:.{3}f},{2:.{3}f} '.format(
                vertex_coordinates[0] / unit_scale, vertex_coordinates[1] / unit_scale, vertex_coordinates[2] / unit_scale, precision)
    # add all faces of the block to the block description
    sub_block_description = 'block create group ' + '"'+str(group)+'"' +' poly %s r=%i' % (
        face_description,node)
    block_description += sub_block_description + '\n'
    # if len(compound_blocks) > 1:
    #     # join the sub blocks to a compound block by region
    #     block_description += 'join range region=%i \n \n' % (region)
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

def main_file(MechParam, path, title):
    parameters = MechParam.standard_material()
    name = 'main.dat'
    main_path = os.path.join(path, name)
    main_string = ';' + time.strftime("%d/%m/%Y") + ' ' + time.strftime("%H:%M:%S")
    create_header = """
    model new
    model large-strain on
    program call 'support_geometry.dat'
    program call 'block_geometry.dat'

    block contact generate-subcontacts
    block property density {0} range group 'Supports'
    block contact property stiffness-normal {1} stiffness-shear {2} friction {3}
    block contact material-table default property stiffness-normal {1} stiffness-shear {2}
    block fix range group 'Supports'

    block property density 1000 range group 'Alex'
    block contact generate-subcontacts
    block contact property stiffness-normal {1} stiffness-shear {2} friction {3}
    block contact material-table default property stiffness-normal {1} stiffness-shear {2}

    block mechanical damping {4}

    plot create
    plot clear
    plot active on
    plot background 'white'
    plot item create block
    """.format(parameters.parameters['density'], parameters.parameters['jkn'], parameters.parameters['jks'], parameters.parameters['friction'], 'global')
    main_string += create_header
    main_string += blocks_output()
    main_string += save_blocks_output('init')
    main_string += contacts_output()
    main_string += save_contacts_output('init')
    main_string += save_analysis(title,'init')
    main_string += restore_analysis(title,'init')
    main_string += """
    model gravity 0 0 -9.806
    model solve ratio-local 1e-06
    """
    main_string += save_blocks_output('grav')
    main_string += save_contacts_output('grav')
    main_string += save_analysis(title,'grav')
    overwrite_file(name, main_string)
    return
