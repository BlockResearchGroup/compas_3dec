import os
import compas

HERE = os.path.dirname(__file__)

# =============================================================================
# Input from json file
# =============================================================================
# FILE_I = os.path.join(HERE, 'timber_shell_connectors.json')
# input_data = compas.json_load(FILE_I)

# panels = input_data['meshes_panels']
# connectors = input_data['meshes_connectors']
# supports = input_data['corners']
# groups = input_data['groups']

# geometry = panels + connectors + supports

# =============================================================================
# Input from class
# =============================================================================
# from compas_3dec.data.arch import Arch
# arch = Arch(rise=5, span=10, thickness=0.5, depth=0.5, n=20)
# geometry = arch.blocks()

# =============================================================================
# Input meshes from Rhino
# =============================================================================
import compas_rhino
import compas_rhino.objects
import compas_rhino.conversions

guids = compas_rhino.objects.select_meshes('Select blocks')
geometry = []
for guid in guids:
    mesh = compas_rhino.conversions.meshobject_to_compas(guid)
    geometry.append(mesh)

# =============================================================================
# Save meshes to json
# =============================================================================
FILE_O = os.path.join(HERE, 'geometry.json')
compas.json_dump(geometry, FILE_O)


# =============================================================================
# View
# =============================================================================
from compas.scene import Scene
scene = Scene()
scene.clear()   #doesn't work
for g in geometry:
    scene.add(g)
scene.draw()



