


import itasca as it

it.command("""
model new
model large-strain on
program call 'support_geometry.dat'
program call 'block_geometry.dat'

block contact generate-subcontacts
block property density 2200 range group 'Supports'
block contact property stiffness-normal 90000000000 stiffness-shear 50000000000 friction 35
block contact material-table default property stiffness-normal 90000000000 stiffness-shear 50000000000
block fix range group 'Supports'

block property density 1000 range group 'Blocks'
block contact generate-subcontacts
block contact property stiffness-normal 90000000000 stiffness-shear 50000000000 friction 35
block contact material-table default property stiffness-normal 90000000000 stiffness-shear 50000000000

block mechanical damping global

plot create
plot clear
plot active on
plot background 'white'
plot item create block

;_______SAVE ANALYSIS_______________________________________________________
    model save "./Analysis_test_init.sav" compress
;___________________________________________________________________________

;_______RESTORE ANALYSIS____________________________________________________
    model restore "./Analysis_test_init.sav"
;___________________________________________________________________________

        model gravity 0 0 -9.806
        model solve ratio-local 1e-10 time 1



fish define mech
    ii = io.out('solve ratio = '+' '+string(mech.solve('ratio-local')))
    return ii
    end
    [mech]
;_______SAVE ANALYSIS_______________________________________________________
    model save "./Analysis_test_grav.sav" compress
;___________________________________________________________________________

""")

import itasca as it
import vec
from compas.geometry import norm_vector

unba = []
for b in it.block.list():
    if it.block.Block.is_fix(b) == False:
        unbalanced_force = it.block.Block.force_unbal(b)
        unbalanced_force_vec = round(vec.vec3.x(unbalanced_force)/1000,8), round(vec.vec3.y(unbalanced_force)/1000,8), round(vec.vec3.z(unbalanced_force)/1000,8)
        unb = norm_vector(unbalanced_force_vec)
        mass = it.block.Block.mass(b)
        weight = round((mass*9.806)/1000,8)
        ratio = (weight-unb)
        unba.append(ratio)

total = sum(unba)
le = len(unba)
average = total/le
print (average)

if average > 1.0000e-05:
    it.command("""
        model gravity 0 0 -9.806
        model solve ratio-local 1e-06 time 3
        [mech.solve('ratio-local')]
        """)
else:
    print ('equilibrium reached')
        
        
        
        
        
        
        