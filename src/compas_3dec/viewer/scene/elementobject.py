from compas_viewer.scene import MeshObject

from compas_model.scene import ElementObject



class ViewerElementObject(MeshObject):
    """Scene object for drawing mesh."""

    def __init__(self, element, **kwargs):
        super().__init__( mesh= element.geometry,**kwargs)
