from compas.data import Data


class RigidInteraction(Data):
    def __init__(
        self,
        compounds=[],  # type: list
    ):
        super().__init__()
        self.compounds = compounds

    @property
    def __data__(self):
        # type: () -> dict
        return {
            "compounds": self.compounds,
        }

    @classmethod
    def __from_data__(cls, data):
        return cls(
            compounds=data["compounds"],
        )

    # def __str__(self):
    #         return f'RigidInteractions {self.compounds}'

    def __str__(self):
        return f"Rigid Interactions {self.compounds}"
