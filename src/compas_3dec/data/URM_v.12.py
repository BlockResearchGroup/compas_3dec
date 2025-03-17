import compas
import compas_rhino
from compas.datastructures import Mesh
# from compas_rhino import MeshArtist


from compas_rhino.artists import MeshArtist
import os
import sys
import json
import rhinoscriptsyntax as rs
import math as mt
from scriptcontext import doc
from compas.geometry import vector_from_points
from compas.geometry import normalize_vector
from compas.geometry import scale_vector
from compas.geometry import plane_from_points
from compas.geometry import translate_points
from compas.geometry import intersection_segment_plane
from compas.geometry import centroid_points
from compas.geometry import angles_vectors_xy
from compas.geometry import distance_point_point
from compas.geometry import midpoint_point_point
from compas.geometry import Line
from compas.datastructures import Mesh
from compas.datastructures.volmesh import VolMesh
# from compas.topology import mesh_subdivide_tri
from compas.utilities import geometric_key
from compas.geometry import Vector
# from compas.topology import mesh_unify_cycles
import compas.geometry as cg
import random
from compas.geometry import Point
from compas.geometry import vector_from_points
from compas.geometry import normalize_vector
from compas.geometry import rotate_points
from compas.geometry import Rotation
from compas.geometry.transformations import matrix_from_axis_and_angle
# from compas.geometry.transformations import transform


# import imp
# imp.reload(Mesh)




def arc(com_pt,pt1,pt2,h):
    # creates arches of the two barrel vaults, the midpoints on the arch, the base lines and
    # the midpoints on the base lines.
    # com_pt is the point that the two arches have in common.

    ln1 = rs.AddLine(com_pt,pt1)
    ln2 = rs.AddLine(pt2,com_pt)
    midpt1 = rs.CurveMidPoint(ln1)
    midpt2 = rs.CurveMidPoint(ln2)
    midpt1[2] = h
    midpt2[2] = h
    midpt_ln1 = rs.CurveMidPoint(ln1)
    midpt_ln2 = rs.CurveMidPoint(ln2)
    arc1 = rs.AddArc3Pt(com_pt,pt1,midpt1)
    arc2 = rs.AddArc3Pt(pt2,com_pt,midpt2)
    pt3 = (pt1[0]+pt2[0],pt1[1]+pt2[1],pt1[2]+pt2[2])
    ln3 = rs.AddLine(pt1,pt3)
    ln4 = rs.AddLine(pt3,pt2)
    midpt_ln3 = rs.CurveMidPoint(ln3)
    midpt_ln4 = rs.CurveMidPoint(ln4)

    return ln1,midpt1,midpt_ln1,ln2,midpt2,midpt_ln2,com_pt,pt1,pt2,pt3,arc1,arc2,ln3,ln4,midpt_ln3,midpt_ln4

def ReverseCurve(curve):
    # flip the direction of a curve
    dup = rs.coercecurve(curve)
    dup.Reverse()
    rs.coercecurve(dup)
    doc.Objects.Replace(curve, dup)
    return dup

def edges():
    # creates the edges of the pavillion vault as intersection between two barrel vaults.

    #first barrel vault
    b_vault1 = rs.ExtrudeCurve(arc1,ln3)
    #second barrel vault
    b_vault2 = rs.ExtrudeCurve(arc2,ln1)
    #barrel vaults intersection
    b_inters = rs.IntersectBreps(b_vault1,b_vault2)

    rs.DeleteObjects(rs.ObjectsByLayer('Vault'))
    rs.CurrentLayer('Vault')

    #explode barrel vaults intersection curves
    edges = rs.ExplodeCurves(b_inters,True)
    edge0,pta = rs.PointClosestObject(com_pt,edges)
    edge1,ptb = rs.PointClosestObject(pt1,edges)
    edge2,ptc = rs.PointClosestObject(pt2,edges)
    edge3,ptd = rs.PointClosestObject(pt3,edges)
    edge0 = ReverseCurve(edge0)
    edge3 = ReverseCurve(edge3)
    rs.AddTextDot(0,pta)
    rs.AddTextDot(1,ptb)
    rs.AddTextDot(2,ptc)
    rs.AddTextDot(3,ptd)
    return edge0,edge1,edge2,edge3

def vault_srf(edge_a, edge_b, midpt_ln):
    #pavilion vault surfaces
    edges_a_b=[]
    edges_a_b.append(edge_a)
    edges_a_b.append(edge_b)
    srf = rs.AddEdgeSrf(edges_a_b)
    #central line and subdivisions
    uv_coord = rs.SurfaceClosestPoint(srf,midpt_ln)
    c_curve = rs.ExtractIsoCurve(srf,uv_coord,1)
    return srf,c_curve

