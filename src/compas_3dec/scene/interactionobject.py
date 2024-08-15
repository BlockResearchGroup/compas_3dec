from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import compas.geometry  # noqa: F401
from compas.scene import SceneObject
from compas.scene.descriptors.colordict import ColorDictAttribute
from compas.colors import Color

# import compas_model.interactions  # noqa: F401


class InteractionObject(SceneObject):
    """Base class for all interaction scene objects.

    Parameters
    ----------
    interaction : :class:`compas_model.interactions.interaction`
        A COMPAS interaction.

    Attributes
    ----------
    interaction : :class:`compas_model.interactions.interaction`
        The interaction.
    color : :class:`compas.colors.Color`
        The base RGB color of the interaction.
    vertexcolor : :class:`compas.colors.ColorDict`
        Vertex colors.
    edgecolor : :class:`compas.colors.ColorDict`
        Edge colors.
    facecolor : :class:`compas.colors.ColorDict`
        Face colors.
    vertexsize : float
        The size of the vertices. Default is ``1.0``.
    edgewidth : float
        The width of the edges. Default is ``1.0``.
    show_vertices : Union[bool, sequence[float]]
        Flag for showing or hiding the vertices, or a list of keys for the vertices to show.
        Default is ``False``.
    show_edges : Union[bool, sequence[tuple[int, int]]]
        Flag for showing or hiding the edges, or a list of keys for the edges to show.
        Default is ``True``.
    show_faces : Union[bool, sequence[int]]
        Flag for showing or hiding the faces, or a list of keys for the faces to show.
        Default is ``True``.

    See Also
    --------
    :class:`compas.scene.GraphObject`
    :class:`compas.scene.VolinteractionObject`

    """

    vertexcolor = ColorDictAttribute()
    edgecolor = ColorDictAttribute()
    facecolor = ColorDictAttribute()

    def __init__(self, interaction, **kwargs):
        # type: (compas_model.interactions.interaction, dict) -> None
        super(InteractionObject, self).__init__(item=interaction, **kwargs)

        self._interaction = interaction
        self.interaction.compute_force_display(scale_factor=0.001)
        self.vertexcolor = kwargs.get("vertexcolor")
        self.edgecolor = kwargs.get("edgecolor", self.contrastcolor)
        self.opacity = kwargs.get("opacity", 0.5)
        self.facecolor = kwargs.get("facecolor", self.color)  #
        self.edgecolor = kwargs.get("edgecolor", self.color)
        self.vertexsize = kwargs.get("vertexsize", 1)
        self.edgewidth = kwargs.get("edgewidth", 10.0)
        self.show_vertices = kwargs.get("show_vertices", False)
        self.show_edges = kwargs.get("show_edges", True)
        self.show_faces = kwargs.get("show_faces", True)
        self.show_normal_force_lines = kwargs.get("show_normal_force_lines", False)
        self.show_shear_force_lines = kwargs.get("show_shear_force_lines", False)
        self.show_points = kwargs.get("show_points", False)
        self.show_mesh_normal_stress = kwargs.get("show_mesh_normal_stress", False)
        self.show_mesh_shear_stress = kwargs.get("show_mesh_shear_stress", False)
        self.color_normal_force_lines = kwargs.get("color_normal_force_lines", Color.red())
        self.color_shear_force_lines = kwargs.get("color_shear_force_lines", Color.blue())
        self.color_points = kwargs.get("color_points", Color.black())
        self.thickness_lines = kwargs.get("thickness_lines", 2.0)
        self.show_resultant_force = kwargs.get("show_resultant_force", True)
        self.show_resultant_point = kwargs.get("show_resultant_point", True)
        self.show_resultant_point_shear = kwargs.get("show_resultant_point_shear", True)
        self.show_resultant_force_shear = kwargs.get("show_resultant_force_shear", True)
        self.show_resultant_force_normal = kwargs.get("show_resultant_force_normal", True)
        self.color_resultant_force = kwargs.get("color_resultant_force", Color.from_rgb255(0, 153, 0))
        self.color_resultant_force_shear = kwargs.get("color_resultant_force_shear", Color.from_rgb255(0, 0, 155))
        self.color_resultant_force_normal = kwargs.get("color_resultant_force_normal", Color.from_rgb255(155, 0, 0))
        self.show_resultant_torque = kwargs.get("show_resultant_torque", True)
        self.color_resultant_torque = kwargs.get("color_resultant_torque", Color.from_rgb255(155, 155, 0))
        self.show_resultant_shear_transported = kwargs.get("show_resultant_shear_transported", True)
        self.color_resultant_shear_transported = kwargs.get(
            "color_resultant_shear_transported", Color.from_rgb255(0, 0, 155)
        )

    @property
    def interaction(self):
        # type: () -> compas_3dec.interactions.interaction
        return self._interaction

    @interaction.setter
    def interaction(self, interaction):
        self._interaction = interaction
        self._transformation = None

    @property
    def transformation(self):
        # type: () -> compas.geometry.Transformation | None
        return self._transformation

    @transformation.setter
    def transformation(self, transformation):
        self._transformation = transformation

    def draw(self):
        """draw the interaction.

        Returns
        -------
        None

        """
        raise NotImplementedError

    def clear(self):
        """Clear all components of the interaction.

        Returns
        -------
        None

        """
        raise NotImplementedError
