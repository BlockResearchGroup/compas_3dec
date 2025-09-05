from compas.data import Data


class Group(Data):
    """
    Represents a group of blocks or elements in a 3DEC model, with associated material and contact properties.

    Parameters
    ----------
    name : str, optional
        Name of the group.
    material : str or Material, optional
        Material assigned to the group.
    contact_property : str or ContactProperty, optional
        Contact property assigned to the group.

    Attributes
    ----------
    name : str
        Name of the group.
    material : str or Material
        Material assigned to the group.
    contact_property : str or ContactProperty
        Contact property assigned to the group.

    Examples
    --------
    >>> group = Group(name="Blocks", material="Stone", contact_property="DryJoint")
    >>> print(group)
    Group name: Blocks, Material: Stone, Contact_property: DryJoint
    """

    def __init__(
        self,
        name=None,  # type: str
        material=None,  # type: str | None
        contact_property=None,  # type: str | None
    ):
        super().__init__(name)
        self.name = name
        self.material = material
        self.contact_property = contact_property

    @property
    def __data__(self):
        # type: () -> dict
        return {
            "name": self.name,
            "material": self.material,
            "contact_property": self.contact_property,
        }

    @classmethod
    def __from_data__(cls, data):
        return cls(
            name=data["name"],
            material=data["material"] if data["material"] else None,
            contact_property=data["contact_property"] if data["contact_property"] else None,
        )

    def __repr__(self):
        return f"Group(name={self.name})"

    def __str__(self):
        return f"Group name: {self.name}, Material: {self.material}, Contact_property: {self.contact_property}"