def bricks(c_curve,srf,bricks_length, bricks_height, bricks_width, offsetting_ratio):

    rP_zero = []
    rP_offs = []
    lP_zero = []
    lP_offs = []
    vectors = []
    rightP_z_tr = []
    rightP_of_tr = []
    leftP_z_tr = []
    leftP_of_tr = []
    epts_list = []
    epts_tr = []
    spts_list = []
    spts_tr = []
    mpts_list = []
    mshs_r = []
    mshs_l = []
    mshs_l = []
    meshs_r = []
    meshs_l = []
    rr = []
    meshs_ri_sm = []
    meshs_le_sm = []

    #################  center point = the [z] of the center point is the same of the radius of the original arch
    center = [midpt_ln1[0],midpt_ln2[1],midpt1[2]-midpt_ln2[1]]
    center_h = [midpt_ln1[0],midpt_ln2[1],midpt_ln1[2]]


    # Z COORDINATE OF THE POINT AT 30 FROM THE BASE
    dp = cg.distance_point_point(center,midpt_ln1)
    z_sin = mt.tan(mt.pi/6)*dp
    print 'z', z_sin
    print 'mz', midpt_ln1[2]
    pt_out = (midpt_ln1[0],midpt_ln1[1],z_sin)
    lin = rs.AddLine(center,pt_out)
    int,p_int,pp = rs.CurveClosestObject(lin,srf_0)
    c_up = (center[0],center[1],z_sin)
    dis = cg.distance_point_point(c_up,pt_out)
    print 'ale', dis


    #################  subdivision of the central line of the surface by the bricks height and courses generation
    c_points = rs.DivideCurveLength(c_curve,bricks_height,False,True)

    for i,cpt in enumerate(c_points):
        if cpt[2]>=p_int[2]:
            uv_cp = rs.SurfaceClosestPoint(srf,cpt)
            courses = rs.ExtractIsoCurve(srf,uv_cp,0)
            epts = rs.CurveEndPoint(courses)
            mpts = rs.CurveMidPoint(courses)
            spts = rs.CurveStartPoint(courses)
            #end points
            epts_list.append(epts)
            #middle points
            mpts_list.append(mpts)
            #start points
            spts_list.append(spts)

        #################  offset and thickness vectors
            #offset_vectors and points
            offs_dir = rs.VectorCreate(epts_list[0],spts_list[0])
            offs_dir_u = rs.VectorUnitize(offs_dir)
            offsetting = offsetting_ratio*bricks_length*offs_dir_u
            of_mpts = rs.PointAdd(cpt,offsetting)
            #thickness vectors
            if i == 0:
                # v = vector_from_points(center_h,cpt)
                v = vector_from_points(center_h,cpt)
                v = normalize_vector(v)
                vectors.append(v)
            else:
                # v = vector_from_points(center,cpt)
                v = vector_from_points(center,cpt)
                v = normalize_vector(v)
                vectors.append(v)

        #################  points and translated points
            #points on the right side (on the surface and translated)
            points_1, tr_points_1 = lines(mpts,epts,bricks_length,bricks_width,v)
            #points on the right side with offset (on the surface and translated)
            points_2, tr_points_2 = lines(of_mpts,epts,bricks_length,bricks_width,v)
            #points on the left side (on the surface and translated)
            points_3, tr_points_3 = lines(mpts,spts,bricks_length,bricks_width,v)
            #points on the left side with offset (on the surface and translated)
            points_4, tr_points_4 = lines(of_mpts,spts,bricks_length,bricks_width,v)

            #points
            rP_zero.append(points_1)
            rP_offs.append(points_2)
            lP_zero.append(points_3)
            lP_offs.append(points_4)

            #translated points
            rightP_z_tr.append(tr_points_1)
            rightP_of_tr.append(tr_points_2)
            leftP_z_tr.append(tr_points_3)
            leftP_of_tr.append(tr_points_4)

            #courses = horizontal lines on the surface
            rightL_zero = rs.AddLine(mpts,epts)
            if rs.CurveLength(rightL_zero)>bricks_length/3:
                rr.append(rightL_zero)

        #################  corner points
            #right corner points
            corners = []
            corners_ = []
            for f,p in enumerate(epts_list):
                ept_tr = translate_points([p],scale_vector(vectors[f], bricks_width))[0]
                corner =  translate_points([ept_tr], scale_vector(offs_dir_u, bricks_width*2))[0]
                corner_ =  translate_points([p], scale_vector(offs_dir_u, bricks_width*2))[0]
                #offset translated end points
                corners.append(corner)
                #offset end points
                corners_.append(corner_)
                #translated end points
                epts_tr.append(ept_tr)

            #left corner points
            cornersl = []
            cornersl_ = []
            for e,r in enumerate(spts_list):
                spt_tr = translate_points([r],scale_vector(vectors[e], bricks_width))[0]
                cornerl =  translate_points([spt_tr], scale_vector(-offs_dir_u, bricks_width*2))[0]
                cornerl_ =  translate_points([r], scale_vector(-offs_dir_u, bricks_width*2))[0]
                #offset translated end points
                cornersl.append(cornerl)
                #offset end points
                cornersl_.append(cornerl_)
                #translated end points
                spts_tr.append(spt_tr)

    #key_stone
    k0 = rs.CurveEndPoint(rr[-1])
    vc = rs.VectorCreate(k0,center)
    vcu = rs.VectorUnitize(vc)
    k1 = rs.PointAdd(k0,vcu*bricks_width)
    stp = rs.CurveStartPoint(rr[-1])
    vl = rs.VectorCreate(stp,k0)
    vlu = rs.VectorUnitize(vl)
    k0_tr = rs.PointAdd(k0,vlu*bricks_height)
    k1_tr = rs.PointAdd(k1,vlu*bricks_height)
    z_vector = [0,0,-1]
    vperp = rs.VectorCrossProduct(z_vector,vlu)
    k0_tr1 = rs.PointAdd(k0_tr,vperp*bricks_height)
    k1_tr1 = rs.PointAdd(k1_tr,vperp*bricks_height)

    #################  bricks

    #lists of corner points ordered by the the index of the courses
    for i in range(len(rr)-1):
        m = corners[i]
        n = corners[i+1]
        o = corners_[i]
        p = corners_[i+1]
        q = cornersl[i]
        r = cornersl[i+1]
        s = cornersl_[i]
        t = cornersl_[i+1]

    #first conditional statement: course length > brick length
        if len(rP_zero[i]) and len(lP_zero[i]) > 1:
            #even lines
            if i%2 == 0:
                #right side
                a = rP_zero[i]
                b = rightP_z_tr[i]
                c = rP_zero[i+1]
                d = rightP_z_tr[i+1]
                #left side
                e = lP_zero[i]
                f = leftP_z_tr[i]
                g = lP_zero[i+1]
                h = leftP_z_tr[i+1]
            #odd lines
            else:
                try:
                    #right side
                    a = rP_offs[i]
                    b = rightP_of_tr[i]
                    c = rP_offs[i+1]
                    d = rightP_of_tr[i+1]
                    # left side
                    e = lP_offs[i]
                    f = leftP_of_tr[i]
                    g = lP_offs[i+1]
                    h = leftP_of_tr[i+1]
                except:
                    pass

        #bricks right side 1st type
            for j in range(len(c)-1):
                mesh_r = bricks_01(a,b,c,d,j)
                if mesh_r:
                    meshs_r.append(mesh_r)

        #bricks right side 2nd type: corners
            msh_r = bricks_02(a,b,c,d,m,n,o,p)
            if msh_r:
                mshs_r.append(msh_r)

        #bricks left side 1st type
            for w in range(len(g)-1):
                mesh_l = bricks_01_b(e,f,g,h,w)
                if mesh_l:
                    meshs_l.append(mesh_l)

        #bricks left side 2nd type: corners
            msh_l = bricks_02_b(e,f,g,h,q,r,s,t)
            if msh_l:
                mshs_l.append(msh_l)

    #second conditional statement: course length < brick length
        else:
            #even lines
            if i%2 == 0:
                # right side
                a = rP_zero[i]
                b = rightP_z_tr[i]
                c = rP_zero[i+1]
                d = rightP_z_tr[i+1]

                # left side
                e = lP_zero[i]
                f = leftP_z_tr[i]
                g = lP_zero[i+1]
                h = leftP_z_tr[i+1]

            #odd lines
            else:
                try:
                    #right side
                    a = rP_offs[i]
                    b = rightP_of_tr[i]
                    c = rP_offs[i+1]
                    d = rightP_of_tr[i+1]

                    #left side
                    e = lP_offs[i]
                    f = leftP_of_tr[i]
                    g = lP_offs[i+1]
                    h = leftP_of_tr[i+1]
                except:
                    pass

        #bricks right side 3rd type: cap
            mesh_r_sm = bricks_03(a,b,c,d,m,n,o,p)
            # draw_mesh(mesh_r_sm)
            if mesh_r_sm:
                meshs_ri_sm.append(mesh_r_sm)

        #bricks left side 3rd type: cap
            mesh_l_sm = bricks_03_b(e,f,g,h,q,r,s,t)
            if mesh_l_sm:
                meshs_le_sm.append(mesh_l_sm)


    #corner bricks right side
        m_r = mshs_r+meshs_ri_sm
    #corner bricks left side
        m_l = mshs_l+meshs_le_sm
    # draw_mesh(m_r[0], layer=None, fl=False, vl=True, color=(0,0,0))
    # draw_mesh(m_l[0], layer=None, fl=True, vl=True, color=(0,0,0))


    ########meshtest
    # draw_mesh(mshs_r[1])
    # kr = mshs_r[1].vertex
    # ver, fc = mshs_r[1].to_vertices_and_faces()
    # print fc

    return center,epts_list,epts_tr,m_r,m_l,meshs_r,meshs_l,k0,k0_tr,k0_tr1,k1, k1_tr, k1_tr1

