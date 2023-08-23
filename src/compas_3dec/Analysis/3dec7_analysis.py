import itasca as it
import os
import sys
import json
import compas
import vec
from compas_assembly.datastructures import Block
from compas_3dec.datastructures import Model
#from compas_3dec.Geometry import Model

HERE = os.path.dirname('C:/Users/adellend/Code/compas_3dec/src/compas_3dec/Geometry/')

FILE = os.path.join(HERE, "mod.json")
init_model = compas.json_load(FILE)


bld = []
f_vkeys = []
blocks_faces = []
block_data = {}
for b in it.block.list():
    #gridpoints list
    vb = []
    gl = it.block.Block.gridpoints(b)
    for g in gl:
        vg = it.block.gridpoint.Gridpoint.pos(g)
        vgc = vec.vec3.x(vg), vec.vec3.y(vg), vec.vec3.z(vg)
        vb.append(vgc)
    bld.append(vb)

    #list of faces per block
    fl = it.block.Block.faces(b, True)
    fff = []
    for f in fl:
        fi = it.block.face.Face.gridpoints(f)
        fal = []
        for fig in fi:
            fip = it.block.gridpoint.Gridpoint.index(fig)
            fal.append(fip)
        fff.append(fal)
    blocks_faces.append(fff)

    # list with faces and vertices keys
    # min index of the vertices in a face
    mkeys=[]
    #for block_faces in blocks_faces:
    for block_face in fff:
        print (block_face)
        mkey = min(block_face)
        mkeys.append(mkey)
    ref = min(mkeys)
    l2=[]
    for block_face in fff:
        l1 = []
        for vkey in block_face:
            nvkey = vkey-ref
            l1.append(nvkey)
        l2.append(l1)
    f_vkeys.append(l2)



#print (f_vkeys)



#mesh_list = []
#for s,w in zip(bld,f_vkeys):
#    s.reverse()
#    mesh = Mesh.from_vertices_and_faces(s,w)
#    mesh_list.append(mesh)
#
#path = r'\Users\adellend\Google Drive\BRG\URM_Parametric model\Research\3dec_7_python\Test_3dec7\threedec_data'
#FILE_O = os.path.join(path, 'test.json')
#compas.json_dump(mesh_list, FILE_O)

#    density = it.block.Block.density(b)
#    volume = it.block.Block.volume(b)
#    mass = it.block.Block.mass(b)
#    velocity = it.block.Block.velocity(b)
#    unbalanced_force = it.block.Block.force_unbal(b)
#    moment = it.block.Block.moment(b)

