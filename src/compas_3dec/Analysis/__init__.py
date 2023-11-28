
"""
********************************************************************************
compas_3dec.analysis
********************************************************************************

.. currentmodule:: compas_3dec.analysis

Classes
=======

.. autosummary::
    :toctree: generated/
    :nosignatures:

    Analysis

Routines
========

.. autosummary::
    :toctree: generated/
    :nosignatures:

    selfweight
    displacement_capacity
    load_capacity
    geometry_dat
    main_dat


"""

from .analysis import Analysis

# from .routines import (
#     selfweight,
#     displacement_capacity,
#     load_capacity
# )

__all__ = [name for name in dir() if not name.startswith('_')]
