from compas.data import Data


class ThreeDECBlockMaterial(Data):
    """Isotropic material assigned directly to 3DEC blocks.

    Parameters
    ----------
    density : float
        Mass density in kilograms per cubic metre.
    young_modulus : float
        Young's modulus in pascals.
    poisson_ratio : float
        Poisson's ratio.
    name : str, optional
        Material name.

    Notes
    -----
    Rigid blocks use only ``density`` directly in the 3DEC input deck.
    Young's modulus and Poisson's ratio describe the source material and can
    be used to derive joint stiffness or future deformable-block properties.
    """

    def __init__(self, density, young_modulus=None, poisson_ratio=None, name=None):
        super().__init__(name=name)
        self.density = float(density)
        self.young_modulus = float(young_modulus) if young_modulus is not None else None
        self.poisson_ratio = float(poisson_ratio) if poisson_ratio is not None else None
        if self.density <= 0.0:
            raise ValueError("Material density must be positive.")
        if self.young_modulus is not None and self.young_modulus <= 0.0:
            raise ValueError("Young's modulus must be positive.")
        if self.poisson_ratio is not None and not -1.0 < self.poisson_ratio < 0.5:
            raise ValueError("Poisson's ratio must be between -1.0 and 0.5.")

    @property
    def E(self):
        """float: Young's modulus in pascals."""
        return self.young_modulus

    @property
    def poisson(self):
        """float: Poisson's ratio."""
        return self.poisson_ratio

    @property
    def shear_modulus(self):
        """float: Isotropic shear modulus in pascals."""
        if self.young_modulus is None or self.poisson_ratio is None:
            return None
        return self.young_modulus / (2.0 * (1.0 + self.poisson_ratio))

    @property
    def G(self):
        """float: Isotropic shear modulus in pascals."""
        return self.shear_modulus

    @property
    def __data__(self):
        return {
            "name": self.name,
            "density": self.density,
            "young_modulus": self.young_modulus,
            "poisson_ratio": self.poisson_ratio,
        }


class ThreeDECContactProperties(Data):
    """Direct contact parameters understood by the 3DEC deck renderer."""

    def __init__(
        self,
        stiffness_normal=100e9,
        stiffness_shear=70e9,
        friction=35.0,
        cohesion=0.0,
        tension=0.0,
        name=None,
    ):
        super().__init__(name=name)
        self.stiffness_normal = float(stiffness_normal)
        self.stiffness_shear = float(stiffness_shear)
        self.friction = float(friction)
        self.cohesion = float(cohesion)
        self.tension = float(tension)

    @property
    def __data__(self):
        return {
            "name": self.name,
            "stiffness_normal": self.stiffness_normal,
            "stiffness_shear": self.stiffness_shear,
            "friction": self.friction,
            "cohesion": self.cohesion,
            "tension": self.tension,
        }
