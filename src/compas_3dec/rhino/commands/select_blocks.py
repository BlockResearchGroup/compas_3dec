"""
NOTE:

- Reference to RhinoCommmon.dll is added by default

- You can specify your script requirements like:

    # r: <package-specifier> [, <package-specifier>]
    # requirements: <package-specifier> [, <package-specifier>]

    For example this line will ask the runtime to install
    the listed packages before running the script:

    # requirements: pytoml, keras

    You can install specific versions of a package
    using pip-like package specifiers:

    # r: pytoml==0.10.2, keras>=2.6.0

- Use env directive to add an environment path to sys.path automatically
    # env: /path/to/your/site-packages/
"""
#! python3

import rhinoscriptsyntax as rs
import scriptcontext as sc
import math

import System
import System.Collections.Generic
import Rhino

import compas


def from_rhino_select(group_types=["support", "other_group"], group_colors=[(255, 0, 0), (255, 0, 255)]):
    """Construct a compas_model by manually selecting Rhino concave or
    convex meshes. At least one mesh as a support and one mesh as a
    block should be selected. The meshes in Rhino should be closed
    and with welded vertices. If some blocks are concave, each of
    them should be subdivided into convex meshes and joined, forming
    a compound.
    Returns
    -------
    :class:`model`
        The assembly datastructure with Supports, Blocks and compound
        groups defined.
    """

    from compas_rhino.objects import select_meshes
    from compas_rhino.objects import get_mesh_vertices_and_faces
    from compas.datastructures import Mesh
    from compas_rhino.conversions import mesh_to_compas
    from compas_rhino.conversions import mesh_to_rhino

    # ==============================================================
    # Delete all the previously added tempoary geometry
    # ==============================================================
    if not ("temporary_geometry" in sc.sticky.keys()):
        sc.sticky["temporary_geometry"] = []

    if sc.sticky["temporary_geometry"]:
        rs.DeleteObjects(sc.sticky["temporary_geometry"])
        sc.sticky["temporary_geometry"] = []
        rs.Redraw()

    # ==============================================================
    # Select all Meshes that will be used in the solver.
    # Add attribute to the object to note that it belongs to the solver.
    # ==============================================================
    mesh_supports_guids = rs.GetObjects(
        "select closed valid meshes for the overall simulation",
        preselect=True,
        select=True,
        group=False,
        filter=rs.filter.mesh,
    )
    mesh_guids = select_meshes()
    rs.UnselectAllObjects()
    mesh_rhino_objects = []

    if mesh_supports_guids:  # user can accidentally do not select anything
        for i in range(len(mesh_guids)):
            rhino_object = Rhino.RhinoDoc.ActiveDoc.Objects.Find(mesh_guids[i])
            rs.ObjectColor(mesh_guids[i], (200, 200, 200))
            mesh_rhino_objects.append(rhino_object)
            rhino_object.Attributes.DeleteAllUserStrings()
            rhino_object.Attributes.SetUserString("group", "block")

            center = rhino_object.Geometry.GetBoundingBox(Rhino.Geometry.Plane.WorldXY).Center
            text = str(i)
            text_dot = Rhino.Geometry.TextDot(text, center)
            sc.sticky["temporary_geometry"].append(Rhino.RhinoDoc.ActiveDoc.Objects.AddTextDot(text_dot))

    else:
        rs.MessageBox("You did not selected any meshes!")
        return
    rs.Redraw()
    # ==============================================================
    # Mark selected meshes as supports
    # ==============================================================

    for i in range(len(group_types)):  # user can accidentally do not select anything

        mesh_supports_guids = rs.GetObjects(
            "select_" + group_types[i], preselect=True, select=True, group=False, filter=rs.filter.mesh
        )
        rs.UnselectAllObjects()

        if mesh_supports_guids:
            for guid in mesh_supports_guids:
                rhino_object = Rhino.RhinoDoc.ActiveDoc.Objects.Find(guid)
                rhino_object.Attributes.SetUserString("group", group_types[i])
                rs.ObjectColor(guid, group_colors[i])
        else:
            rs.MessageBox("Select " + group_types[i] + " !")
            return

    # ==============================================================
    # Convert user strings as the 3dec input
    # ==============================================================
    input_meshes = []
    is_support = []

    for mesh_rhino_object in mesh_rhino_objects:
        input_meshes.append(mesh_to_compas(mesh_rhino_object.Geometry))
        is_support.append(mesh_rhino_object.Attributes.GetUserString("group") == "support")

    print(input_meshes)
    print(is_support)


def from_obj():
    pass


def from_library():
    pass


from_rhino_select()
