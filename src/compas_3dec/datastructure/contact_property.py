from compas.data import Data
from compas_3dec.datastructure.failure_criteria import MohrCoulomb


class ContactProperty(Data):
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
