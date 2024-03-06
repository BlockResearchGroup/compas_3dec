from compas.plugins import plugin
from compas.scene import register

from compas_3dec.blockelement3dec import BlockElement
from compas_3dec.interactions_3dec import Interaction3dec
from compas_3dec.model_3dec import Model_3dec
from .blockobject import BlockObject
from .interactionobject import InteractionObject
from .modelobject import ModelObject


@plugin(category="factories")
def register_scene_objects():
    register(BlockElement, BlockObject)
    register(Interaction3dec, InteractionObject)
    register(Model_3dec, ModelObject)


__all__ = [
    "BlockObject",
    "InteractionObject",
    "ModelObject"
]
