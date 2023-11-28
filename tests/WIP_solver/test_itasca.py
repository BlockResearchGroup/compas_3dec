import itasca as it
import os
import json
import compas
import vec
from compas.datastructures import Mesh
it.command("python-reset-state false")

it.command("""
model new
model large-strain on
program call 'support_geometry.dat'
program call 'block_geometry.dat'


block contact generate-subcontacts
block property density 1500 range group 'Supports'
block contact property stiffness-normal 20000000000.0 stiffness-shear 8000000000.0 friction 90
block contact material-table default property stiffness-normal 20000000000.0 stiffness-shear 8000000000.0
block fix range group 'Supports'

block property density 1000 range group 'ale'
block contact generate-subcontacts
block contact property stiffness-normal 40000000000.0 stiffness-shear 6000000000.0 friction 90
block contact material-table default property stiffness-normal 40000000000.0 stiffness-shear 6000000000.0

block mechanical damping global


plot create
plot clear
plot active on
plot background 'white'
plot item create block

model gravity 0 0 -9.806
model solve ratio-local 1e-06
""")


