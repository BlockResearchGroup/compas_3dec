from compas.data import Data
from compas.geometry import Vector


class BoundaryCondition(Data):
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
