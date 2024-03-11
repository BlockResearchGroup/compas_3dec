"""This package provides scene object plugins for visualising COMPAS Model objects in Rhino.
When working in Rhino, :class:`compas.scene.SceneObject` will automatically use
the corresponding Rhino scene object for each COMPAS model object type.

"""

from compas.plugins import plugin
from compas.scene import register

from compas_3dec.blockelement3dec import BlockElement
from compas_3dec.interactions_3dec import Interaction3dec
from compas_3dec.model_3dec import Model_3dec
from .blockobject import RhinoBlockObject
from .interactionobject import RhinoInteractionObject
from .modelobject import RhinoModelObject



@plugin(category="factories", requires=["Rhino"])
def register_scene_objects():
    register(BlockElement, RhinoBlockObject, context="Rhino")
    register(Interaction3dec, RhinoInteractionObject, context="Rhino")
    register(Model_3dec, RhinoModelObject, context="Rhino")

__all__ = [
    "RhinoBlockObject",
    "RhinoInteractionObject",
    "RhinoModelObject",
]
