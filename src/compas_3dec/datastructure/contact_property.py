from compas.data import Data
from compas_3dec.datastructure.failure_criteria import MohrCoulomb


class ContactProperty(Data):
    """
    Represents contact properties for block interactions in a 3DEC model.

    Parameters
    ----------
    stiffness : tuple[float, float], optional
        Tuple containing normal and shear stiffness values.
    failure_criteria : MohrCoulomb, optional
        Failure criterion assigned to the contact (e.g., Mohr-Coulomb).
    group : list, optional
        List of group names or indices associated with the contact property.
    name : str, optional
        Name of the contact property.

    Attributes
    ----------
    stiffness : tuple[float, float]
        Normal and shear stiffness values.
    failure_criteria : MohrCoulomb
        Failure criterion assigned to the contact.
    group : list
        Associated groups.
    name : str
        Name of the contact property.

    Examples
    --------
    >>> fc = MohrCoulomb(friction=30, cohesion=1000)
    >>> cp = ContactProperty(stiffness=(1e7, 5e6), failure_criteria=fc, group=["Blocks"], name="DryJoint")
    >>> print(cp)
    [Stiffness: (10000000.0, 5000000.0), failure_criteria: [name: MohrCoulomb, friction: 30, cohesion: 1000, dilation: 0, tension: 0], group: ['Blocks'], Name: DryJoint]
    """

    def __init__(
        self,
        stiffness=None,  # type: tuple[float, float]
        failure_criteria=None,  # type: MohrCoulomb
        group=None,  # type: list
        name=None,  # type: str
    ):
        super().__init__(name)
        self.stiffness = stiffness
        self.failure_criteria = failure_criteria
        self.group = group if group is not None else []

    @property
    def __data__(self):
        # type: () -> dict
        return {
            "stiffness": self.stiffness,
            "failure_criteria": self.failure_criteria,
            "group": self.group,
            "name": self.name,
        }

    @classmethod
    def from_data(cls, data):
        return cls(
            stiffness=data["stiffness"],
            failure_criteria=MohrCoulomb.__from_data__(data["failure_criteria"]) if data["failure_criteria"] else None,
            group=data["group"] if data["group"] else None,
            name=data.get("name"),
        )

    def __repr__(self):
        # return "[Stiffness: " + str(self.stiffness) + ", failure_criteria: " + str(self.failure_criteria) + ", group: " + str(self.group) +  "]"
        return f"[Stiffness: {self.stiffness}, failure_criteria: {self.failure_criteria}, group: {self.group}, Name: {self.name}]"
