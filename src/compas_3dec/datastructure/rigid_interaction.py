from compas.data import Data


class RigidInteraction(Data):
    """
    Represents a collection of rigid interaction compounds for use in 3DEC models.

    Parameters
    ----------
    compounds : list, optional
        List of compounds representing rigid interactions. If not provided, an empty list is used.

    Attributes
    ----------
    compounds : list
        The list of rigid interaction compounds.

    Examples
    --------
    >>> ri = RigidInteraction(compounds=[compound1, compound2])
    >>> print(ri)
    Rigid Interactions [compound1, compound2]
    """

    def __init__(
        self,
        compounds=None,
    ):
        super().__init__()
        self.compounds = compounds if compounds is not None else []

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

    def __str__(self):
        return f"Rigid Interactions {self.compounds}"
