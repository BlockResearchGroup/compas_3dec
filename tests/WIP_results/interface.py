import os
import time
import compas
from adem.threedec import threedec_data_contact_step
# from adem.threedec import contact_forces_light_test
from adem.rhino import init_layers_wip3
import os
import time
import rhinoscriptsyntax as rs
import compas
from math import radians

from compas.datastructures import Mesh
from compas.geometry import centroid_points
from compas.geometry import norm_vector
from compas.geometry import cross_vectors
from compas.geometry import normalize_vector
from compas.geometry import scale_vector
from compas.geometry import sum_vectors
from compas.geometry import dot_vectors
from compas.geometry import angle_vectors
from compas.geometry import distance_point_point
from compas.geometry import length_vector
from compas.geometry import Vector
from compas.geometry import add_vectors
from compas.geometry import subtract_vectors
from compas.geometry import project_points_line
from compas.geometry import rotate_points
from compas.geometry import Plane
from compas.geometry import midpoint_line
from compas.geometry import Polyline
from compas.datastructures import mesh_slice_plane
from compas.utilities import geometric_key
from compas_assembly.datastructures import Block
from compas_rhino.artists import PolylineArtist
from adem.file_management import overwrite_file
from adem.rhino import mesh_view
from adem.threedec import data_from_threedec_contact
from adem.file_management import get_blocks_from_json_file_2
from adem.threedec import mesh_block_map_dict_concave
from adem.threedec import threedec_data_init_grav_step_concave
from adem.threedec import update_concave
from adem.threedec import threedec_data_contact_step
from adem.threedec import cracks
from compas.geometry import closest_point_in_cloud
from compas.colors import Color
from compas.colors import Color 
from compas.colors import ColorMap

azure = Color.azure()
pink = Color.pink()
white = Color.white()
grey = Color.grey()
blue = Color.blue()
red = Color.red()
cyan = Color.cyan()
cyan = cyan.darkened(8)
blue = blue.darkened(8)
grey = grey.lightened(50)
cmap = ColorMap.from_three_colors(azure, grey,pink)
# cmap = ColorMap.from_two_colors(,pink)




start = time.time()
HERE = os.path.dirname(__file__)
FILE3 = os.path.join(HERE, 'results_bkey_forces.json')
init_layers_wip3()

def get_key(my_dict, val):
    for key, value in my_dict.items():
         if val == value:
             return key


import os
import compas
import time
import math
import rhinoscriptsyntax as rs

from adem.file_management import get_blocks_from_json_file_2
from adem.threedec import mesh_block_map_dict_concave
from adem.threedec import threedec_data_init_grav_step_concave
from adem.threedec import update_concave
from adem.threedec import threedec_data_contact_step
from adem.threedec import contact_interface
# from adem.threedec import contact_forces_light_test
from adem.threedec import data_from_threedec_contact
from adem.rhino import mesh_view
from adem.rhino import init_layers_light


from compas.geometry import Vector
from compas.geometry import scale_vector
from compas.geometry import normalize_vector
from compas.geometry import centroid_points
from compas.geometry import cross_vectors
from compas.geometry import sum_vectors
from compas.geometry import dot_vectors
from compas.geometry import distance_point_point
from compas.geometry import Vector


from compas.geometry import centroid_points
from compas.geometry import norm_vector
from compas.geometry import cross_vectors
from compas.geometry import normalize_vector
from compas.geometry import scale_vector
from compas.geometry import sum_vectors
from compas.geometry import dot_vectors
from compas.geometry import angle_vectors
from compas.geometry import distance_point_point
from compas.geometry import length_vector
from compas.geometry import Vector
from compas.geometry import add_vectors
from compas.geometry import subtract_vectors
from compas.geometry import project_points_line
from compas.geometry import rotate_points
from compas.geometry import Plane
from compas.geometry import midpoint_line
from compas.geometry import Polyline
from compas.datastructures import mesh_slice_plane
from compas.utilities import geometric_key
from compas_assembly.datastructures import Block


# ==============================================================================
# Initialise folders and layers
# ==============================================================================
start = time.time()
compas.PRECISION = '10'
DIR = os.path.dirname(__file__)
readpath = os.path.join(DIR, 'json_data')
HERE = os.path.dirname(__file__)
# init_layers()
init_layers_light()

block_json = 'blocks.json'
support_json = 'supports.json'
other_json = 'others.json'
displ_x = 0.0
displ_y = 0.0
displ_z = 0.0

# reaction output
WRITEPATH = os.path.join(DIR, 'to_zha')
HERE = os.path.dirname(__file__)

