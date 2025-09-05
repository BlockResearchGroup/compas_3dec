from compas.data import Data


class Material(Data):
    """
    Represents a material with mechanical properties for use in 3DEC models.

    Parameters
    ----------
    name : str, optional
        Name of the material.
    E : float, optional
        Young's modulus of the material.
    poisson : float, optional
        Poisson's ratio of the material.
    rho : float, optional
        Density of the material.
    group : list, optional
        List of group names or indices associated with the material.

    Attributes
    ----------
    name : str
        Name of the material.
    E : float
        Young's modulus.
    poisson : float
        Poisson's ratio.
    rho : float
        Density.
    group : list
        Associated groups.

    Examples
    --------
    >>> mat = Material(name="Stone", E=30e9, poisson=0.2, rho=2500)
    >>> print(mat)
    Stone E: 30000000000.0 poisson: 0.2 rho: 2500 group: []
    """

    def __init__(
        self,
        name=None,  # type: str
        E=None,  # type: float
        poisson=None,  # type: float
        rho=None,  # type: float
        group=None,  # type: list
    ):
        super().__init__(name)
        self.name = name
        self.E = E
        self.poisson = poisson
        self.rho = rho
        self.group = group if group is not None else []

    @property
    def __data__(self):
        return {
            "name": self.name,
            "E": self.E,
            "poisson": self.poisson,
            "rho": self.rho,
            "group": self.group,
        }

    @classmethod
    def __from_data__(cls, data):
        return cls(
            name=data["name"],
            E=data["E"],
            poisson=data["poisson"],
            rho=data["rho"],
            group=data["group"] if data["group"] else None,
        )

    def __repr__(self):
        # return self.name + " E: " + str(self.E) + " poisson: " + str(self.poisson) + " rho: " + str(self.rho) + " group: " + str(self.group)
        return f"{self.name} E: {self.E} poisson: {self.poisson} rho: {self.rho} group: {self.group}"

    @property
    def G(self):
        return self.E / (2 * (1 + self.poisson))
