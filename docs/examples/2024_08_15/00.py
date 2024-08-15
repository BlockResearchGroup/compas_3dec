import os
import compas
import compas_rhino
import compas_rhino.objects
import compas_rhino.conversions

# =============================================================================
# Input
# =============================================================================
guids = compas_rhino.objects.select_meshes('Select blocks')
meshes = []
for guid in guids:
    mesh = compas_rhino.conversions.meshobject_to_compas(guid)
    meshes.append(mesh)

# =============================================================================
# Save meshes to json
# =============================================================================
HERE = os.path.dirname(__file__)
FILE = os.path.join(HERE, 'meshes.json')
compas.json_dump(meshes, FILE)