filename1 = 'forces.json'



def contact_forces_light_test(contact_file, scale_factor, region, friction_angle, threshold, arrow=False,Shear=False):
    # visualise contact forces acting on a single block in compression in only one region is given as argument
    # otherwise it visualises action and reaction forces in all blocks
    far = math.radians(friction_angle)
    mu = math.tan(far)
    contacts = data_from_threedec_contact(str(contact_file))
    points = []
    c_forces = []
    # loop per contact
    for contact in contacts:
        # check if the region is in the contact neighbours
        if (region in contacts[contact]['neighbours']) and (contacts[contact]['subcontacts']):
            if contacts[contact]['neighbours'][0] == region:
                s_dict = contacts[contact]['subcontacts']
                normal = scale_vector(contacts[contact]['normal'], -1)
            else:
                s_dict = contacts[contact]['subcontacts']
                normal = contacts[contact]['normal']
            # get the vertices [x,y,z] of the contact face and create a list

            verts = [s_dict[sub]['coordinates'] for sub in s_dict]
            centroid = centroid_points(verts)

            # 3DEC results post-processing 1st part
            for sub in s_dict:
                if s_dict[sub]['normal_force']:
                    vertex = s_dict[sub]['coordinates']
                    e1_plane = normalize_vector(
                        (vertex[0] - centroid[0], vertex[1] - centroid[1], vertex[2] - centroid[2]))
                    e2_plane = cross_vectors(normal, e1_plane)
                    break
            MtorqueG = [0, 0, 0]
            Mtot = [0, 0, 0]
            Ntot = 0
            Stot = [0, 0, 0]

            # list of shear forces used later for pure shear calculation (no transportation couple)
            slist = []
            # 3DEC results post-processing 2nd part
            for sub in s_dict:
                vertex = s_dict[sub]['coordinates']
                ri = ((vertex[0] - centroid[0], vertex[1] -
                        centroid[1], vertex[2] - centroid[2]))
                Ni = s_dict[sub]['normal_force']

                # 3DEC results post-processing 2nd part
                Mi = cross_vectors(ri, scale_vector(normal, Ni))
                Mtot = sum_vectors([Mtot, Mi])
                Ntot = Ntot + Ni
                # check position of the region(block) to switch shear forces direction
                if contacts[contact]['neighbours'][0] == region:
                    Si = (-1 * (s_dict[sub]['shear_force'][0]), -1 * (s_dict[sub]
                                                                        ['shear_force'][1]), -1 * (s_dict[sub]['shear_force'][2]))
                    Stot = (sum_vectors([Stot, Si]))
                    slist.append(Si)
                    # calculate torque
                    MtorqueGi = cross_vectors(ri, Si)
                    MtorqueG = sum_vectors([MtorqueG, MtorqueGi])
                else:
                    Si = s_dict[sub]['shear_force']
                    Stot = (sum_vectors([Stot, Si]))
                    slist.append(Si)
                    # calculate torque
                    MtorqueGi = cross_vectors(ri, Si)
                    MtorqueG = sum_vectors([MtorqueG, MtorqueGi])

            # 3DEC results post-processing 3rd part
            if Ntot > threshold:
                # compute the resultant contact force
                Ftot = sum_vectors([Stot, scale_vector(normal, Ntot)])
                c_forces.append(Ftot)

                NN = scale_vector(normal, Ntot)
                b2 = dot_vectors(Mtot, e1_plane) / Ntot
                b1 = -1 * dot_vectors(Mtot, e2_plane) / Ntot

                # point of application of the resultant contact force
                po = sum_vectors([centroid, scale_vector(
                    e1_plane, b1), scale_vector(e2_plane, b2)])
                points.append(po)

                Mtorquepo = sum_vectors([MtorqueG, cross_vectors(
                sum_vectors([centroid, scale_vector(po, -1)]), Stot)])

                # contact forces visualisation
                end_point_2 = sum_vectors(
                    [po, scale_vector(Ftot, -scale_factor)])
                end_point_4 = sum_vectors(
                    [po, scale_vector(NN, -scale_factor)])
                end_point_6 = sum_vectors(
                    [po, scale_vector(Stot, -scale_factor)])
                end_point_21 = sum_vectors(
                [po, scale_vector(Mtorquepo, -scale_factor)])

                rs.CurrentLayer('Thrust_pt')
                rs.AddPoint(po)

                rs.CurrentLayer('Thrust')
                if distance_point_point(po, end_point_2) > 0.0001:
                    th1 = rs.AddLine(po, end_point_2)
                    if arrow:
                        rs.CurveArrows(th1, 1)

                rs.CurrentLayer('Thrust_N')
                if distance_point_point(po, end_point_4) > 0.0001:
                    tn1 = rs.AddLine(po, end_point_4)
                    if arrow:
                        rs.CurveArrows(tn1, 1)

                rs.CurrentLayer('Thrust_S')
                if distance_point_point(po, end_point_6) > 0.0001:
                    ts1 = rs.AddLine(po, end_point_6)
                    if arrow:
                        rs.CurveArrows(ts1, 1)

                rs.CurrentLayer('Torque')
                if distance_point_point(po, end_point_21) > 0.0001:
                    to1 = rs.AddLine(po, end_point_21)
                    if arrow:
                        rs.CurveArrows(to1, 1)

    rs.CurrentLayer('Default')
    rs.LayerVisible('Thrust', False)
    rs.LayerVisible('Thrust_N', False)
    rs.LayerVisible('Thrust_S', False)
    rs.LayerVisible('Thrust_pt', False)
    rs.LayerVisible('Torque', False)

    return [c_forces], [points]
    
