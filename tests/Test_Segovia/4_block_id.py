import os
import compas
import compas_rhino

HERE = os.path.dirname(__file__)
FILE = os.path.join(HERE, "assembly_3dec.json")
assembly_3dec = compas.json_load(FILE)


for node in assembly_3dec.nodes():
    centroid = assembly_3dec.node_block(node).centroid()
    compas_rhino.rs.AddTextDot(int(node) + 1, centroid)
