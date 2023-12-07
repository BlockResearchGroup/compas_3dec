from __future__ import print_function
from __future__ import absolute_import
from __future__ import division

import os
import compas

__all__ = ["standard_material"]


class MechParam:
    def __init__(self):
        self.parameters = {
            "density": None,
            "jkn": None,
            "jks": None,
            "friction": None,
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
        mechparam.parameters["jkn"] = 90000000000
        mechparam.parameters["jks"] = 50000000000
        mechparam.parameters["friction"] = 35

        return mechparam
