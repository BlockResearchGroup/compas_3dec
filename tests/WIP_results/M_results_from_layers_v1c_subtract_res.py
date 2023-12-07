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
compas.PRECISION = "10"
DIR = os.path.dirname(__file__)
readpath = os.path.join(DIR, "json_data")
HERE = os.path.dirname(__file__)
# init_layers()
init_layers_light()

block_json = "blocks.json"
support_json = "supports.json"
other_json = "others.json"
displ_x = 0.0
displ_y = 0.0
displ_z = 0.0

# reaction output
WRITEPATH = os.path.join(DIR, "to_zha")
HERE = os.path.dirname(__file__)

filename1 = "forces.json"


def update_concave_resultants(bindex_mindex, step_n, scale_factor):  # step n is the threedec dict at step n
    # CCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC
    vault_weight = 0
    for bkey in step_n.keys():
        if bindex_mindex[bkey]["type"] == "block":
            vault_weight += step_n[bkey]["mass"] * 9.806
        else:
            vault_weight += 0.0
    # CCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC

    for bkey in bindex_mindex.keys():
        if bkey in step_n.keys() and step_n[bkey]["mass"] != 0:
            bindex_mindex[bkey]["weight"] = step_n[bkey]["mass"] * 9.806
            bindex_mindex[bkey]["unb_force"] = norm_vector(step_n[bkey]["force"])

            if bindex_mindex[bkey]["type"] == "block":
                bindex_mindex[bkey]["unb_f_ratio"] = bindex_mindex[bkey]["unb_force"] / bindex_mindex[bkey]["weight"]

                res_block = bindex_mindex[bkey]["unb_f_ratio"]
                if res_block <= 0.001:
                    bindex_mindex[bkey]["layer"] = "Layer 1"
                elif (res_block > 0.001) and (res_block <= 0.005):
                    bindex_mindex[bkey]["layer"] = "Layer 2"
                elif (res_block > 0.005) and (res_block <= 0.01):
                    bindex_mindex[bkey]["layer"] = "Layer 3"
                elif (res_block > 0.01) and (res_block <= 0.05):
                    bindex_mindex[bkey]["layer"] = "Layer 4"
                elif (res_block > 0.05) and (res_block <= 0.1):
                    bindex_mindex[bkey]["layer"] = "Layer 5"
                elif (res_block > 0.1) and (res_block <= 0.5):
                    bindex_mindex[bkey]["layer"] = "Layer 6"
                elif (res_block > 0.5) and (res_block <= 1):
                    bindex_mindex[bkey]["layer"] = "Layer 7"
                elif res_block > 1:
                    bindex_mindex[bkey]["layer"] = "Layer 8"

            else:
                f2 = (bindex_mindex[bkey]["unb_force"]) - ((bindex_mindex[bkey]["weight"]))
                bindex_mindex[bkey]["unb_f_ratio"] = f2 / vault_weight
                # bindex_mindex[bkey]['unb_f_ratio'] = (bindex_mindex[bkey]['unb_force'])/vault_weight
                res_support = bindex_mindex[bkey]["unb_f_ratio"]
                bindex_mindex[bkey]["layer"] = "Support"
                # bindex_mindex[bkey]['unb_f_ratio'] = bindex_mindex[bkey]['unb_force']/vault_weight
                # res_support = bindex_mindex[bkey]['unb_f_ratio']
                # bindex_mindex[bkey]['layer'] = 'Support'

            mesh = bindex_mindex[bkey]["mesh"]
            for vkey, attr in mesh.vertices(True):
                mindex = bindex_mindex[bkey]
                vkey_3dec = bindex_mindex[bkey]["map_verts"][vkey]
                attr["x"] = step_n[bkey]["vertices"][vkey_3dec][0]
                attr["y"] = step_n[bkey]["vertices"][vkey_3dec][1]
                attr["z"] = step_n[bkey]["vertices"][vkey_3dec][2]
        # else:
        #     bindex_mindex[bkey]['status'] = 'out'
        #     bindex_mindex[bkey]['layer'] = 'out'

        # this is ok since no blocks are falling
        # else:
        if bkey in step_n.keys() and step_n[bkey]["mass"] == 0:
            bindex_mindex[bkey]["layer"] = "Slaves"
            mesh = bindex_mindex[bkey]["mesh"]
            for vkey, attr in mesh.vertices(True):
                mindex = bindex_mindex[bkey]
                vkey_3dec = bindex_mindex[bkey]["map_verts"][vkey]
                attr["x"] = step_n[bkey]["vertices"][vkey_3dec][0]
                attr["y"] = step_n[bkey]["vertices"][vkey_3dec][1]
                attr["z"] = step_n[bkey]["vertices"][vkey_3dec][2]

    # LAYER FUNCTION
    # *******************************************************************************
    # *******************************************************************************

    rs.AddLayer("Resultants")
    rs.LayerColor("Resultants", (120, 120, 120))
    rs.DeleteObjects(rs.ObjectsByLayer("Resultants"))
    rs.AddLayer("Grid_weight")
    rs.LayerColor("Grid_weight", (255, 0, 0))
    rs.DeleteObjects(rs.ObjectsByLayer("Grid_weight"))
    rs.AddLayer("Result_value")
    rs.LayerColor("Result_value", (120, 120, 120))
    rs.DeleteObjects(rs.ObjectsByLayer("Result_value"))
    rs.AddLayer("Result_coord")
    rs.LayerColor("Result_coord", (120, 120, 120))
    rs.DeleteObjects(rs.ObjectsByLayer("Result_coord"))
    rs.CurrentLayer("Resultants")

    # *******************************************************************************
    # *******************************************************************************
    r_points = []
    r_vectors = []
    for bkey in bindex_mindex.keys():
        if bkey in step_n.keys():
            if bindex_mindex[bkey]["type"] == "support" and step_n[bkey]["mass"] != 0:
                ratio = (1 / vault_weight) * scale_factor
                cen = step_n[bkey]["centroid"]
                r_points.append(cen)

                force = step_n[bkey]["force"]
                force_r = force[0] / 1000, force[1] / 1000, force[2] / 1000

                force_r = (
                    "%.2f" % force_r[0],
                    "%.2f" % force_r[1],
                    "%.2f" % force_r[2],
                )

                force_mag = length_vector(force)
                force_mag = force_mag / 1000
                force_mag = "%.2f" % force_mag

                ff = (cen[0] + (force[0] * ratio), cen[1] + (force[1]) * ratio, cen[2] + (force[2]) * ratio)
                r_vectors.append(ff)
                aal = rs.AddLine(cen, ff)
                rs.CurveArrows(aal, 2)
                res_support = bindex_mindex[bkey]["unb_f_ratio"]
                rrr = round(res_support, 2)
                res_sup = "%.3f" % res_support

                rs.CurrentLayer("Result_value")
                # rs.AddTextDot(str(res_sup),ff)
                rs.AddTextDot(str(force_mag), ff)
                rs.CurrentLayer("Result_coord")
                # rs.AddTextDot(str(res_sup),ff)
                rs.AddTextDot(str(force_r), ff)
                rs.CurrentLayer("Resultants")

    rs.CurrentLayer("Default")
    rs.LayerVisible("Resultants", False)
    rs.LayerVisible("Result_value", False)
    rs.LayerVisible("Result_coord", False)

    return bindex_mindex, r_points, r_vectors