def new_contact_interface(contact_file, scale_factor, threshold):
    contacts = data_from_threedec_contact(str(contact_file))
    points = []
    for contact in contacts:
        if contacts[contact]['subcontacts']:
            s_dict = contacts[contact]['subcontacts']
            normal = contacts[contact]['normal']
            verts = []
            for sub in s_dict:
                vertex = s_dict[sub]['coordinates']
                verts.append(vertex)

            centroid = centroid_points(verts)
            for sub in s_dict:
                # I have addedd two zeros otherwise does not calculate e1_plane and e2_plane, before was > 0.0001
                if s_dict[sub]['normal_force'] > 0.000001:
                    vertex = s_dict[sub]['coordinates']
                    e1_plane = normalize_vector(
                        (vertex[0] - centroid[0], vertex[1] - centroid[1], vertex[2] - centroid[2]))
                    e2_plane = cross_vectors(normal, e1_plane)
                    break

            Mtot = [0, 0, 0]
            Ntot = 0
            Stot = [0, 0, 0]

            for sub in s_dict:
                vertex = s_dict[sub]['coordinates']
                ri = ((vertex[0] - centroid[0], vertex[1] -
                       centroid[1], vertex[2] - centroid[2]))
                Ni = s_dict[sub]['normal_force']
                Mi = cross_vectors(ri, scale_vector(normal, Ni))
                Mtot = sum_vectors([Mtot, Mi])
                Ntot = Ntot + Ni
                Si = s_dict[sub]['shear_force']
                Stot = sum_vectors([Stot, Si])

            if Ntot >= threshold:

                Ftot = sum_vectors([Stot, scale_vector(normal, Ntot)])
                NN = scale_vector(normal, Ntot)
                b2 = dot_vectors(Mtot, e1_plane) / Ntot
                b1 = -1 * dot_vectors(Mtot, e2_plane) / Ntot

                po = sum_vectors([centroid, scale_vector(
                    e1_plane, b1), scale_vector(e2_plane, b2)])
                points.append(po)

                end_point_1 = sum_vectors(
                    [po, scale_vector(Ftot, scale_factor)])
                end_point_2 = sum_vectors(
                    [po, scale_vector(Ftot, -scale_factor)])

                end_point_3 = sum_vectors([po, scale_vector(NN, scale_factor)])
                end_point_4 = sum_vectors(
                    [po, scale_vector(NN, -scale_factor)])

                end_point_5 = sum_vectors(
                    [po, scale_vector(Stot, scale_factor)])
                end_point_6 = sum_vectors(
                    [po, scale_vector(Stot, -scale_factor)])

                rs.CurrentLayer('Thrust_pt')
                rs.AddPoint(po)

                rs.CurrentLayer('Thrust')
                th1 = rs.AddLine(po, end_point_1)
                th2 = rs.AddLine(po, end_point_2)

                rs.CurrentLayer('Thrust_N')
                tn1 = rs.AddLine(po, end_point_3)
                tn2 = rs.AddLine(po, end_point_4)

                rs.CurrentLayer('Thrust_S')
                if distance_point_point(po, end_point_5) > 0.001:
                    ts1 = rs.AddLine(po, end_point_5)
                    ts2 = rs.AddLine(po, end_point_6)

    rs.CurrentLayer('Default')
    rs.LayerVisible('Thrust', False)
    rs.LayerVisible('Thrust_N', False)
    rs.LayerVisible('Thrust_S', False)
    rs.LayerVisible('Thrust_pt', False)

    return Ftot

