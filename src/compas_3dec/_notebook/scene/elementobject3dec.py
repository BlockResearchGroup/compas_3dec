from compas_notebook.scene import ThreeSceneObject

from compas_3dec.scene import BlockElement3decObject



class ThreeBlockElementObject(ThreeSceneObject, BlockElement3decObject):
    """Scene object for drawing mesh."""

    def __init__(self, element, **kwargs):
        super().__init__(element=element, **kwargs)