def contact_forces_light_test(contact_file, scale_factor, region, friction_angle, threshold, arrow=False, Shear=False):
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
        if (region in contacts[contact]["neighbours"]) and (contacts[contact]["subcontacts"]):
            if contacts[contact]["neighbours"][0] == region:
                s_dict = contacts[contact]["subcontacts"]
                normal = scale_vector(contacts[contact]["normal"], -1)
            else:
                s_dict = contacts[contact]["subcontacts"]
                normal = contacts[contact]["normal"]
            # get the vertices [x,y,z] of the contact face and create a list

            verts = [s_dict[sub]["coordinates"] for sub in s_dict]
            centroid = centroid_points(verts)

            # 3DEC results post-processing 1st part
            for sub in s_dict:
                if s_dict[sub]["normal_force"]:
                    vertex = s_dict[sub]["coordinates"]
                    e1_plane = normalize_vector(
                        (vertex[0] - centroid[0], vertex[1] - centroid[1], vertex[2] - centroid[2])
                    )
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
                vertex = s_dict[sub]["coordinates"]
                ri = (vertex[0] - centroid[0], vertex[1] - centroid[1], vertex[2] - centroid[2])
                Ni = s_dict[sub]["normal_force"]

                # 3DEC results post-processing 2nd part
                Mi = cross_vectors(ri, scale_vector(normal, Ni))
                Mtot = sum_vectors([Mtot, Mi])
                Ntot = Ntot + Ni
                # check position of the region(block) to switch shear forces direction
                if contacts[contact]["neighbours"][0] == region:
                    Si = (
                        -1 * (s_dict[sub]["shear_force"][0]),
                        -1 * (s_dict[sub]["shear_force"][1]),
                        -1 * (s_dict[sub]["shear_force"][2]),
                    )
                    Stot = sum_vectors([Stot, Si])
                    slist.append(Si)
                    # calculate torque
                    MtorqueGi = cross_vectors(ri, Si)
                    MtorqueG = sum_vectors([MtorqueG, MtorqueGi])
                else:
                    Si = s_dict[sub]["shear_force"]
                    Stot = sum_vectors([Stot, Si])
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
                po = sum_vectors([centroid, scale_vector(e1_plane, b1), scale_vector(e2_plane, b2)])
                points.append(po)

                Mtorquepo = sum_vectors([MtorqueG, cross_vectors(sum_vectors([centroid, scale_vector(po, -1)]), Stot)])

                # contact forces visualisation
                end_point_2 = sum_vectors([po, scale_vector(Ftot, -scale_factor)])
                end_point_4 = sum_vectors([po, scale_vector(NN, -scale_factor)])
                end_point_6 = sum_vectors([po, scale_vector(Stot, -scale_factor)])
                end_point_21 = sum_vectors([po, scale_vector(Mtorquepo, -scale_factor)])

                rs.CurrentLayer("Thrust_pt")
                rs.AddPoint(po)

                rs.CurrentLayer("Thrust")
                if distance_point_point(po, end_point_2) > 0.0001:
                    th1 = rs.AddLine(po, end_point_2)
                    if arrow:
                        rs.CurveArrows(th1, 1)

                rs.CurrentLayer("Thrust_N")
                if distance_point_point(po, end_point_4) > 0.0001:
                    tn1 = rs.AddLine(po, end_point_4)
                    if arrow:
                        rs.CurveArrows(tn1, 1)

                rs.CurrentLayer("Thrust_S")
                if distance_point_point(po, end_point_6) > 0.0001:
                    ts1 = rs.AddLine(po, end_point_6)
                    if arrow:
                        rs.CurveArrows(ts1, 1)

                rs.CurrentLayer("Torque")
                if distance_point_point(po, end_point_21) > 0.0001:
                    to1 = rs.AddLine(po, end_point_21)
                    if arrow:
                        rs.CurveArrows(to1, 1)

    rs.CurrentLayer("Default")
    rs.LayerVisible("Thrust", False)
    rs.LayerVisible("Thrust_N", False)
    rs.LayerVisible("Thrust_S", False)
    rs.LayerVisible("Thrust_pt", False)
    rs.LayerVisible("Torque", False)

    return [c_forces], [points]