def draw_mesh(mesh, layer=None, fl=False, vl=False, color=(0,0,0)):
    if layer:
        rs.CurrentLayer(layer)
    vert = mesh.vertex
    faces = mesh.face
    srf = []
    for fkey in faces:
        fv = mesh.face_vertices(fkey)
        pts = [mesh.vertex_coordinates(v) for v in fv]
        pts.append(pts[0])
        try:
            ply = rs.AddPolyline(pts)
            rs.ObjectColor(ply, color)
            srf.append(rs.AddPlanarSrf(ply))
            rs.DeleteObject(ply)
        except(Exception):
            # rs.AddPoints(pts)
            # print mesh.vertex
            # print mesh.face
            return False
        if fl:
            c = mesh.face_centroid(fkey)
            rs.AddTextDot(fkey, c)
    try:
        rs.JoinSurfaces(srf, delete_input=True)
    except:
        print mesh.vertex
        print mesh.face
        pass
    for vkey in vert:
        if vl:
            c = mesh.vertex_coordinates(vkey)
            d = rs.AddTextDot(vkey, c)
            rs.ObjectColor(d, (255,0,0))
    return True

def create_corner_bricks(bricks1,bricks2):
    cbricks = []
    cbricks_ = []
    cbricks3 = []
    cutters = []
    bricks = []
    bricks_ = []
    cbrick_holes = []
    cbricksnew = []
    to_cut_end = []
    cutter_end = []
    for i in range(len(bricks1)):
        if i%2 == 0:
            brick = bricks1[i]
            brick_ = bricks2[i]
        else:
            brick = bricks2[i]
            brick_ = bricks1[i]

    #first cut: face 3 and keep vertex 4
        vert, faces = brick_.to_vertices_and_faces()
        face = faces[3]
        pts = [vert[i] for i in face]
        pl = plane_from_points(pts[0],pts[1],pts[2])
        cbrick,cbrick1 = mesh_plane_trim(brick,pl,4)


        ckeys = cbrick.vertex.keys()
        if 5 not in ckeys and 1 not in ckeys:
            vert, faces = brick_.to_vertices_and_faces()
            face = faces[0]
            pts = [vert[i] for i in face]
            pl = plane_from_points(pts[0],pts[1],pts[2])
            cbrick_a,cbrick_1a = mesh_plane_trim(cbrick1,pl,5)
            cbrick_holes.append(cbrick_a)

        min_vd = min(cbrick.vertex_degree(key) for key in cbrick.vertices())
        if min_vd <= 2:
            print "tomas1"
            draw_mesh(brick,layer=None, fl=True, vl=True, color=(0,0,0))
            rs.AddPoints([pts[0],pts[1],pts[2]])


    #second cut: face 1 and keep vertex 4
        vert, faces = brick.to_vertices_and_faces()
        face = faces[1]
        pts = [vert[i] for i in face]
        pl = plane_from_points(pts[0],pts[1],pts[2])
        cbrick_,cbrick_1 = mesh_plane_trim(brick_,pl,4)

        #########meshtest
        # ctest.append(cbrick_)

        min_vd = min(cbrick_.vertex_degree(key) for key in cbrick_.vertices())
        if min_vd <= 2:
            print "tomas2"
            draw_mesh(brick_,layer=None, fl=True, vl=True, color=(0,0,0))
            rs.AddPoints([pts[0],pts[1],pts[2]])

        if i%2 == 0:
            cbricks_.append(cbrick_)
            cbricks.append(cbrick)
            bricks.append(cbrick)

        else:
            cbricks_.append(cbrick)
            cbricks.append(cbrick_)
            bricks_.append(cbrick)
    # bricks.append(cbricks[0])
        #########meshtest
    # draw_mesh(ctest[1])
    # kr = ctest[1].vertex
    # ver, fc = ctest[1].to_vertices_and_faces()
    # for i,n in enumerate(ver):
    #     rs.AddTextDot(i,n)
    # print kr
    # print fc

    # plt = plane_from_points([3.61495,0.07,0.0707666],[3.49545,0.07,0.0598244],[3.61495,-0.114951,0.0707666])
    # cc,ccd = mesh_plane_trim(ctest[1],plt,4)
    # ver, fc = cc.to_vertices_and_faces()
    # for i,n in enumerate(ver):
    #     rs.AddTextDot(i,n)
    # print ver
    # print fc
    # draw_mesh(cc)

    for i in range(len(cbricks)-1):
        if i%2 == 0:
            to_cut = cbricks_[i+1]
            cutter = cbricks[i]
        else:
            to_cut = cbricks[i+1]
            cutter = cbricks_[i]


    #third cut: face 3 and keep vertex 4
        pts = [cutter.vertex_coordinates(p) for p in cutter.face[3]]
        pl = plane_from_points(pts[0],pts[1],pts[2])
        cbrick3,cbrick3_b = mesh_plane_trim(to_cut,pl,4)
        cbricks3.append(cbrick3)
        min_vd = min(cbrick3.vertex_degree(key) for key in cbrick3.vertices())

        if min_vd <= 2:
            print "tomas3"
            draw_mesh(cbrick3,layer=None, fl=True, vl=True, color=(0,0,0))
            rs.AddPoints([pts[0],pts[1],pts[2]])

    to_cut_end.append(cbricks[0])
    cutter_end.append(cbricks_[0])

    for c in to_cut_end:
        for cu in cutter_end:


        #fourth cut: face 2 and keep vertex 4
            pts = [cu.vertex_coordinates(p) for p in cu.face[2]]
            pl = plane_from_points(pts[0],pts[1],pts[2])
            cbrick3,cbrick3_b = mesh_plane_trim(c,pl,4)
            cbricks3.append(cbrick3)
            min_vd = min(cbrick3.vertex_degree(key) for key in cbrick3.vertices())
            # draw_mesh(cbrick3,layer=None, fl=False, vl=True, color=(0,0,0))
            int_sup = Mesh.vertex_coordinates(cbrick3,12)
            ext_sup = Mesh.vertex_coordinates(cbrick3,11)

         #########meshtest
    # draw_mesh(cbricks3[0])
    # kr = cbricks3[0].vertex
    # ver, fc = cbricks3[0].to_vertices_and_faces()
    # for i,n in enumerate(ver):
    #     rs.AddTextDot(i,n)
    # print kr
    # print fc

    br = cbricks3+bricks+bricks_+cbrick_holes

    return br,int_sup,ext_sup

