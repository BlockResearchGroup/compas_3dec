from compas_model.interactions import Interaction


class RigidInteraction(Interaction):
    def __init__(self, name=None):
        # type: (str | None) -> None
        super().__init__(name)