def new_contact_interface(contact_file, scale_factor, threshold):
    contacts = data_from_threedec_contact(str(contact_file))
    points = []
    for contact in contacts:
        if contacts[contact]["subcontacts"]:
            s_dict = contacts[contact]["subcontacts"]
            normal = contacts[contact]["normal"]
            verts = []
            for sub in s_dict:
                vertex = s_dict[sub]["coordinates"]
                verts.append(vertex)

            centroid = centroid_points(verts)
            for sub in s_dict:
                # I have addedd two zeros otherwise does not calculate e1_plane and e2_plane, before was > 0.0001
                if s_dict[sub]["normal_force"] > 0.000001:
                    vertex = s_dict[sub]["coordinates"]
                    e1_plane = normalize_vector(
                        (vertex[0] - centroid[0], vertex[1] - centroid[1], vertex[2] - centroid[2])
                    )
                    e2_plane = cross_vectors(normal, e1_plane)
                    break

            Mtot = [0, 0, 0]
            Ntot = 0
            Stot = [0, 0, 0]

            for sub in s_dict:
                vertex = s_dict[sub]["coordinates"]
                ri = (vertex[0] - centroid[0], vertex[1] - centroid[1], vertex[2] - centroid[2])
                Ni = s_dict[sub]["normal_force"]
                Mi = cross_vectors(ri, scale_vector(normal, Ni))
                Mtot = sum_vectors([Mtot, Mi])
                Ntot = Ntot + Ni
                Si = s_dict[sub]["shear_force"]
                Stot = sum_vectors([Stot, Si])

            if Ntot >= threshold:
                Ftot = sum_vectors([Stot, scale_vector(normal, Ntot)])
                NN = scale_vector(normal, Ntot)
                b2 = dot_vectors(Mtot, e1_plane) / Ntot
                b1 = -1 * dot_vectors(Mtot, e2_plane) / Ntot

                po = sum_vectors([centroid, scale_vector(e1_plane, b1), scale_vector(e2_plane, b2)])
                points.append(po)

                end_point_1 = sum_vectors([po, scale_vector(Ftot, scale_factor)])
                end_point_2 = sum_vectors([po, scale_vector(Ftot, -scale_factor)])

                end_point_3 = sum_vectors([po, scale_vector(NN, scale_factor)])
                end_point_4 = sum_vectors([po, scale_vector(NN, -scale_factor)])

                end_point_5 = sum_vectors([po, scale_vector(Stot, scale_factor)])
                end_point_6 = sum_vectors([po, scale_vector(Stot, -scale_factor)])

                rs.CurrentLayer("Thrust_pt")
                rs.AddPoint(po)

                rs.CurrentLayer("Thrust")
                th1 = rs.AddLine(po, end_point_1)
                th2 = rs.AddLine(po, end_point_2)

                rs.CurrentLayer("Thrust_N")
                tn1 = rs.AddLine(po, end_point_3)
                tn2 = rs.AddLine(po, end_point_4)

                rs.CurrentLayer("Thrust_S")
                if distance_point_point(po, end_point_5) > 0.001:
                    ts1 = rs.AddLine(po, end_point_5)
                    ts2 = rs.AddLine(po, end_point_6)

    rs.CurrentLayer("Default")
    rs.LayerVisible("Thrust", False)
    rs.LayerVisible("Thrust_N", False)
    rs.LayerVisible("Thrust_S", False)
    rs.LayerVisible("Thrust_pt", False)

    return Ftot


