from compas.data import Data


class MohrCoulomb(Data):
    """
    Represents a Mohr-Coulomb failure criterion for use in 3DEC models.

    Parameters
    ----------
    name : str, optional
        Name of the failure criterion (default is "MohrCoulomb").
    friction : float, optional
        Friction angle or coefficient.
    cohesion : float, optional
        Cohesion value (default is 0).
    dilation : float, optional
        Dilation angle or coefficient (default is 0).
    tension : float, optional
        Tensile strength (default is 0).

    Attributes
    ----------
    name : str
        Name of the failure criterion.
    friction : float
        Friction angle or coefficient.
    cohesion : float
        Cohesion value.
    dilation : float
        Dilation angle or coefficient.
    tension : float
        Tensile strength.

    Examples
    --------
    >>> fc = MohrCoulomb(friction=30, cohesion=1000, dilation=5, tension=0)
    >>> print(fc)
    [name: MohrCoulomb, friction: 30, cohesion: 1000, dilation: 5, tension: 0]
    """

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
