import itasca as it
import os
import json
import compas
import vec
from compas.datastructures import Mesh
from compas.geometry import scale_vector

it.command("python-reset-state false")

it.command(
    """
;-------------------------------------------------------------
model new
model large-strain on

;-------------------------------------------------------------
;input geometry
;-------------------------------------------------------------
program call 'support_geometry.dat'
program call 'block_geometry.dat'


;-------------------------------------------------------------
;damping
;-------------------------------------------------------------

;-------------------------------------------------------------
;supports
;-------------------------------------------------------------
block fix range group 'Supports'

;-------------------------------------------------------------
;block material properties
;-------------------------------------------------------------
block property density 1500 range group 'Supports'
block property density 1000 range group 'Blocks'

;-------------------------------------------------------------
;joints
;-------------------------------------------------------------
;to increase number of subcontacts use "block face triangulate"
;to change block tolerance use "block contact tolerance f <range>" Contacts are deleted if the distance 
;from the common plane is greater than f, or added if the block is within value of the common plane.
;By default, the value is 5 times the block tolerance

block contact generate-subcontacts
block contact jmodel assign mohr
block contact property stiffness-normal 20000000000.0 stiffness-shear 8000000000.0 coh 0.0 friction 90 range group 'Supports'
block contact property stiffness-normal 40000000000.0 stiffness-shear 6000000000.0 coh 0.0 friction 90 range group 'Blocks'
block contact material-table default property stiffness-normal 20000000000.0 stiffness-shear 8000000000.0 coh 0.0 friction 90

model gravity 0 0 -9.806
model solve ratio-local 1e-06
model save 'Test'
"""
)
bld = []
f_vkeys = []
blocks_faces = []
block_data = {}
for b in it.block.list():
    # float
    b_id = it.block.Block.index(b)
    # vec3
    cen = it.block.Block.pos(b)
    centroid = vec.vec3.x(cen), vec.vec3.y(cen), vec.vec3.z(cen)
    # float
    density = it.block.Block.density(b)
    # float
    volume = it.block.Block.vol(b)
    # float
    mass = it.block.Block.mass(b)
    # float
    weight = mass * 9.806
    # vec3
    vel = it.block.Block.velocity(b)
    velocity = vec.vec3.x(vel), vec.vec3.y(vel), vec.vec3.z(vel)
    # vec3
    unbal_f = it.block.Block.force_unbal(b)
    unbalanced_force = vec.vec3.x(unbal_f), vec.vec3.y(unbal_f), vec.vec3.z(unbal_f)
    # vec3
    mom = it.block.Block.moment(b)
    moment = vec.vec3.x(mom), vec.vec3.y(mom), vec.vec3.z(mom)
    # float
    unb_f_mag = vec.vec3.mag(unbal_f)
    if weight > 0:
        unb_f_ratio = unb_f_mag / weight

    # vec3
    f_app = it.block.Block.force_app(b)
    force_app = vec.vec3.x(f_app), vec.vec3.y(f_app), vec.vec3.z(f_app)
    # bool
    is_fix = it.block.Block.is_fix(b)

    cont_list = it.block.Block.contacts(b)
    for c in cont_list:
        # id
        c_id = it.block.contact.Contact.id(c)
        # type
        c_ty = it.block.contact.Contact.type(c)
        if c_ty == 0:
            c_ty = "null"
        if c_ty == 1:
            c_ty = "face_face"
        if c_ty == 2:
            c_ty = "face_edge"
        if c_ty == 3:
            c_ty = "face_vertex"
        if c_ty == 4:
            c_ty = "edge_edge"
        if c_ty == 5:
            c_ty = "edge_vertex"
        if c_ty == 6:
            c_ty = "vertex_vertex"
        if c_ty == 7:
            c_ty = "joined"
        # valid: Returns True if this contact is live.
        c_valid = it.block.contact.Contact.valid(c)
        # neighbours
        b1 = it.block.contact.Contact.b1(c)
        b2 = it.block.contact.Contact.b2(c)
        # Get face block 1 associated with the contact.
        # fb1 = it.block.contact.Contact.fb1(c)
        # fb2 = it.block.contact.Contact.fb2(c)

        # position
        c_pos = it.block.contact.Contact.pos(c)
        c_pos = vec.vec3.x(c_pos), vec.vec3.y(c_pos), vec.vec3.z(c_pos)

        # normal
        c_nor = it.block.contact.Contact.normal(c)
        c_normal = vec.vec3.x(c_nor), vec.vec3.y(c_nor), vec.vec3.z(c_nor)

        # subcontacts
        c_sub = it.block.contact.Contact.subcontacts(c)
        for sub in c_sub:
            # pos
            s_pos = it.block.subcontact.Subcontact.pos(sub)
            sub_pos = vec.vec3.x(s_pos), vec.vec3.y(s_pos), vec.vec3.z(s_pos)
            # disp_norm
            sub_d_norm = it.block.subcontact.Subcontact.disp_norm(sub)
            sub_d_norm = scale_vector(c_normal, sub_d_norm)
            # disp_shear
            s_d_shear = it.block.subcontact.Subcontact.disp_shear(sub)
            sub_d_shear = vec.vec3.x(s_d_shear), vec.vec3.y(s_d_shear), vec.vec3.z(s_d_shear)

            # force_norm
            sub_f_norm = it.block.subcontact.Subcontact.force_norm(sub)

            # force_shear
            sub_f_shear = it.block.subcontact.Subcontact.force_shear(sub)

            # sratio Get the ratio of shear force magnitude to normal force.
            sub_sratio = it.block.subcontact.Subcontact.sratio(sub)

            # stress_normal
            sub_st_norm = it.block.subcontact.Subcontact.stress_norm(sub)

            # stress_shear
            sub_st_shear = it.block.subcontact.Subcontact.stress_shear(sub)

            # type
            s_type = it.block.subcontact.Subcontact.type(sub)

            # valid
            s_valid = it.block.subcontact.Subcontact.valid(sub)

        print(sub_pos)

        # print (c_sub)
        # print ('b2', b2)
    # print (weight)