def new_contact_interface_sub(contact_grav, contact_file, scale_factor, threshold):
    contacts = data_from_threedec_contact(str(contact_file))
    contacts_grav = data_from_threedec_contact(str(contact_grav))
    points = []

    for contact in contacts:
        if contacts[contact]["subcontacts"]:
            s_dict = contacts[contact]["subcontacts"]
            s_dict_g = contacts_grav[contact]["subcontacts"]
            normal = contacts[contact]["normal"]
            verts = []
            for sub in s_dict:
                vertex = s_dict[sub]["coordinates"]
                verts.append(vertex)

            centroid = centroid_points(verts)
            for sub in s_dict:
                # I have addedd two zeros otherwise does not calculate e1_plane and e2_plane, before was > 0.0001
                if s_dict[sub]["normal_force"] > 0.000001:
                    vertex = s_dict[sub]["coordinates"]
                    e1_plane = normalize_vector(
                        (vertex[0] - centroid[0], vertex[1] - centroid[1], vertex[2] - centroid[2])
                    )
                    e2_plane = cross_vectors(normal, e1_plane)
                    break

            Mtot = [0, 0, 0]
            Ntot = 0
            Stot = [0, 0, 0]

            for sub, sub_g in zip(s_dict, s_dict_g):
                vertex = s_dict[sub]["coordinates"]
                ri = (vertex[0] - centroid[0], vertex[1] - centroid[1], vertex[2] - centroid[2])
                Ni = (s_dict[sub]["normal_force"]) - (s_dict_g[sub_g]["normal_force"])
                Mi = cross_vectors(ri, scale_vector(normal, Ni))
                Mtot = sum_vectors([Mtot, Mi])
                Ntot = Ntot + Ni
                Si = subtract_vectors(s_dict[sub]["shear_force"], s_dict_g[sub_g]["shear_force"])
                Stot = sum_vectors([Stot, Si])

            if Ntot >= threshold:
                Ftot = sum_vectors([Stot, scale_vector(normal, Ntot)])
                NN = scale_vector(normal, Ntot)
                b2 = dot_vectors(Mtot, e1_plane) / Ntot
                b1 = -1 * dot_vectors(Mtot, e2_plane) / Ntot

                po = sum_vectors([centroid, scale_vector(e1_plane, b1), scale_vector(e2_plane, b2)])
                points.append(po)

                end_point_1 = sum_vectors([po, scale_vector(Ftot, scale_factor)])
                end_point_2 = sum_vectors([po, scale_vector(Ftot, -scale_factor)])

                end_point_3 = sum_vectors([po, scale_vector(NN, scale_factor)])
                end_point_4 = sum_vectors([po, scale_vector(NN, -scale_factor)])

                end_point_5 = sum_vectors([po, scale_vector(Stot, scale_factor)])
                end_point_6 = sum_vectors([po, scale_vector(Stot, -scale_factor)])

                rs.CurrentLayer("Thrust_pt")
                rs.AddPoint(po)

                rs.CurrentLayer("Thrust")
                th1 = rs.AddLine(po, end_point_1)
                th2 = rs.AddLine(po, end_point_2)

                rs.CurrentLayer("Thrust_N")
                tn1 = rs.AddLine(po, end_point_3)
                tn2 = rs.AddLine(po, end_point_4)

                rs.CurrentLayer("Thrust_S")
                if distance_point_point(po, end_point_5) > 0.001:
                    ts1 = rs.AddLine(po, end_point_5)
                    ts2 = rs.AddLine(po, end_point_6)

    rs.CurrentLayer("Default")
    rs.LayerVisible("Thrust", False)
    rs.LayerVisible("Thrust_N", False)
    rs.LayerVisible("Thrust_S", False)
    rs.LayerVisible("Thrust_pt", False)

    return


