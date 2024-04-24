# This is a sample Python file generated programmatically

import itasca as it

it.command("""
;21/02/2024 17:23:26
model new
model large-strain on
program call 'geometry.dat'

block contact generate-subcontacts
block property density 2200 range group 'Supports'
block contact property stiffness-normal 150000.0 stiffness-shear 62500.0 friction 35
block contact material-table default property stiffness-normal 150000.0 stiffness-shear 62500.0
block fix range group 'Supports'

block property density 2200 range group 'Blocks'
block contact generate-subcontacts
block contact property stiffness-normal 150000.0 stiffness-shear 62500.0 friction 35
block contact material-table default property stiffness-normal 150000.0 stiffness-shear 62500.0

block mechanical damping global

;_______SAVE ANALYSIS_______________________________________________________
    model save "./init.sav" compress
;___________________________________________________________________________

;_______RESTORE ANALYSIS____________________________________________________
    model restore "./init.sav"
;___________________________________________________________________________

;GRAVITY APPLIED IN 10 STEPS 
;^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
;_____GRAVITY_____ step 1
model gravity 0 0 -0.981
model solve ratio-local 1e-06 time 0.02
;_____GRAVITY_____ step 2
model gravity 0 0 -1.962
model solve ratio-local 1e-06 time 0.02
;_____GRAVITY_____ step 3
model gravity 0 0 -2.943
model solve ratio-local 1e-06 time 0.02
;_____GRAVITY_____ step 4
model gravity 0 0 -3.924
model solve ratio-local 1e-06 time 0.02
;_____GRAVITY_____ step 5
model gravity 0 0 -4.905
model solve ratio-local 1e-06 time 0.02
;_____GRAVITY_____ step 6
model gravity 0 0 -5.886
model solve ratio-local 1e-06 time 0.02
;_____GRAVITY_____ step 7
model gravity 0 0 -6.867
model solve ratio-local 1e-06 time 0.02
;_____GRAVITY_____ step 8
model gravity 0 0 -7.848
model solve ratio-local 1e-06 time 0.02
;_____GRAVITY_____ step 9
model gravity 0 0 -8.829
model solve ratio-local 1e-06 time 0.02
;_____GRAVITY_____ step 10
model gravity 0 0 -9.81
model solve ratio-local 1e-06 time 0.02
model solve ratio-local 1e-06 time 1
;^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

;_______SAVE ANALYSIS_______________________________________________________
    model save "./grav.sav" compress
;___________________________________________________________________________
exit()
""")