def mesh_plane_trim(mesh, plane, vk):
    tol = '3f'
    key_index = {geometric_key(mesh.vertex_coordinates(v), tol):v for v in mesh.vertex}
    pts = [mesh.vertex_coordinates(v) for v in mesh.vertex]
    c = centroid_points(pts)
    fid = [[],[]]
    for pt in pts:
        x = intersection_segment_plane((c, pt), plane)
        if x:
            fid[0].append(key_index[geometric_key(pt,tol)])
        else:
            fid[1].append(key_index[geometric_key(pt,tol)])
    faces1 = []
    faces2 = []
    for fkey in mesh.face:
        nfaces = [[],[]]
        face = mesh.face_halfedges(fkey)
        for u, v in face:
            a = mesh.vertex_coordinates(u)
            b = mesh.vertex_coordinates(v)
            x = intersection_segment_plane((a, b), plane)
            if u in fid[0]:
                idx = 0
                idx_ = 1
            else:
                idx = 1
                idx_ = 0
            if x:
                try:
                    xkey = key_index[geometric_key(x,tol)]
                except:
                    xkey = max(mesh.vertex.keys())+1
                    key_index[geometric_key(x, tol)] = xkey
                    mesh.add_vertex(xkey, attr_dict={'x':x[0], 'y':x[1], 'z':x[2]})
                nfaces[idx].append(u)
                nfaces[idx].append(xkey)
                nfaces[idx_].append(xkey)
            else:
                nfaces[idx].append(u)
        if nfaces[0]:
            faces1.append(nfaces[0])
        if nfaces[1]:
            faces2.append(nfaces[1])

    mesh_ = Mesh()
    for k in mesh.vertex:

        if any(k in sl for sl in faces1):
            mesh_.add_vertex(key=k, x=mesh.vertex[k]['x'], y=mesh.vertex[k]['y'], z=mesh.vertex[k]['z'])
    for face in faces1:
        if len(face)>= 3:
            mesh_.add_face(face)

    mesh__ = Mesh()
    for k in mesh.vertex:
        if any(k in sl for sl in faces2):
            mesh__.add_vertex(key=k, x=mesh.vertex[k]['x'], y=mesh.vertex[k]['y'], z=mesh.vertex[k]['z'])

    for face in faces2:
        if len(face)>= 3:
            mesh__.add_face(face)

    bpt = list(mesh_.vertices_on_boundary(ordered=True))
    mesh_.add_face(vertices=bpt)

    bpt = list(mesh__.vertices_on_boundary(ordered=True))
    mesh__.add_face(vertices=bpt)



    if any(vk in sl for sl in faces1):
        return mesh_, mesh__
    else:
        return mesh__, mesh_

def bricks_01(a,b,c,d,j):
    pts = [c[j],a[j],a[j+1],c[j+1],d[j],b[j],b[j+1],d[j+1]]
    faces_right = [[3,2,1,0],[6,7,4,5],[2,6,5,1],[0,4,7,3],[1,5,4,0],[3,7,6,2]]
    # rs.AddMesh(pts,faces_right)
    mesh_r = Mesh.from_vertices_and_faces(pts,faces_right)
    return mesh_r

def bricks_02(a,b,c,d,m,n,o,p):
    j = len(c)-2
    pts = [c[j+1],a[j+1],o,p,d[j+1],b[j+1],m,n]
    faces_right = [[3,2,1,0],[6,7,4,5],[2,6,5,1],[0,4,7,3],[1,5,4,0],[3,7,6,2]]
     # rs.AddMesh(pts,faces_right)
    msh_r = Mesh.from_vertices_and_faces(pts,faces_right)
    return msh_r

def bricks_03(a,b,c,d,m,n,o,p):
    pts = [c[0],a[0],o,p,d[0],b[0],m,n]
    faces_right = [[3,2,1,0],[6,7,4,5],[2,6,5,1],[0,4,7,3],[1,5,4,0],[3,7,6,2]]
     # rs.AddMesh(pts,faces_right)
    mesh_r_sm = Mesh.from_vertices_and_faces(pts,faces_right)
    return mesh_r_sm

def bricks_01_b(a,b,c,d,j):
    pts = [c[j],a[j],a[j+1],c[j+1],d[j],b[j],b[j+1],d[j+1]]
    faces_right = [[0,1,2,3],[5,4,7,6],[1,5,6,2],[3,7,4,0],[0,4,5,1],[2,6,7,3]]
    # rs.AddMesh(pts,faces_right)
    mesh_r = Mesh.from_vertices_and_faces(pts,faces_right)
    return mesh_r

def bricks_02_b(a,b,c,d,m,n,o,p):
    j = len(c)-2
    pts = [c[j+1],a[j+1],o,p,d[j+1],b[j+1],m,n]
    faces_right = [[0,1,2,3],[5,4,7,6],[1,5,6,2],[3,7,4,0],[0,4,5,1],[2,6,7,3]]
     # rs.AddMesh(pts,faces_right)
    msh_r = Mesh.from_vertices_and_faces(pts,faces_right)
    return msh_r

def bricks_03_b(a,b,c,d,m,n,o,p):
    pts = [c[0],a[0],o,p,d[0],b[0],m,n]
    faces_right = [[0,1,2,3],[5,4,7,6],[1,5,6,2],[3,7,4,0],[0,4,5,1],[2,6,7,3]]
     # rs.AddMesh(pts,faces_right)
    mesh_r_sm = Mesh.from_vertices_and_faces(pts,faces_right)
    return mesh_r_sm

def bricks_03_k(a,b,c,d,m,n,o,p):

    pts = [a,b,c,d,m,n,o,p]
    faces_right = [[3,2,1,0],[6,7,4,5],[2,6,5,1],[0,4,7,3],[1,5,4,0],[3,7,6,2]]
     # rs.AddMesh(pts,faces_right)
    mesh_r_sm = Mesh.from_vertices_and_faces(pts,faces_right)
    return mesh_r_sm

def bricks_03_k2(a,b,c,d,m,n,o,p):

    pts = [a,b,c,d,m,n,o,p]
    faces_right = [[0,1,2,3],[5,4,7,6],[1,5,6,2],[3,7,4,0],[0,4,5,1],[2,6,7,3]]
     # rs.AddMesh(pts,faces_right)
    mesh_r_sm = Mesh.from_vertices_and_faces(pts,faces_right)
    return mesh_r_sm

def lines(start,end,distance,thickness,th_vector):
    lines = rs.AddLine(start,end)
    points = rs.DivideCurveLength(lines,distance,False,True)
    if points:
        tr_points = translate_points(points,scale_vector(th_vector,thickness))
    else:
        points = [rs.CurveStartPoint(lines)]
        tr_points = translate_points(points,scale_vector(th_vector,thickness))
    return points,tr_points

