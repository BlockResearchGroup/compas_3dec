import os
from compas_3dec.datastructures import Assembly_3dec
from compas_3dec.analysis import Analysis
from compas_3dec.mechanical import MechParam

from compas_assembly.artists import AssemblyArtist
import compas_rhino
from compas.colors import Color


# ==============================================================================
# import
# ==============================================================================
HERE = os.path.dirname(__file__)

# ==============================================================================
# Get geometry
# ==============================================================================
assembly_3dec = Assembly_3dec.from_rhino_select(HERE)

compas_rhino.rs.AddLayer("IDs")
compas_rhino.rs.DeleteObjects(compas_rhino.rs.ObjectsByLayer("IDs"))
compas_rhino.rs.CurrentLayer("IDs")
for node in assembly_3dec.nodes():
    centroid = assembly_3dec.node_block(node).centroid()
    compas_rhino.rs.AddTextDot(int(node) + 1, centroid)
compas_rhino.rs.CurrentLayer("Default")
compas_rhino.rs.LayerVisible("IDs", False)

# ==============================================================================
# Get/set mechanical parameters
# ==============================================================================
mechparam = MechParam.standard_material()

# ==============================================================================
# Analysis
# ==============================================================================
Analysis.geometry_dat(assembly_3dec, HERE)
Analysis.main_dat(mechparam, HERE, "Analysis_test")
