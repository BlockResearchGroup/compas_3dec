import compas.datastructures  # noqa: F401
import compas.geometry  # noqa: F401
from compas_notebook.scene import ThreeSceneObject

from compas_3dec.scene import BlockObject
from compas_3dec.scene import InteractionObject
from compas_3dec.scene import ModelObject


class ThreeModelObject(ThreeSceneObject, ModelObject):
    """Scene object for drawing block objects."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def draw(self):
        """Draw the mesh associated with the scene object.

        Returns
        -------
        list[three.Mesh, three.LineSegments]
            List of pythreejs objects created.

        """
        for child in self.children:
            if isinstance(child, BlockObject):
                child.show = self.show_elements

        return self.guids