def support_bricks(com_pt,pt1,pt2,pt3,bricks_width,sup_h):

    vc3 = rs.VectorCreate(pt3,com_pt)
    vc3 = rs.VectorUnitize(vc3)
    v12 = rs.VectorCreate(pt2,pt1)
    v12 = rs.VectorUnitize(v12)
    vert = rs.VectorCreate([0,0,-1],[0,0,0])
    pt3_of = rs.PointAdd(pt3,vc3*mt.sqrt(2)*bricks_width)
    pt2_of = rs.PointAdd(pt2,v12*mt.sqrt(2)*bricks_width)
    pt1_of = rs.PointAdd(pt1,-v12*mt.sqrt(2)*bricks_width)
    ptc_of = rs.PointAdd(com_pt,-vc3*mt.sqrt(2)*bricks_width)
    ptc_v = rs.PointAdd(com_pt,vert*sup_h)
    pt1_v = rs.PointAdd(pt1,vert*sup_h)
    pt2_v = rs.PointAdd(pt2,vert*sup_h)
    pt3_v = rs.PointAdd(pt3,vert*sup_h)
    ptc_of_v = rs.PointAdd(ptc_of,vert*sup_h)
    pt1_of_v = rs.PointAdd(pt1_of,vert*sup_h)
    pt2_of_v = rs.PointAdd(pt2_of,vert*sup_h)
    pt3_of_v = rs.PointAdd(pt3_of,vert*sup_h)

    sup01 = bricks_03_k2(com_pt,ptc_of,pt1_of,pt1,ptc_v,ptc_of_v,pt1_of_v,pt1_v)
    sup12 = bricks_03_k2(pt1,pt1_of,pt3_of,pt3,pt1_v,pt1_of_v,pt3_of_v,pt3_v)
    sup23 = bricks_03_k2(pt3,pt3_of,pt2_of,pt2,pt3_v,pt3_of_v,pt2_of_v,pt2_v)
    sup30 = bricks_03_k2(pt2,pt2_of,ptc_of,com_pt,pt2_v,pt2_of_v,ptc_of_v,ptc_v)



    return sup01,sup12,sup23,sup30

def supports(a,b,c,d,m,n,o,p):
    pts = [a,b,c,d,m,n,o,p]
    faces_right = [[0,1,2,3],[5,4,7,6],[1,5,6,2],[3,7,4,0],[0,4,5,1],[2,6,7,3]]
     # rs.AddMesh(pts,faces_right)
    sup = Mesh.from_vertices_and_faces(pts,faces_right)
    return sup

def splitted_supports(a,b,c,d):

    p0_b = ([a[0],a[1],a[2]-0.3])
    p1_b = ([b[0],b[1],a[2]-0.3])
    p2_b = ([c[0],c[1],a[2]-0.3])
    p3_b = ([d[0],d[1],a[2]-0.3])

    m1_2_a = midpoint_point_point(p0_b,p3_b)
    m1_2_b = midpoint_point_point(a,d)
    m1_2_c = midpoint_point_point(b,c)
    m1_2_d = midpoint_point_point(p1_b,p2_b)

    m1_4_a = midpoint_point_point(m1_2_a,p0_b)
    m1_4_b = midpoint_point_point(m1_2_b,a)
    m1_4_c0 = midpoint_point_point(m1_2_c,b)
    m1_4_c = (m1_4_c0[0],m1_4_a[1],m1_4_c0[2])
    m1_4_d0 = midpoint_point_point(m1_2_d,p1_b)
    m1_4_d = (m1_4_d0[0],m1_4_a[1],m1_4_d0[2])

    m1_8_a = midpoint_point_point(m1_4_a,p0_b)
    m1_8_b = midpoint_point_point(m1_4_b,a)
    m1_8_c0 = midpoint_point_point(m1_4_c,b)
    m1_8_c = (m1_8_c0[0],m1_8_a[1],m1_8_c0[2])
    m1_8_d0 = midpoint_point_point(m1_4_d,p1_b)
    m1_8_d = (m1_8_d0[0],m1_8_a[1],m1_8_d0[2])

    sup0 = supports(m1_2_d,m1_2_c,m1_2_b,m1_2_a,p2_b,c,d,p3_b)
    sup1 = supports(m1_4_d,m1_4_c,m1_4_b,m1_4_a,m1_2_d,m1_2_c,m1_2_b,m1_2_a)
    sup2 = supports(m1_8_d,m1_8_c,m1_8_b,m1_8_a,m1_4_d,m1_4_c,m1_4_b,m1_4_a)
    sup3 = supports(p1_b,b,a,p0_b,m1_8_d,m1_8_c,m1_8_b,m1_8_a)

    support_meshes = []
    support_meshes.append(sup0)
    support_meshes.append(sup1)
    support_meshes.append(sup2)
    support_meshes.append(sup3)

    # for m in support_meshes:
    #     me = draw_mesh(m)

    return support_meshes

def splitted_supports2(a,b,c,d):

    p0_b = ([a[0],a[1],a[2]-0.3])
    p1_b = ([b[0],b[1],a[2]-0.3])
    p2_b = ([c[0],c[1],a[2]-0.3])
    p3_b = ([d[0],d[1],a[2]-0.3])

    m1_2_a = midpoint_point_point(p0_b,p3_b)
    m1_2_b = midpoint_point_point(a,d)
    m1_2_c = midpoint_point_point(b,c)
    m1_2_d = midpoint_point_point(p1_b,p2_b)

    m1_4_a = midpoint_point_point(m1_2_a,p0_b)
    m1_4_b = midpoint_point_point(m1_2_b,a)
    m1_4_c0 = midpoint_point_point(m1_2_c,b)
    m1_4_c = (m1_4_c0[0],m1_4_a[1],m1_4_c0[2])
    m1_4_d0 = midpoint_point_point(m1_2_d,p1_b)
    m1_4_d = (m1_4_d0[0],m1_4_a[1],m1_4_d0[2])

    m1_8_a = midpoint_point_point(m1_4_a,p0_b)
    m1_8_b = midpoint_point_point(m1_4_b,a)
    m1_8_c0 = midpoint_point_point(m1_4_c,b)
    m1_8_c = (m1_8_c0[0],m1_8_a[1],m1_8_c0[2])
    m1_8_d0 = midpoint_point_point(m1_4_d,p1_b)
    m1_8_d = (m1_8_d0[0],m1_8_a[1],m1_8_d0[2])

    sup0 = supports(p2_b,c,d,p3_b,m1_2_d,m1_2_c,m1_2_b,m1_2_a)
    sup1 = supports(m1_2_d,m1_2_c,m1_2_b,m1_2_a,m1_4_d,m1_4_c,m1_4_b,m1_4_a)
    sup2 = supports(m1_4_d,m1_4_c,m1_4_b,m1_4_a,m1_8_d,m1_8_c,m1_8_b,m1_8_a)
    sup3 = supports(m1_8_d,m1_8_c,m1_8_b,m1_8_a,p1_b,b,a,p0_b)

    support_meshes = []
    support_meshes.append(sup0)
    support_meshes.append(sup1)
    support_meshes.append(sup2)
    support_meshes.append(sup3)

    # for m in support_meshes:
    #     me = draw_mesh(m)

    return support_meshes