# ==============================================================================
# mapping 3DEC/compas
# ==============================================================================

support_blocks = get_blocks_from_json_file_2(HERE, "supports.json")
compound_blocks = get_blocks_from_json_file_2(HERE, "blocks.json")

blocks1, blocks_grav1, blocks_step1 = threedec_data_init_grav_step_concave(
    "init_state.txt", "grav_state.txt", 0, 0.0, 0.0, 0.0, True
)
bindex_mindex1 = mesh_block_map_dict_concave(blocks1, support_blocks, compound_blocks, 2, 3)
um1, cen1, vec1 = update_concave_resultants(bindex_mindex1, blocks_step1, 10)

for n in range(26, 27):
    # get geometry from json
    support_blocks = get_blocks_from_json_file_2(HERE, "supports.json")
    compound_blocks = get_blocks_from_json_file_2(HERE, "blocks.json")

    # mapping + mechanical update
    blocks, blocks_grav, blocks_step = threedec_data_init_grav_step_concave(
        "init_state.txt", "grav_state.txt", n, 0.0, 0.0, 0.0, True
    )
    bindex_mindex = mesh_block_map_dict_concave(blocks, support_blocks, compound_blocks, 2, 3)
    up_mesh = update_concave(bindex_mindex, blocks_step, 10)
    um, cen, vec = update_concave_resultants(bindex_mindex, blocks_step, 10)

    # extra

    rs.AddLayer("Res_Diff")
    rs.CurrentLayer("Res_Diff")
    rs.LayerColor("Res_Diff", (0, 90, 0))

    for v1, v2, p1, p2 in zip(vec, vec1, cen, cen1):
        v = subtract_vectors(v1, v2)
        vv = sum_vectors([v2, v])
        vl = rs.AddLine(v2, vv)
        rs.CurveArrows(vl, 2)

    #  extra

    # 3DEC contacts data per step
    filename_grav = threedec_data_contact_step(0, displ_x, displ_y, displ_z)
    filename = threedec_data_contact_step(n, displ_x, displ_y, displ_z)

    # Mesh categorization based on out of balance
    for bkey in up_mesh.keys():
        if up_mesh[bkey]["status"] == "in":
            mesh = up_mesh[bkey]["mesh"]
            if up_mesh[bkey]["layer"] == "Layer 1":
                rs.CurrentLayer("Layer 1")
            if up_mesh[bkey]["layer"] == "Layer 2":
                rs.CurrentLayer("Layer 2")
            if up_mesh[bkey]["layer"] == "Layer 3":
                rs.CurrentLayer("Layer 3")
            if up_mesh[bkey]["layer"] == "Layer 4":
                rs.CurrentLayer("Layer 4")
            if up_mesh[bkey]["layer"] == "Layer 5":
                rs.CurrentLayer("Layer 5")
            if up_mesh[bkey]["layer"] == "Layer 6":
                rs.CurrentLayer("Layer 6")
            if up_mesh[bkey]["layer"] == "Layer 7":
                rs.CurrentLayer("Layer 7")
            if up_mesh[bkey]["layer"] == "Layer 8":
                rs.CurrentLayer("Layer 8")
            if up_mesh[bkey]["layer"] == "Support":
                rs.CurrentLayer("Support")
            # mesh_view(mesh)
            if up_mesh[bkey]["layer"] == "Slaves":
                rs.CurrentLayer("Slaves")
        mesh_view(mesh)

    # Ftot = contact_interface(filename, 0.00001)
    # json files name with geometry + mechanical info
    # for bkey in up_mesh.keys():
    # fs, pt = contact_forces_light_test(filename, 0.00001, bkey, 25, 500, False, False)
    # fs = new_contact_interface(filename, 0.00002,100)
    new_contact_interface_sub(filename_grav, filename, 0.00002, 100)

    # contacts = data_from_threedec_contact(str(filename))
    # # print(contacts)
    # for sub in contacts['subcontact']:
    #     print)


end = time.time()
print("analysis_3dec time", end - start)
