import os
import compas
import vec
import itasca as it


# after running the solver, run this file loading the existing assembly json and updating all the dictionaries
# with the new data coming from 3dec

HERE = os.path.dirname("C:/Users/adellend/Code/compas_3dec/src/compas_3dec/Analysis/WIP/")

# ==============================================================================
# Load init assembly
# ==============================================================================
FILE = os.path.join(HERE, "model.json")
init_assembly = compas.json_load(FILE)

# ==============================================================================
## access 3DEC results and extrapolate data
# ==============================================================================
# list of list (list of blocks, and in each block there is a list of gridpoints)
bld = []
f_vkeys = []
blocks_faces = []
block_data = {}

# BLOCKS LIST
for b in it.block.list():
    b_id = b.id()
    print(b_id)
    # gridpoints list
    vb = []
    gl = it.block.Block.gridpoints(b)
    for g in gl:
        vg = it.block.gridpoint.Gridpoint.pos(g)
        vgc = vec.vec3.x(vg), vec.vec3.y(vg), vec.vec3.z(vg)
        vb.append(vgc)
    bld.append(vb)

    # list of faces per block
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


print()


# # list with faces and vertices keys
# # min index of the vertices in a face
# mkeys=[]
# #for block_faces in blocks_faces:
# for block_face in fff:
#     print (block_face)
#     mkey = min(block_face)
#     mkeys.append(mkey)
# ref = min(mkeys)
# l2=[]
# for block_face in fff:
#     l1 = []
#     for vkey in block_face:
#         nvkey = vkey-ref
#         l1.append(nvkey)
#     l2.append(l1)
# f_vkeys.append(l2)
