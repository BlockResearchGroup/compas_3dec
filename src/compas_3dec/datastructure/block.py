from compas.colors import Color
from compas.data import Data
from compas.datastructures import Mesh


class Block(Data):
    """
    Represents a block in a 3DEC model, including geometry, group assignment, and visualization properties.

    Parameters
    ----------
    index : int, optional
        Unique index of the block.
    mesh : Mesh, optional
        Mesh object representing the block geometry.
    is_support : bool, optional
        Indicates if the block is a support block (default is False).
    group : str, optional
        Name of the group to which the block belongs.
    unbalanced_force_ratio : float, optional
        Ratio of unbalanced force for the block.
    color_equilibrium : Color, optional
        Color used to visualize equilibrium state.
    color : Color, optional
        Color used for block visualization.
    name : str, optional
        Name of the block.

    Attributes
    ----------
    index : int
        Unique index of the block.
    mesh : Mesh
        Mesh object representing the block geometry.
    is_support : bool
        Indicates if the block is a support block.
    group : str
        Name of the group to which the block belongs.
    unbalanced_force_ratio : float
        Ratio of unbalanced force for the block.
    color_equilibrium : Color
        Color used to visualize equilibrium state.
    color : Color
        Color used for block visualization.
    name : str
        Name of the block.

    Examples
    --------
    >>> block = Block(index=1, mesh=my_mesh, is_support=True, group="Supports", name="Block1")
    >>> print(block)
    Block index: 1, Mesh: <Mesh object>, is_support: True, Group: Supports, Unbalanced_Force_Ratio: None, Color_Equilibrium: None, Color: None, Name: Block1
    """

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

    #

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
