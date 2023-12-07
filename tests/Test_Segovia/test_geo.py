import compas_rhino
from compas_rhino.geometry import RhinoMesh
from compas_rhino.utilities import select_meshes

supports = select_meshes("Select support meshes")
for guid in supports:
    mesh = RhinoMesh.from_guid(guid)
    submeshes = compas_rhino.rs.ExplodeMeshes(guid, delete=True)