def unsplitted_supports(a,b,c,d):
    # a = rs.PointCoordinates(a)
    # b = rs.PointCoordinates(b)
    # c = rs.PointCoordinates(c)
    # d = rs.PointCoordinates(d)

    p0_b = ([a[0],a[1],a[2]-0.3])
    p1_b = ([b[0],b[1],a[2]-0.3])
    p2_b = ([c[0],c[1],a[2]-0.3])
    p3_b = ([d[0],d[1],a[2]-0.3])

    # sup0 = supports(p0_b,a,b,p1_b,p3_b,d,c,p2_b)
    sup0 = supports(p1_b,b,a,p0_b,p2_b,c,d,p3_b)
    # mes = draw_mesh(sup0)
    return sup0

def tri_faces(mesh0):
    mes = []
    for me in mesh0:
        fkeys = me.face.keys()
        for fkey in fkeys:
            if len(me.face_vertices(fkey)) > 3:
                me.insert_vertex(fkey)
        mes.append(me)
    return mes

def cull_duplicates_face_list(meshes):
    for mesh in meshes:
        for fk in mesh.faces():
            se = []
            for item in mesh.face[fk]:
                if item not in se:
                    se.append(item)
                mesh.face[fk] = se
            # print mesh.face[fk]
            mesh.face[fk]=list(se)

def scale_mesh_factors(mesh,fx,fy,fz,print_dist = False):
    """Scale mesh by scale factors along x,y,z.
    The origin point is the centroid of the mesh
    """
    pts = [mesh.vertex_coordinates(v) for v in mesh.vertex]
    nkeys = mesh.vertex.keys()
    centroid = centroid_points(pts)
    pts_sc = []
    for i, p in enumerate(pts):
        a = p[0]-centroid[0]
        b = p[1]-centroid[1]
        c = p[2]-centroid[2]

        a1 = a*fx
        b1 = b*fy
        c1 = c*fz

        px = centroid[0]+a1
        py = centroid[1]+b1
        pz = centroid[2]+c1
        dict = {'x': px, 'y': py, 'z': pz}
        mesh.set_vertex_attributes(nkeys[i], dict)

        # pt_sc = [px,py,pz]
        # pts_sc.append(pt_sc)

        if print_dist:
            dist = mt.sqrt(mt.pow(a,2)+mt.pow(b,2)+mt.pow(c,2))
            new_dist = mt.sqrt(mt.pow(a1,2)+mt.pow(b1,2)+mt.pow(c1,2))
            print 'dist',dist,'new_dist',new_dist

def scale_mesh_printer_tolerance(mesh,ptol,print_dist = False):
    """Scale mesh adding or subtracting the printer tolerance value to the vertices coordinates.
    The origin point for the scaling is the centroid of the mesh
    """
    pts = [mesh.vertex_coordinates(v) for v in mesh.vertex]
    nkeys = mesh.vertex.keys()
    centroid = centroid_points(pts)
    pts_sc = []
    for i, p in enumerate(pts):
        a = p[0]-centroid[0]
        b = p[1]-centroid[1]
        c = p[2]-centroid[2]

        a1 = a-ptol
        b1 = b-ptol
        c1 = c-ptol

        px = centroid[0]+a1
        py = centroid[1]+b1
        pz = centroid[2]+c1
        dict = {'x': px, 'y': py, 'z': pz}
        mesh.set_vertex_attributes(nkeys[i], dict)

        # pt_sc = [px,py,pz]
        # pts_sc.append(pt_sc)

        if print_dist:
            dist = mt.sqrt(mt.pow(a,2)+mt.pow(b,2)+mt.pow(c,2))
            new_dist = mt.sqrt(mt.pow(a1,2)+mt.pow(b1,2)+mt.pow(c1,2))
            print 'dist',dist,'new_dist',new_dist

def assembly_imperfections(meshes,imperfection):
    for mesh in meshes:
        displ = random.uniform(-imperfection,imperfection)
        # get vertices coordinates, vertices keys, faces keys, mesh centroid.
        pts = [mesh.vertex_coordinates(v) for v in mesh.vertex]
        nkeys = mesh.vertex.keys()
        fkeys = mesh.face.keys()
        centroid = centroid_points(pts)
        # order the faces by the area
        f_areas = []
        for f in fkeys:
            f_area = mesh.face_area(f)
            f_areas.append(f_area)
        f_areas.sort()
        # get centroids of the two biggest faces
        axis_pt = []
        f_points = []
        directions = []
        for f in fkeys:
            if mesh.face_area(f) >= f_areas[-2]:
                a_pt = mesh.face_centroid(f)
                axis_pt.append(a_pt)
        # get centroids of the other faces
            else:
                d_pt = mesh.face_centroid(f)
                f_points.append(d_pt)
        # create axis between the two biggest faces
        axis_u = normalize_vector(vector_from_points(axis_pt[0],axis_pt[1]))
        # create vectors perpendicular to the other faces (possible directions for translation)
        for p in f_points:
            dir_u = normalize_vector(vector_from_points(centroid,p))
            directions.append(dir_u)
        # pick randomly one direction
        mov = random.choice(directions)
        # translate mesh
        pts_sc = []
        for i, p in enumerate(pts):
            # vertex coordinates
            a = p[0]
            b = p[1]
            c = p[2]
            # new vertex coordinates
            a1 = a+mov[0]*displ
            b1 = b+mov[1]*displ
            c1 = c+mov[2]*displ
            # update vertices coordinates
            dict = {'x': a1, 'y': b1, 'z': c1}
            mesh.set_vertex_attributes(nkeys[i], dict)

def assembly_imperfections_new(meshes,translation,angle,rotate=False):
    for mesh in meshes:
        displ = random.uniform(-translation,translation)
        angle = mt.radians(angle)
        # get vertices coordinates, vertices keys, faces keys, mesh centroid
        pts = [mesh.vertex_coordinates(v) for v in mesh.vertex]
        nkeys = mesh.vertex.keys()
        fkeys = mesh.face.keys()
        centroid = centroid_points(pts)
        directions = []
        for f in fkeys:
            fnorm = mesh.face_normal(f,True)
            directions.append(fnorm)
        mov = random.choice(directions)
        # translate mesh
        pts_sc = []
        for i, p in enumerate(pts):
            # vertex coordinates
            a = p[0]
            b = p[1]
            c = p[2]
            # new vertex coordinates
            a1 = a+mov[0]*displ
            b1 = b+mov[1]*displ
            c1 = c+mov[2]*displ
            pr = [a1,b1,c1]
            pts_sc.append(pr)
            tcentroid = centroid_points(pts_sc)

        if rotate:
            rotP = rotate_points(pts_sc,mov,angle,tcentroid)
            # rotm = matrix_from_axis_and_angle(mov,angle,centroid)
            # rotP = transform(pts_sc,rotm)
            for pr in rotP:
                a1 = rotP[0][0]
                b1 = rotP[0][1]
                c1 = rotP[0][2]
    # update vertices coordinates
        dict = {'x': a1, 'y': b1, 'z': c1}
        mesh.set_vertex_attributes(nkeys[i], dict)

