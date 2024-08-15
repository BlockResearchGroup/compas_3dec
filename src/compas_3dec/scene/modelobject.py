from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import compas.geometry  # noqa: F401
from compas.scene import SceneObject


from compas_3dec.interactions_3dec import Interaction3dec


class ModelObject(SceneObject):
    def __init__(
        self,
        model,
        show_tree=False,  # type: bool
        show_graph=False,  # type: bool
        show_elements=True,  # type: bool
        show_interactions=True,  # type: bool
        show_element_faces=False,  # type: bool
        **kwargs,  # type: dict
    ):  # type: (...) -> None
        super(ModelObject, self).__init__(item=model, **kwargs)

        self._model = model

        self.show_tree = show_tree
        self.show_graph = show_graph
        self.show_elements = show_elements
        self.show_interactions = show_interactions

        elementkwargs = kwargs.copy()
        if "show_faces" in elementkwargs:
            del elementkwargs["show_faces"]

        for element in model.elementlist:
            self.add(element, show_faces=show_element_faces, **elementkwargs)

        for edge, interaction in model.graph.edges(True):
            if isinstance(interaction["interaction"], Interaction3dec):
                self.add(
                    interaction["interaction"],
                    show_normal_force_lines=False,
                    show_shear_force_lines=True,
                    show_points=False,
                    show_mesh_normal_stress=False,
                    show_mesh_shear_stress=False,
                    show_resultant_force=True,
                    show_resultant_point=True,
                    show_resultant_point_shear=False,
                    show_resultant_force_shear=False,
                    show_resultant_force_normal=True,
                    show_resultant_torque=False,
                    show_resultant_shear_transported=True,
                )

        # for edge in model.graph.edges():
        #     interaction = model.graph.edge_attribute(edge, name="interaction")
        #     self.add(interaction, show_faces=show_interaction_faces,  **kwargs)

    @property
    def model(self):
        # type: () -> compas_model.model.Model
        return self._model

    @model.setter
    def model(self, model):
        self._model = model
        self._transformation = None

    @property
    def transformation(self):
        # type: () -> compas.geometry.Transformation | None
        return self._transformation

    @transformation.setter
    def transformation(self, transformation):
        self._transformation = transformation

    def draw(self):
        """draw the model.

        Returns
        -------
        None

        """
        raise NotImplementedError

    def clear(self):
        """Clear all components of the model.

        Returns
        -------
        None

        """
        raise NotImplementedError