def new_contact_interface_color(contact_file, scale_factor, threshold, up_mesh):
    contacts = data_from_threedec_contact(str(contact_file))
    points = []
    c_forces = []
    fkeys = {}
    for contact in contacts:
        if contacts[contact]['subcontacts']:
            s_dict = contacts[contact]['subcontacts']
            normal = contacts[contact]['normal']
            verts = [s_dict[sub]['coordinates'] for sub in s_dict]
            centroid = centroid_points(verts)
            neighbour_1 = up_mesh[contacts[contact]['neighbours'][0]]['mesh']
            cen_m = [neighbour_1.face_centroid(fkey) for fkey in neighbour_1.faces()]
            a,b,c = closest_point_in_cloud(centroid,cen_m)
            for fkey in neighbour_1.faces():
                coord = neighbour_1.face_centroid(fkey)
                gkey = geometric_key(coord)
                fkeys[gkey] = fkey
            kk = fkeys[geometric_key(b)]
            neighbour_2 = up_mesh[contacts[contact]['neighbours'][1]]['mesh']
            cen_m = [neighbour_2.face_centroid(fkey) for fkey in neighbour_2.faces()]
            d,e,f = closest_point_in_cloud(centroid,cen_m)
            for fkey in neighbour_2.faces():
                coord = neighbour_2.face_centroid(fkey)
                gkey = geometric_key(coord)
                fkeys[gkey] = fkey
            kk2 = fkeys[geometric_key(e)]






            for sub in s_dict:
                # I have addedd two zeros otherwise does not calculate e1_plane and e2_plane, before was > 0.0001
                if s_dict[sub]['normal_force'] > 0.000001:
                    vertex = s_dict[sub]['coordinates']
                    e1_plane = normalize_vector(
                        (vertex[0] - centroid[0], vertex[1] - centroid[1], vertex[2] - centroid[2]))
                    e2_plane = cross_vectors(normal, e1_plane)
                    break

            Mtot = [0, 0, 0]
            Ntot = 0
            Stot = [0, 0, 0]

            for sub in s_dict:
                vertex = s_dict[sub]['coordinates']
                ri = ((vertex[0] - centroid[0], vertex[1] -
                       centroid[1], vertex[2] - centroid[2]))
                Ni = s_dict[sub]['normal_force']
                Mi = cross_vectors(ri, scale_vector(normal, Ni))
                Mtot = sum_vectors([Mtot, Mi])
                Ntot = Ntot + Ni
                Si = s_dict[sub]['shear_force']
                Stot = sum_vectors([Stot, Si])

            if Ntot >= threshold:

                Ftot = sum_vectors([Stot, scale_vector(normal, Ntot)])
                c_forces.append(Ftot)
                NN = scale_vector(normal, Ntot)
                b2 = dot_vectors(Mtot, e1_plane) / Ntot
                b1 = -1 * dot_vectors(Mtot, e2_plane) / Ntot

                po = sum_vectors([centroid, scale_vector(
                    e1_plane, b1), scale_vector(e2_plane, b2)])
                points.append(po)


                pts = neighbour_1.face_coordinates(kk)
                pts2 = neighbour_2.face_coordinates(kk2)
                points_n = pts + pts2
                
                zs = []
                # for i in pts:
                for i in points_n:
                    z = i[2]
                    zs.append(z)
                tolerance = 0.01

                z_max = max(zs) + tolerance
                z_min = min(zs) - tolerance
                
                z_norm = (po[2]-z_min)/(z_max-z_min)
                z_norm = float("%.1f" % z_norm)
                # rs.CurrentLayer('Thrust_pt')
                # if z_norm >1:
                #     # rs.AddPoint(po)
                #     rs.AddPoints(pts)

                # print(z_max, z_min, po[2],z_norm)

                # print (z_norm)

                color = cmap(z_norm)
                rs.CurrentLayer('Thrust_pt')
                p_rhino = rs.AddPoint(po)
                rs.ObjectPrintColor(p_rhino,color.rgb255)


                



                    # if vertex[2] == z_max:
                    #     rs.CurrentLayer('Extradox')
                    #     rs.AddPoint(vertex)
                    # if vertex[2] == z_min:
                    #     rs.CurrentLayer('Intradox')
                    #     rs.AddPoint(vertex)
                    # if (vertex[2]<z_max) and (vertex[2]>z_min):
                    #     z_norm = (vertex[2]-z_min)/(z_max-z_min)






                end_point_1 = sum_vectors(
                    [po, scale_vector(Ftot, scale_factor)])
                end_point_2 = sum_vectors(
                    [po, scale_vector(Ftot, -scale_factor)])

                end_point_3 = sum_vectors([po, scale_vector(NN, scale_factor)])
                end_point_4 = sum_vectors(
                    [po, scale_vector(NN, -scale_factor)])

                end_point_5 = sum_vectors(
                    [po, scale_vector(Stot, scale_factor)])
                end_point_6 = sum_vectors(
                    [po, scale_vector(Stot, -scale_factor)])

                # rs.CurrentLayer('Thrust_pt')
                # rs.AddPoint(po)

                rs.CurrentLayer('Thrust')
                th1 = rs.AddLine(po, end_point_1)
                rs.ObjectPrintColor(th1,color.rgb255)
                th2 = rs.AddLine(po, end_point_2)
                rs.ObjectPrintColor(th2,color.rgb255)

                rs.CurrentLayer('Thrust_N')
                tn1 = rs.AddLine(po, end_point_3)
                tn2 = rs.AddLine(po, end_point_4)

                rs.CurrentLayer('Thrust_S')
                if distance_point_point(po, end_point_5) > 0.001:
                    ts1 = rs.AddLine(po, end_point_5)
                    ts2 = rs.AddLine(po, end_point_6)

    rs.CurrentLayer('Default')
    rs.LayerVisible('Thrust', False)
    rs.LayerVisible('Thrust_N', False)
    rs.LayerVisible('Thrust_S', False)
    rs.LayerVisible('Thrust_pt', False)

    return Ftot


