from compas.data import Data


class Group(Data):
    def __init__(
        self,
        name=None,  # type: str
        material=None,  # type: str | None
        contact_property=None,  # type: str | None
    ):
        super().__init__(name)  # not sure about name in parenthesis
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
