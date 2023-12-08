from __future__ import print_function
from __future__ import absolute_import
from __future__ import division

import os
import compas

__all__ = ["standard_material", "custom_material"]


class MechParam:
    def __init__(self):
        self.parameters = {
            "name"  : None,
            "density": None,
            "jkn": None,
            "jks": None,
            "friction": None,
            "E"     : None,
            "v"     : None
        }

    @classmethod
    def standard_material(cls):
        """_summary_

        Parameters
        -------
        density kg/mc
        jkn Pascal
        jks Pascal
        friction degrees

        Returns
        -------
        :class:`~compas_3dec.mechparam.MechParam`
            The mechanical parameters of the material
        """
        mechparam = cls()
        mechparam.parameters["density"] = 2200
        mechparam.parameters["jkn"] = 100000000000
        mechparam.parameters["jks"] = 50000000000
        mechparam.parameters["friction"] = 35

        return mechparam

    def custom_material(cls,name,density,friction_angle, youngs_modulus, poisson_ratio):
        """Create a custom material with all the parameters needed by 3DEC to calculate
        joint stiffness values and the other material properties.

        Parameters
        ----------
        name    : _str_
            The name of the material.
        density : _float_
            The density of the material in kg/m3.
        friction_angle : _float_
            The static friction angle of the material in degree.
        youngs_modulus : _float_
            The Young's modulus of the material in Pascal.
        poisson_ratio : _float_
            The Poisson ratio of the material.

        Returns
        -------
        :class:`~compas_3dec.mechparam.MechParam`
            The mechanical parameters of the material
        """

        mechparam = cls()

        mechparam.parameters["name"] = name
        mechparam.parameters["density"] = density
        mechparam.parameters["friction"] = friction_angle
        mechparam.parameters["E"] = youngs_modulus
        mechparam.parameters["v"] = poisson_ratio

        return mechparam


def joint_stiffness_one_material(cls, material, block_height, reduction_factor):

    E = material.parameters["E"]
    v = material.parameters["v"]
    G = E/(2*(1+v))

    jkn = (E/block_height)
    jks = (G/block_height)

    # average joint stiffness along two main directions
    # jkn = ((E/block_height)+(E/block_length))/2
    # jks = ((G/block_height)+(G/block_length))/2

    jkn = jkn / reduction_factor
    jks = jks / reduction_factor

    return jkn, jks

def joint_stiffness_two_materials(cls,material1,material2,block_height, block_length, reduction_factor):

    E1 = material1.parameters["E"]
    v1 = material1.parameters["v"]
    G1 = E1/(2*(1+v1))

    E2 = material1.parameters["E"]
    v2 = material1.parameters["v"]
    G1 = E2/(2*(1+v2))

    jkn = (E1*E2)/((block_height*E2)+(layer_height*E1))
    jks = (G1*G2)/((block_height*G2)+(layer_height*G1))



    jkn = jkn / reduction_factor
    jks = jks / reduction_factor

    return jkn, jks
