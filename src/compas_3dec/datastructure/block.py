from compas.colors import Color
from compas.data import Data
from compas.datastructures import Mesh


class Block(Data):
    def __init__(
        self,
        index=None,  # type: int
        mesh=None,  # type: Mesh
        is_support=False,  # type: bool
        group=None,  # type: str | None
        unbalanced_force_ratio=None,  # type: float
        color_equilibrium=None,  # type: Color
        color=None,  # type: Color
        name=None,  # type: str | None
    ):
        super().__init__()
        self.index = index
        self.mesh = mesh
        self.is_support = is_support
        self.group = group
        self.unbalanced_force_ratio = unbalanced_force_ratio
        self.color_equilibrium = color_equilibrium
        self.color = color
        self.name = name

    @property
    def __data__(self):
        return {
            "index": self.index,
            "mesh": self.mesh,
            "is_support": self.is_support,
            "group": self.group,
            "unbalanced_force_ratio": self.unbalanced_force_ratio,
            "color_equilibrium": self.color_equilibrium,
            "color": self.color,
            "name": self.name,
        }

    @classmethod
    def __from_data__(cls, data):
        mesh = data["mesh"] if Mesh else None
        color = data["color"] if data["color"] else None
        color_equilibrium = data["color_equilibrium"] if data["color_equilibrium"] else None
        return cls(
            index=data["index"],
            mesh=mesh,
            is_support=data["is_support"],
            group=data["group"],
            color=color,
            unbalanced_force_ratio=data["unbalanced_force_ratio"],
            color_equilibrium=color_equilibrium,
            name=data["name"],
        )

    def __str__(self):
        return f"Block index: {self.index}, Mesh: {self.mesh}, is_support: {self.is_support}, Group: {self.group}, Unbalanced_Force_Ratio: {self.unbalanced_force_ratio}, Color_Equilibrium: {self.color_equilibrium}, Color: {self.color}, Name: {self.name}"
