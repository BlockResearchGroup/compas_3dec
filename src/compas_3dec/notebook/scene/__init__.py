"""This package provides scene object plugins for visualising COMPAS Model objects in Rhino.
When working in Rhino, :class:`compas.scene.SceneObject` will automatically use
the corresponding Rhino scene object for each COMPAS model object type.

"""

from compas.plugins import plugin
from compas.scene import register

from compas_3dec.blockelement3dec import BlockElement
from compas_3dec.interactions_3dec import Interaction3dec
from compas_3dec.model_3dec import Model_3dec
from .blockobject import ThreeBlockObject
from .interactionobject import ThreeInteractionObject
from .modelobject import ThreeModelObject


@plugin(category="factories", requires=["pythreejs"])
def register_scene_objects():
    register(BlockElement, ThreeBlockObject, context="Notebook")
    register(Interaction3dec, ThreeInteractionObject, context="Notebook")
    register(Model_3dec, ThreeModelObject, context="Notebook")


__all__ = ["ThreeBlockObject", "ThreeInteractionObject", "ThreeModelObject"]
