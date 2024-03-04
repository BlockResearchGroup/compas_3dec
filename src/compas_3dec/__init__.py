from __future__ import print_function

import os


__author__ = ["Alessandro Dell'Endice, Petras Vestartas"]
__copyright__ = "Block Research Group"
__license__ = "MIT License"
__email__ = "dellendice@arch.ethz.ch"
__version__ = "0.1.0"


HERE = os.path.dirname(__file__)

HOME = os.path.abspath(os.path.join(HERE, "../../"))
DATA = os.path.abspath(os.path.join(HOME, "data"))
DOCS = os.path.abspath(os.path.join(HOME, "docs"))
TEMP = os.path.abspath(os.path.join(HOME, "temp"))
log = "compas_3dec: 0.1.0"

__all__ = ["HOME", "DATA", "DOCS", "TEMP"]

__all_plugins__ = [
    "compas_3dec.scene",
    "compas_3dec.notebook.scene",
]


