"""
********************************************************************************
compas_3dec.assembly_3dec
********************************************************************************

.. currentmodule:: compas_3dec.assembly_3dec

Classes
=======

.. autosummary::
    :toctree: generated/
    :nosignatures:

    Model

Routines
========

.. autosummary::
    :toctree: generated/
    :nosignatures:

    from_rhino_select_convex
    from_rhino_select_concave
    from_assembly
    geometry_dat

"""
from .assembly_3dec import Assembly_3dec


__all__ = [name for name in dir() if not name.startswith("_")]
