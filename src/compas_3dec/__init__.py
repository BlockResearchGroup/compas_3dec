# ruff: noqa: F401

from compas_3dec.analysis import ThreeDECAnalysis
from compas_3dec.analysis import ThreeDECAnalysisBuilder
from compas_3dec.solver import find_3dec_executable
from compas_3dec.solver import ThreeDECSolver


__author__ = ["Alessandro Dell'Endice, Petras Vestartas"]
__copyright__ = "Block Research Group"
__license__ = "MIT License"
__email__ = "dellendice@arch.ethz.ch"
__version__ = "0.2.0"


__all__ = [
    "ThreeDECAnalysis",
    "ThreeDECAnalysisBuilder",
    "ThreeDECSolver",
    "find_3dec_executable",
]

__all_plugins__ = []
