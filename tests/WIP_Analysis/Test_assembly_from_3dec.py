import os
import compas
import vec
import itasca as it
from compas.geometry import Frame
from compas.geometry import Plane
from compas.geometry import Polygon
from compas_3dec.datastructures import Assembly_3dec
from compas_3dec.utilities import remove_duplicate_points
from compas_assembly.datastructures import Assembly
from compas_assembly.datastructures import Block
from compas_assembly.datastructures import Interface


# after running the solver, run this file loading the existing assembly json and updating all the dictionaries
# with the new data coming from 3dec

HERE = os.path.dirname("C:/Users/adellend/Code/compas_3dec/src/compas_3dec/Analysis/WIP/")

# ==============================================================================
# Init empty assembly
# ==============================================================================
assembly_3dec = Assembly()

# ==============================================================================
## access 3DEC results and extrapolate data
# ==============================================================================
# list of list (list of blocks, and in each block there is a list of gridpoints)
# BLOCKS LIST
for b in it.block.list():
    # vertices list
    verts = []
    gridp_list = it.block.Block.gridpoints(b)
    for g in gridp_list:
        vector_g = it.block.gridpoint.Gridpoint.pos(g)
        vector_g_coord = vec.vec3.x(vector_g), vec.vec3.y(vector_g), vec.vec3.z(vector_g)
        verts.append(vector_g_coord)
    # faces list
    faces_threedec = []
    faces_list = it.block.Block.faces(b, True)
    for face in faces_list:
        face_gridpts = it.block.face.Face.gridpoints(face)
        face_index_list = []
        for face_gridp in face_gridpts:
            f_gridp_index = it.block.gridpoint.Gridpoint.index(face_gridp)
            face_index_list.append(f_gridp_index)
        faces_threedec.append(face_index_list)
    # change vkeys per mesh starting from 0
    mkeys = []
    for block_face in faces_threedec:
        mkey = min(block_face)
        mkeys.append(mkey)
    ref = min(mkeys)
    faces = []
    for block_face in faces_threedec:
        new_index_list = []
        for vkey in block_face:
            new_vkey = vkey - ref
            new_index_list.append(new_vkey)
        faces.append(new_index_list)
    # create mesh and add to assembly
    mesh = Block.from_vertices_and_faces(verts, faces)
    assembly_3dec.add_block(mesh)
    node = assembly_3dec.block_node(mesh)

    # supports
    if it.block.Block.is_fix(b):
        node = assembly_3dec.block_node(mesh)
        assembly_3dec.graph.node_attribute(node, "is_support", True)

    # unbalanced force
    unbalanced_force = it.block.Block.force_unbal(b)
    unbalanced_force_vec = vec.vec3.x(unbalanced_force), vec.vec3.y(unbalanced_force), vec.vec3.z(unbalanced_force)
    assembly_3dec.graph.node_attribute(node, "3dec_unbal_force", unbalanced_force_vec)

    # velocity
    velocity = it.block.Block.velocity(b)
    velocity = vec.vec3.x(velocity), vec.vec3.y(velocity), vec.vec3.z(velocity)
    assembly_3dec.graph.node_attribute(node, "3dec_velocity", velocity)

    # density
    density = it.block.Block.density(b)
    assembly_3dec.graph.node_attribute(node, "density", density)

    # mass
    mass = it.block.Block.mass(b)
    assembly_3dec.graph.node_attribute(node, "mass", mass)

    # weight
    weight = (mass * 9.806) / 1000
    assembly_3dec.graph.node_attribute(node, "weight", weight)


for b in it.block.list():
    c = it.block.Block.contacts(b)
    for co in c:
        # valid contact
        valid = it.block.contact.Contact.valid(co)

        # contact neighbours
        b1 = it.block.contact.Contact.b1(co)
        b2 = it.block.contact.Contact.b2(co)
        blo = [b1.id(), b2.id()]

        # contact frame
        normal = it.block.contact.Contact.normal(co)
        pos = it.block.contact.Contact.pos(co)
        plane = Plane(pos, normal)
        frame = Frame.from_plane(plane)

        # contact points
        subcts = it.block.contact.Contact.subcontacts(co)
        pts = []
        for sub in subcts:
            point = it.block.subcontact.Subcontact.pos(sub)
            vpt = vec.vec3.x(point), vec.vec3.y(point), vec.vec3.z(point)
            pts.append(vpt)
            n_force = it.block.subcontact.Subcontact.force_norm(sub)
            s_force = it.block.subcontact.Subcontact.force_shear(sub)
            n_stress = it.block.subcontact.Subcontact.stress_norm(sub)
            s_stress = it.block.subcontact.Subcontact.stress_shear(sub)
            n_disp = it.block.subcontact.Subcontact.disp_norm(sub)
            s_disp = it.block.subcontact.Subcontact.disp_shear(sub)

        points = remove_duplicate_points(pts)
        if len(points) > 4:
            points = compas.geometry.convex_hull_xy(points)
        else:
            points == points

        # contact area
        polygon = Polygon(points)
        area = polygon.area
        # mesh_in = Mesh.from_polygons([polygon])

        # contact type
        c_type = it.block.contact.Contact.type(co)
        if c_type == 0:
            contact_t = "null"
        if c_type == 1:
            contact_t = "Face-Face"
        if c_type == 2:
            contact_t = "Face-Edge"
        if c_type == 3:
            contact_t = "Face-Vertex"
        if c_type == 4:
            contact_t = "Edge-Edge"
        if c_type == 5:
            contact_t = "Edge-Vertex"
        if c_type == 6:
            contact_t = "Vertex-Vertex"
        if c_type == 7:
            contact_t = "Joined"

        # forces

        # displacements

        # interface
        inter = Interface(
            type=contact_t,
            size=area,
            points=points,
            frame=frame,
            forces=None,
            mesh=None,
            viewmesh=None,
            interaction=None,
        )

        n1 = b1.id() - 1
        n2 = b2.id() - 1
        #
        block1 = assembly_3dec.node_block(n1)
        block2 = assembly_3dec.node_block(n2)

        assembly_3dec.add_block_block_interfaces(block1, block2, [inter])


# path = r'\Users\adellend\Google Drive\BRG\URM_Parametric model\Research\3dec_7_python\Test_3dec7\threedec_data'
FILE_O = os.path.join(HERE, "Test_assembly.json")
# FILE_O1 = os.path.join(HERE, 'Test_mesh.json')
compas.json_dump(assembly_3dec, FILE_O)
# compas.json_dump(mesh_list,FILE_O1)

#    density = it.block.Block.density(b)
#    volume = it.block.Block.volume(b)
#    mass = it.block.Block.mass(b)
#    velocity = it.block.Block.velocity(b)
#    unbalanced_force = it.block.Block.force_unbal(b)
#    moment = it.block.Block.moment(b)
