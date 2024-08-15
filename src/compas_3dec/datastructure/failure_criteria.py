from compas.data import Data


class MohrCoulomb(Data):
    def __init__(
        self,
        name="MohrCoulomb",
        friction=None,  # type: float
        cohesion=0,  # type: float
        dilation=0,  # type: float
        tension=0,  # type: float
    ):
        super().__init__(name)
        self.name = name
        self.friction = friction
        self.cohesion = cohesion
        self.dilation = dilation
        self.tension = tension

    @property
    def __data__(self):
        # type: () -> dict
        return {
            "name": self.name,
            "friction": self.friction,
            "cohesion": self.cohesion,
            "dilation": self.dilation,
            "tension": self.tension,
        }

    @classmethod
    def __from_data__(cls, data):
        return cls(
            name=data["name"],
            friction=data["friction"],
            cohesion=data["cohesion"],
            dilation=data["dilation"],
            tension=data["tension"],
        )

    def __repr__(self):
        return f"[name: {self.name}, friction: {self.friction}, cohesion: {self.cohesion}, dilation: {self.dilation}, tension: {self.tension}]"
