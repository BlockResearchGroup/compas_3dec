from compas_rhino.scene import RhinoSceneObject

from compas_3dec.scene import BlockObject
from compas_3dec.scene import ModelObject


class RhinoModelObject(RhinoSceneObject, ModelObject):
    """Scene object for drawing block objects."""

    def __init__(self, model, **kwargs):
        super().__init__(model=model, **kwargs)

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
