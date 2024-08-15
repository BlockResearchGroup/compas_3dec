from compas.data import Data


class Material(Data):
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
