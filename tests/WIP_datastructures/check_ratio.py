import os
import compas
import vec
import itasca as it

ale = it.command(
    """
[mech.solve('ratio-local')]
"""
)

print(ale)
