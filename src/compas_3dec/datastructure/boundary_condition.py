from compas.data import Data
from compas.geometry import Vector


class BoundaryCondition(Data):
    """
    Represents a boundary condition for blocks or regions in a 3DEC model.

    Parameters
    ----------
    type : str, optional
        Type of boundary condition (e.g., "displacement", "force", "velocity").
    point_of_application : str, optional
        Identifier or description of the point where the boundary condition is applied.
    region : int, optional
        Region index to which the boundary condition is applied.
    magnitude : float, optional
        Magnitude of the boundary condition (e.g., displacement, force).
    direction : Vector, optional
        Direction vector for the boundary condition.

    Attributes
    ----------
    type : str
        Type of boundary condition.
    point_of_application : str
        Point where the boundary condition is applied.
    region : int
        Region index.
    magnitude : float
        Magnitude of the boundary condition.
    direction : Vector
        Direction vector.

    Examples
    --------
    >>> bc = BoundaryCondition(type="displacement", region=1, magnitude=0.01, direction=[0, 0, -1])
    >>> print(bc)
    BoundaryCondition(type=displacement, point_of_application=None, region=1, magnitude=0.01, direction=[0, 0, -1])
    """

    def __init__(
        self,
        type=None,  # type: str
        point_of_application=None,  # type: str | None
        region=None,  # type: int | None
        magnitude=None,  # type: float | None
        direction=None,  # type: Vector | None
    ):
        super().__init__()
        self.type = type
        self.point_of_application = point_of_application
        self.region = region
        self.magnitude = magnitude
        self.direction = direction

    @property
    def __data__(self):
        # type: () -> dict
        return {
            "type": self.type,
            "point_of_application": self.point_of_application,
            "region": self.region,
            "magnitude": self.magnitude,
            "direction": self.direction,
        }

    @classmethod
    def __from_data__(cls, data):
        return cls(
            type=data["type"],
            point_of_application=data["point_of_application"] if data["point_of_application"] else None,
            region=data["region"] if data["region"] else None,
            magnitude=data["magnitude"] if data["magnitude"] else None,
            direction=data["direction"] if data["direction"] else None,
        )

    def __str__(self):
        return f"BoundaryCondition(type={self.type}, point_of_application={self.point_of_application}, region={self.region}, magnitude={self.magnitude}, direction={self.direction})"