displ_x = 0.0
displ_y = 0.0
displ_z = 0.0
for n in range(26,27):
    filename = threedec_data_contact_step(n, displ_x, displ_y, displ_z)
    # get geometry from json
    support_blocks = get_blocks_from_json_file_2(HERE, 'supports.json')
    compound_blocks = get_blocks_from_json_file_2(HERE, 'blocks.json')
    # mapping + mechanical update
    blocks, blocks_grav, blocks_step = threedec_data_init_grav_step_concave(
        'init_state.txt', 'grav_state.txt', n, 0.0, 0.0, 0.0, True)
    bindex_mindex = mesh_block_map_dict_concave(blocks, support_blocks, compound_blocks,2,3)
    up_mesh = update_concave(bindex_mindex, blocks_step,10)
    # new_contact_interface_color(filename,0.00004,500,up_mesh)
    for bkey in up_mesh.keys():
        if up_mesh[bkey]['status'] == 'in':
            mesh = up_mesh[bkey]['mesh']
            if up_mesh[bkey]['layer'] == 'Layer 1':
                rs.CurrentLayer('Layer 1')
            if up_mesh[bkey]['layer'] == 'Layer 2':
                rs.CurrentLayer('Layer 2')
            if up_mesh[bkey]['layer'] == 'Layer 3':
                rs.CurrentLayer('Layer 3')
            if up_mesh[bkey]['layer'] == 'Layer 4':
                rs.CurrentLayer('Layer 4')
            if up_mesh[bkey]['layer'] == 'Layer 5':
                rs.CurrentLayer('Layer 5')
            if up_mesh[bkey]['layer'] == 'Layer 6':
                rs.CurrentLayer('Layer 6')
            if up_mesh[bkey]['layer'] == 'Layer 7':
                rs.CurrentLayer('Layer 7')
            if up_mesh[bkey]['layer'] == 'Layer 8':
                rs.CurrentLayer('Layer 8')
            if up_mesh[bkey]['layer'] == 'Support':
                rs.CurrentLayer('Support')
            # mesh_view(mesh)
            if up_mesh[bkey]['layer'] == 'Slaves':
                rs.CurrentLayer('Slaves')
        mesh_view(mesh)


    new_contact_interface_color(filename,0.00002,100,up_mesh)


# bkey_forces = {}
# for bkey in range(0,14):
#     bkey_forces[bkey] = {
#     'c_forces'      : [],selpt
#     'points'        : [],
#     'cont_cens'     : []

#     }
#     c_forces, points, cont_cens, f_c = contact_forces_light_test(filename, 0.00001, bkey, 1.0,  False)

# # for i in cont_cens[0]:
# #     rs.AddPoint(i)
#     bkey_forces[bkey]['c_forces'] = c_forces
#     bkey_forces[bkey]['points' ] = points
#     bkey_forces[bkey]['cont_cens'] = cont_cens
#     bkey_forces[bkey]['f_c'] = f_c

# #     bkey_forces[bkey]['cents'] = cents

# compas.json_dump(bkey_forces, FILE3)

end = time.time()
print('analysis_3dec time',end - start)