from __future__ import print_function
from __future__ import absolute_import
from __future__ import division

from enum import Enum

class Damping(Enum):
    GLOBAL = 1
    LOCAL = 2

class MechanicalParameters:
    def __init__(self):
        self.material = {}
        self._damping = None

    def __getitem__(self, value):
        return self.parameters[value]

    @property
    def damping(self):
        return self._damping

    @damping.setter
    def damping(self, value):
        if value is Damping.GLOBAL or value is Damping.GLOBAL.value:
            self._damping = "block mechanical damping global"
        elif value is Damping.LOCAL or value is Damping.LOCAL.value:
            self._damping = "block mechanical damping local"
        else:
            raise ValueError("Input has to be 1 for damping.Global or 2 for damping.Local")

    def add_material(self, name, density, friction_angle, young_modulus, poisson_ratio):
        self.material[name] = {
            "density": density,
            "friction_angle": friction_angle,
            "young_modulus": young_modulus,
            "poisson_ratio": poisson_ratio,
        }
        return self.material[name]

    def get_joint_stiffness_one_material(self, material, block_height, reduction_factor, block_length=None):
        E = material["young_modulus"]
        v = material["poisson_ratio"]
        G = E / (2 * (1 + v))

        if not block_length:
            jkn = E / block_height
            jks = G / block_height
        else:
            jkn = ((E / block_height) + (E / block_length)) / 2
            jks = ((G / block_height) + (G / block_length)) / 2

        jkn = jkn / reduction_factor
        jks = jks / reduction_factor

        return jkn, jks

    def get_joint_stiffness_two_materials(
        self, material_1, material_2, block_1_height, block_2_height, reduction_factor
    ):

        E1 = material_1["young_modulus"]
        v1 = material_1["poisson_ratio"]
        G1 = E1 / (2 * (1 + v1))

        E2 = material_2["young_modulus"]
        v2 = material_2["poisson_ratio"]
        G2 = E2 / (2 * (1 + v2))

        jkn = (E1 * E2) / ((block_1_height * E2) + (block_2_height * E1))
        jks = (G1 * G2) / ((block_1_height * G2) + (block_2_height * G1))

        jkn = jkn / reduction_factor
        jks = jks / reduction_factor

        return jkn, jks




