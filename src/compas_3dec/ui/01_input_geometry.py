import os
import compas_rhino
from compas_3dec.model_3dec import Model_3dec
from compas_3dec.blockelement3dec import BlockElement
from compas.scene import Scene
import rhinoscriptsyntax as rs
from compas_3dec.ui.utilities import adjust_options
from compas_3dec.data.arch import Arch
import scriptcontext as sc
from compas_rhino.conversions import mesh_to_rhino
import Rhino

# Get the current document (file) path
filePath = rs.DocumentPath()
# Check if a file path was returned
if filePath:
    print("Current file path:", filePath)
else:
    print("No file is currently open.")


user_choice = rs.GetString("Input geometry", strings=["from_rhino", "from_library", "from_model"])

if user_choice == "from_rhino":
    # compas_rhino.rs.sticky["model"] = Model_3dec.from_rhino()
    pass

elif user_choice == "from_library":
    geometry_name = rs.GetString("Select geometry from library", strings=["Arch", "Dome", "Wall"])
    if geometry_name == "Arch":
        message = "Define geometric parameters"
        arch_option_names = ["Rise", "Span", "Thickness", "Depth", "Blocks_number"]
        arch_option_values = [2, 5, 0.3, 0.3, 20]
        collected_values = adjust_options(message, arch_option_names, arch_option_values)
        arch = Arch(rise=int(collected_values[0]), span=int(collected_values[1]), thickness=collected_values[2], depth=collected_values[3], n=int(collected_values[4]))
        # arch = Arch(rise=5, span=10, thickness=0.5, depth=0.5, n=20)
        meshes = arch.blocks()
        model = Model_3dec(working_path = os.path.dirname(__file__))
        print (os.path.dirname(__file__))
        for m in meshes:
            model.add_element(BlockElement(m))

        # sc.sticky["model"] = model


    elif geometry_name == "Dome":
        # compas_rhino.rs.sticky["model"] = Model_3dec.from_library("dome")
        pass
    elif geometry_name == "Wall":
        # compas_rhino.rs.sticky["model"] = Model_3dec.from_library("wall")
        pass
    pass

elif user_choice == "from_model":
    # compas_rhino.rs.sticky["model"] = Model_3dec.from_model()
    pass

# print(sc.sticky["model"])
# sc.sticky["model"].print()
scene = Scene()
scene.clear()

for e in model.elementlist:
    # print(e)
    # geometry = mesh_to_rhino(e.geometry,disjoint=False)  # type: ignore
    # print(e.IsValid)
    # Rhino.RhinoDoc.ActiveDoc.Objects.AddMesh(geometry)
    scene.add(e)


# scene.add(sc.sticky["model"])
# scene.add(model)
scene.draw()