def random_translation(meshes,translation):
    for mesh in meshes:
        displ = random.uniform(-translation,translation)
        # get vertices coordinates, vertices keys, faces keys, mesh centroid
        pts = [mesh.vertex_coordinates(v) for v in mesh.vertex]
        nkeys = mesh.vertex.keys()
        fkeys = mesh.face.keys()
        centroid = centroid_points(pts)
        directions = []
        for f in fkeys:
            fnorm = mesh.face_normal(f,True)
            directions.append(fnorm)
        mov = random.choice(directions)
        # translate mesh
        for i, p in enumerate(pts):
            # vertex coordinates
            a = p[0]
            b = p[1]
            c = p[2]
            # new vertex coordinates
            a1 = a+mov[0]*displ
            b1 = b+mov[1]*displ
            c1 = c+mov[2]*displ
        # update vertices coordinates
            dict = {'x': a1, 'y': b1, 'z': c1}
            mesh.set_vertex_attributes(nkeys[i], dict.keys(), dict.values())


def random_rotation(meshes,angle_range):
    for mesh in meshes:
        angle = random.uniform(-angle_range,angle_range)
        angler = mt.radians(angle)
        fkeys = mesh.face.keys()
        pts = [mesh.vertex_coordinates(v) for v in mesh.vertex]
        nkeys = mesh.vertex.keys()
        centroid = centroid_points(pts)
        directions = []
        for f in fkeys:
            fnorm = mesh.face_normal(f,True)
            directions.append(fnorm)
        mov = random.choice(directions)
        rotP = rotate_points(pts,mov,angler,centroid)
    # get vertices coordinates, vertices keys, faces keys, mesh centroid
        for i,r in enumerate(rotP):
            a1 = r[0]
            b1 = r[1]
            c1 = r[2]
    # update vertices coordinates
            dict = {'x': a1, 'y': b1, 'z': c1}
            mesh.set_vertex_attributes(nkeys[i], dict)

def decomp_mesh(mesh):
    pts = [mesh.vertex_coordinates(v) for v in mesh.vertex]
    fkeys = mesh.face.keys()
    # fa = mesh.face_vertices(fkeys)
    face = []

    for f in fkeys:
        fa = mesh.face_vertices(f)
        face.append(fa)


    print 'points',pts
    print 'faces',face



