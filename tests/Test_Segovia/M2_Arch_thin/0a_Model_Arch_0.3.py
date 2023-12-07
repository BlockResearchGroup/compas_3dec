import os
import rhinoscriptsyntax as rs
import compas_rhino
from compas.artists import Artist
from compas.colors import Color
from compas.colors import Color
from compas_assembly.datastructures import Assembly
from compas_assembly.geometry import Arch


HERE = os.path.dirname(__file__)
FILE_1 = os.path.join(HERE, "init_state.txt")
FILE_2 = os.path.join(HERE, "grav_state.txt")
FILE_3 = os.path.join(HERE, "contacts_init")
FILE_4 = os.path.join(HERE, "contact_grav.txt")
FILE_5 = os.path.join(HERE, "assembly_3dec.json")
FILE_6 = os.path.join(HERE, "blocks.json")
FILE_7 = os.path.join(HERE, "supports.json")
FILE_8 = os.path.join(HERE, "Analysis_test_init.sav")
FILE_9 = os.path.join(HERE, "Analysis_test_grav.sav")

try:
    if FILE_1:
        os.remove(FILE_1)
    if FILE_2:
        os.remove(FILE_2)
    if FILE_3:
        os.remove(FILE_3)
    if FILE_4:
        os.remove(FILE_4)
    if FILE_5:
        os.remove(FILE_5)
    if FILE_6:
        os.remove(FILE_6)
    if FILE_7:
        os.remove(FILE_7)
    if FILE_8:
        os.remove(FILE_8)
except Exception:
    pass


if rs.IsLayer("Layer 1"):
    compas_rhino.rs.DeleteObjects(compas_rhino.rs.ObjectsByLayer("Layer 1"))

if rs.IsLayer("Support"):
    compas_rhino.rs.DeleteObjects(compas_rhino.rs.ObjectsByLayer("Support"))

# =============================================================================
# arch
# =============================================================================
arch = Arch(rise=5, span=10, thickness=0.3, depth=0.5, n=20)
assembly = Assembly.from_template(arch)

# =============================================================================
# View
# =============================================================================
compas_rhino.rs.AddLayer("Model")
compas_rhino.rs.DeleteObjects(compas_rhino.rs.ObjectsByLayer("Model"))
for node in assembly.nodes():
    block = assembly.node_block(node)
    artist = Artist(block, layer="Model")
    artist.draw(color=Color.from_rgb255(10, 10, 10))
compas_rhino.rs.CurrentLayer("Model")
