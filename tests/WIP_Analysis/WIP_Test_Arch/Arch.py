from compas_assembly.geometry import Arch
from compas_assembly.datastructures import Assembly
from compas.artists import Artist
from compas.colors import Color
import compas_rhino




arch = Arch(rise=5, span=10, thickness=0.7, depth=0.5, n=19)

assembly = Assembly.from_template(arch)

compas_rhino.rs.AddLayer('Model')
# compas_rhino.rs.DeleteObjects(compas_rhino.rs.ObjectsByLayer('Model'))
for node in assembly.nodes():
    block = assembly.node_block(node)
    artist = Artist(block, layer = 'Model')
    artist.draw(color = Color.from_rgb255(10, 10, 10))
compas_rhino.rs.CurrentLayer('Model')