if __name__ == "__main__":
    for i in range(50): print ""

    brick_L = 0.240
    brick_H = 0.06
    brick_W = 0.12
    off = 1/3

    rs.DeleteObjects(rs.ObjectsByLayer("Srf_x"))
    rs.DeleteObjects(rs.ObjectsByLayer("Srf_-y"))
    rs.DeleteObjects(rs.ObjectsByLayer("Srf_-x"))
    rs.DeleteObjects(rs.ObjectsByLayer("Srf_y"))
    rs.DeleteObjects(rs.ObjectsByLayer('Geometry'))
    rs.CurrentLayer('Geometry')

    # CREATE BASE GEOMETRY
    ln1,midpt1,midpt_ln1,ln2,midpt2,midpt_ln2,com_pt,pt1,pt2,pt3,arc1,arc2,ln3,ln4,midpt_ln3,midpt_ln4 = arc([0.0,0.0,0.0],[4.0,0.0,0.0],[0.0,4.0,0.0],2.28)

    # CREATE PAVILION VAULT EDGES
    edge0,edge1,edge2,edge3 = edges()

    # CREATE PAVILION VAULT WEB SURFACES
    srf_0,c_curve0 = vault_srf(edge0,edge1,midpt_ln1)
    srf_1,c_curve1 = vault_srf(edge1,edge3,midpt_ln3)
    srf_2,c_curve2 = vault_srf(edge3,edge2,midpt_ln4)
    srf_3,c_curve3 = vault_srf(edge2,edge0,midpt_ln2)

    # rs.VectorCreate(midpt_ln1,center)
    # rs.VectorRotate()
    # CREATE CENTRAL BRICKS
    rs.CurrentLayer('Srf_x')
    c0,ep0,ep0_tr,m_r0,m_l0,meshs_r0,meshs_l0,k0_0,k0_tr_0,k0_tr1_0,k1_0,k1_tr_0,k1_tr1_0 = bricks(c_curve0,srf_0,brick_L,brick_H,brick_W,off)
    rs.CurrentLayer('Srf_-y')
    c1,ep1,ep1_tr,m_r1,m_l1,meshs_r1,meshs_l1,k0_1,k0_tr_1,k0_tr1_1,k1_1,k1_tr_1,k1_tr1_1   = bricks(c_curve1,srf_1,brick_L,brick_H,brick_W,off)
    rs.CurrentLayer('Srf_-x')
    c2,ep2,ep2_tr,m_r2,m_l2,meshs_r2,meshs_l2,k0_2,k0_tr_2,k0_tr1_2,k1_2,k1_tr_2,k1_tr1_2  = bricks(c_curve2,srf_2,brick_L,brick_H,brick_W,off)
    rs.CurrentLayer('Srf_y')
    c3,ep3,ep3_tr,m_r3,m_l3,meshs_r3,meshs_l3,k0_3,k0_tr_3,k0_tr1_3,k1_3,k1_tr_3,k1_tr1_3   = bricks(c_curve3,srf_3,brick_L,brick_H,brick_W,off)

    # CREATE CORNER BRICKS
    br_01,int_sup0,ext_sup0 = create_corner_bricks(m_r0,m_l1)
    br_12,int_sup1,ext_sup1 = create_corner_bricks(m_r1,m_l2)
    br_23,int_sup2,ext_sup2 = create_corner_bricks(m_r2,m_l3)
    br_30,int_sup3,ext_sup3 = create_corner_bricks(m_r3,m_l0)

    cull_duplicates_face_list(br_01)
    cull_duplicates_face_list(br_12)
    cull_duplicates_face_list(br_23)
    cull_duplicates_face_list(br_30)

    rs.DeleteObjects(rs.ObjectsByLayer('Bricks'))
    rs.LayerVisible('Geometry',False)
    rs.LayerVisible('Vault',False)
    rs.CurrentLayer('Bricks')

    # CREATE KEY STONES BRICKS
    ke = []
    key_stone01 = bricks_03_k(k0_0,k0_tr_1,k0_tr1_1,k0_tr_0,k1_0,k1_tr_1,k1_tr1_1,k1_tr_0)
    key_stone12 = bricks_03_k(k0_1,k0_tr_2,k0_tr1_2,k0_tr_1,k1_1,k1_tr_2,k1_tr1_2,k1_tr_1)
    key_stone23 = bricks_03_k(k0_2,k0_tr_3,k0_tr1_3,k0_tr_2,k1_2,k1_tr_3,k1_tr1_3,k1_tr_2)
    key_stone30 = bricks_03_k(k0_3,k0_tr_0,k0_tr1_0,k0_tr_3,k1_3,k1_tr_0,k1_tr1_0,k1_tr_3)

    ppt_01 = midpoint_point_point(k0_tr1_0,k0_tr1_1)
    ppt_02 = midpoint_point_point(k0_tr1_2,k0_tr1_3)
    ppt_03 = midpoint_point_point(k1_tr1_0,k1_tr1_1)
    ppt_04 = midpoint_point_point(k1_tr1_2,k1_tr1_3)

    key_stone_c1 = bricks_03_k(k0_tr1_0,ppt_01,ppt_02,k0_tr1_3,k1_tr1_0,ppt_03,ppt_04,k1_tr1_3)
    key_stone_c2 = bricks_03_k(ppt_01,k0_tr1_1,k0_tr1_2,ppt_02,ppt_03,k1_tr1_1,k1_tr1_2,ppt_04)

    ke.append(key_stone01)
    ke.append(key_stone12)
    ke.append(key_stone23)
    ke.append(key_stone30)
    ke.append(key_stone_c1)
    ke.append(key_stone_c2)

    # CREATE FOUR SUPPORTS
    # sup01,sup12,sup23,sup30 = support_bricks(com_pt,pt1,pt2,pt3,brick_W,0.3)

    # CREATE SUPPORTS FOR 3DEC
    unsp = []
    s_sp1 = splitted_supports(int_sup0,ext_sup0,ext_sup1,int_sup1)
    s_sp2 = splitted_supports2(int_sup3,ext_sup3,ext_sup2,int_sup2)
    s_unsp1 = unsplitted_supports(int_sup3,ext_sup3,ext_sup0,int_sup0)
    s_unsp2 = unsplitted_supports(int_sup1,ext_sup1,ext_sup2,int_sup2)
    unsp.append(s_unsp1)
    unsp.append(s_unsp2)

    # DRAW ALL THE MESHES
    compas_meshes_blocks = []
    compas_meshes_supports = []
    compas_meshes = meshs_r0+meshs_l0+meshs_r1+meshs_l1+meshs_r2+meshs_l2+meshs_r3+meshs_l3+br_01+br_12+br_23+br_30+ke
    compas_me_sup = s_sp1+s_sp2+unsp

    for mesh in compas_meshes:
        artist = MeshArtist(mesh)
        # artist.draw_mesh()
        # artist.clear()
        artist.draw_vertices()
        artist.draw_faces(join_faces=True)
        artist.draw_edges()
        artist.redraw()
        # artist.draw_mesh()
    for mesh in compas_me_sup:
        artist = MeshArtist(mesh)
        # artist.draw_faces(join_faces=True)
        # artist.draw_mesh()
        # artist.clear()
        artist.draw_vertices()
        artist.draw_faces(join_faces=True)
        artist.draw_edges()
        artist.redraw()
        # artist.draw_mesh()


    # compas_meshes = ke

    # for m in compas_meshes:
    #     print len(compas_meshes)
    #     sc_meshes = imp_random_scale(m,0.01,0.01,0.01)

    # cg.mesh_cull_duplicate_vertices(mesh__,'3f')

    # COMPAS MESH AND NORMALS
    # mesh = Mesh.from_obj(compas.get('faces.obj'))
    # guid = compas_rhino.select_surface()
    # mesh = compas_rhino.mesh_from_surface(Mesh, guid)

    # comp = []
    # comp.append(compas_meshes)
    # comp.append(compas_me_sup)
    # mesh_tom = []
    # for me in comp:
        # fmax = mesh.face_max_degree()
        # if fmax >5:

    # decomp_mesh(ke[0])



    # al = assembly_imperfections_new(compas_meshes,0.003,4,rotate = True)
    # al = random_translation(compas_meshes,0.005)
    # ale = random_rotation(compas_meshes,2)



    # for mesh in compas_meshes:
    # #     # ra_fx = random.uniform(0.97,0.995)
    # #     # ra_fy = random.uniform(0.97,0.995)
    # #     # ra_fz = random.uniform(0.97,0.995)
    # #     ptol = random.uniform(-0.0001,0.0001)
    # #
    # #
    # #     scale_mesh_printer_tolerance(mesh,ptol,print_dist = False)
    # #     # scale_mesh_factors(mesh,ra_fx,ra_fy,ra_fz,False)
    # #
    # #
    # #
    #     artist = MeshArtist(mesh)
    #     artist.clear()
    #     artist.draw_vertices()
    #     artist.draw_faces(join_faces=True)
    #     artist.draw_edges()
    #     artist.redraw()

    # for mesh in sc_meshes:
    #     # fmax = mesh.face_max_degree()
    #     # if fmax >5:
    #     # mesh_tom.append(mesh)
    #     artist = MeshArtist(mesh)
    #     artist.clear()
    #     artist.draw_vertices()
    #     artist.draw_faces(join_faces=True)
    #     artist.draw_edges()
    #     artist.redraw()



    #
    #     lines = []
    #     for fkey in mesh.faces():
    #         nx, ny, nz = mesh.face_normal(fkey)
    #         sp = mesh.face_centroid(fkey)
    #         ep = sp[0] + nx, sp[1] + ny, sp[2] + nz
    #         vv,ff = Mesh.to_vertices_and_faces(mesh)
    #         mc = centroid_points(vv)
    #         iv = rs.VectorCreate(mc,sp)
    #         dv = rs.VectorDotProduct(mesh.face_normal(fkey),iv)
    #         if dv > 0:
    #             print dv
    #             mesh_unify_cycles(mesh,fkey)
    #             lines.append({
    #                 'start': sp,
    #                 'end'  : ep,
    #                 'color': (0, 255, 0),
    #                 'name' : "{}.normal.{}".format(mesh.name, fkey),
    #                 'arrow': 'end'
    #
    #             })
    #     compas_rhino.xdraw_lines(lines)


    # # for m in compas_meshes:
    # for m in compas_meshes:
    #     # check = draw_mesh(m)
    #     # if not check:
    #     #     break
    # # #
    # # #
    #     data_blocks = m.to_data()
    #     compas_meshes_blocks.append(data_blocks)
    #
    # supports = []
    # for me in s_sp1:
    #     supports.append(me)
    # for mee in s_sp2:
    #     supports.append(mee)
    # supports.append(s_unsp1)
    # supports.append(s_unsp2)
    #
    # compas_meshes_sup = supports
    # #
    # for m in compas_me_sup:
    #     # draw_mesh(m)
    #     data_blocks_sup = m.to_data()
    #     compas_meshes_supports.append(data_blocks_sup)
    #
    # # vault's weight
    # weight = len(compas_meshes)*brick_L*brick_H*brick_W*2700
    # print 'Kg'+' '+str(weight)
    #
    #
    # DIR = os.path.dirname(__file__)
    # WRITEPATH = os.path.join(DIR, 'json_data')

    #===============================================================================
    #===============================================================================

    # set path to write data
    # filename2 = 'supports.json'
    # filename1 = 'blocks.json'
    # with open(os.path.join(WRITEPATH, filename1), 'w') as fp:
    #     json.dump(compas_meshes_blocks, fp)
    #
    # with open(os.path.join(WRITEPATH, filename2), 'w') as fp:
        # json.dump(compas_meshes_supports, fp)
