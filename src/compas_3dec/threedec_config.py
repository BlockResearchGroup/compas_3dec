import time
from enum import Enum
import inspect
import os
from compas_3dec.utilities import overwrite_file, check_and_delete_gravity_files

class Damping(Enum):
    GLOBAL = 1
    LOCAL = 2

class ThreedecConfig:

    def __init__(self):
        self.material = {}
        self._damping = "global"
        self.jkn = None
        self.jks = None

    @property
    def damping(self):
        return self._damping

    @damping.setter
    def damping(self, value):
        if value is Damping.GLOBAL or value is Damping.GLOBAL.value:
            self._damping = "global"
        elif value is Damping.LOCAL or value is Damping.LOCAL.value:
            self._damping = "local"
        else:
            raise ValueError("Input has to be 1 for damping.Global or 2 for damping.Local")

    def add_material(self, name, density, friction_angle, young_modulus, poisson_ratio):
        self.material[name] = {
            "density": density,
            "friction_angle": friction_angle,
            "young_modulus": young_modulus,
            "poisson_ratio": poisson_ratio,
        }
        return self.material[name]

    def get_joint_stiffness_one_material(self, material_name, block_height, reduction_factor, block_length=None):
        E = self.material[material_name]["young_modulus"]
        v = self.material[material_name]["poisson_ratio"]
        G = E / (2 * (1 + v))

        if not block_length:
            jkn = E / block_height
            jks = G / block_height
        else:
            jkn = ((E / block_height) + (E / block_length)) / 2
            jks = ((G / block_height) + (G / block_length)) / 2

        self.jkn = jkn / reduction_factor
        self.jks = jks / reduction_factor


        return self.jkn, self.jks

    def get_joint_stiffness_two_materials(
        self, material_1, material_2, block_1_height, block_2_height, reduction_factor
    ):

        E1 = self.material[material_1]["young_modulus"]
        v1 = self.material[material_1]["poisson_ratio"]
        G1 = E1 / (2 * (1 + v1))

        E2 = self.material[material_2]["young_modulus"]
        v2 = self.material[material_2]["poisson_ratio"]
        G2 = E2 / (2 * (1 + v2))

        jkn = (E1 * E2) / ((block_1_height * E2) + (block_2_height * E1))
        jks = (G1 * G2) / ((block_1_height * G2) + (block_2_height * G1))

        self.jkn = jkn / reduction_factor
        self.jks = jks / reduction_factor

        return self.jkn, self.jks

    def save_analysis(self,stage):
        """
        Stages:     init
                    grav
                    step
        """
        save_analysis = """
;_______SAVE ANALYSIS_______________________________________________________
    model save "./{}.sav" compress
;___________________________________________________________________________
""".format(stage)
        return save_analysis

    def restore_analysis(self, stage):
        """
        Stages:     init
                    grav
                    step
        """
        restore_analysis = """
;_______RESTORE ANALYSIS____________________________________________________
    model restore "./{}.sav"
;___________________________________________________________________________
""".format(
            stage
        )
        return restore_analysis


    def gravity_equilibrium(self, steps=10, keyword="ratio-local", ratio=1e-06, time=0.02, final_ratio=1e-06, time_final_step=1):
        """_summary_

        Parameters
        ----------
        steps : _type_
            _description_
        keyword : _type_
            _description_
        ratio : _type_
            _description_
        time : _type_
            _description_
        final_ratio : _type_
            _description_
        time_final_step : _type_
            _description_

        Returns
        -------
        _type_
            _description_
        """

        g = (-9.806 / steps)
        g = round(g, 3)
        text = ';GRAVITY APPLIED IN' + ' ' + str(steps) + ' ' + 'STEPS ' + '\n'
        text += ';^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^' + '\n'
        for i in range(steps):
            gr = g * (i+1)
            # header = ';^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^' + '\n'
            header = ';_____GRAVITY_____' + " " + 'step' + " " + str(i+1) + '\n'
            header += 'model gravity' + ' ' + '0' + " " + '0' + " " + str(gr) + '\n'
            header += 'model solve' + " " + str(keyword) +  " " + str(ratio) + \
                " " + 'time' + " " + str(time) + '\n'
            text += header
        text += 'model solve' + " " + str(keyword) + " " +str(final_ratio) + \
                " " + 'time' + " " + str(time_final_step) + '\n'
        text += ';^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^' + '\n'
        return text


    def blocks_output(self):
        """FISH function: get blocks data from 3DEC analysis:

        Returns
        -------
        per block:
            region n in 3DEC
                int
            centroid
                x,y,z (precision = 18)
            mass
                float [Kg]
            volume
                float [mc]
            out of balance force
                fx,fy,fz [N]
            moments
                mx,my,mz [Nm]
            loads
                lx,ly,lz [N]
            velocity
                (vx,vy,vz) [m/s]
            list of vertices (coordinates)
                x,y,z (precision = 18)
        """
        blocks_output = """

    ;___________________________________________________________________________
    fish define blocks_output
        ii = io.out('solve ratio = '+' '+string(mech.solve('ratio-local')))
        ii = io.out('timestep = '+' '+string(mech.timestep))
        ii=io.out(' centr - result - veloc')
        ic = block.contact.head
        loop foreach ib block.list
            bid = block.id(ib)
            br=block.region(ib)
        ii=io.out('block '+string(bid))
        ii=io.out('region '+string(br))
        ii=io.out('centroid'+' '+'='+' '+string(block.pos.x(ib))+','+string(block.pos.y(ib))+','+string(block.pos.z(ib))+' '+string(br))
        ii=io.out('mass '+' '+string(block.mass(ib)))
        ii=io.out('volume '+' '+string(block.vol(ib)))
        vel=block.vel(ib)
        rx=block.force.unbal.x(ib)
        ry=block.force.unbal.y(ib)
        rz=block.force.unbal.z(ib)
        lx=block.force.app.x(ib)
        ly=block.force.app.y(ib)
        lz=block.force.app.z(ib)
        ; if there is gravity, the block weight should be added
        rz=block.force.unbal.z(ib)+block.mass(ib)*global.gravity.z
        ii=io.out('forces'+' '+'='+' '+string(rx)+','+string(ry)+','+string(rz)+' '+string(br))
        ii=io.out('moment'+' '+'='+' '+string(block.moment.x(ib))+','+string(block.moment.y(ib))+','+string(block.moment.z(ib))+' '+string(br))
        ii=io.out('loads'+' '+'='+' '+string(lx)+','+string(ly)+','+string(lz)+' '+string(br))
        ii=io.out('velocity'+' '+'='+' '+string(vel)+' '+string(br))
        loop foreach vi block.gplist(ib)
            ii = io.out('vertex'+' '+'='+' '+string(block.gp.pos(vi))+' '+string(block.region(block.gp.hostblock(vi))))
            vi = block.gp.next(vi)
        endloop
        ib = block.next(ib)
        endloop
    end
    ;___________________________________________________________________________
    """
        return blocks_output


    def save_blocks_output(self,state):
        save_blocks_output = """
    ;___________________________________________________________________________
    log on
    log-file '{}.txt'
    @blocks_output
    log off
    ;___________________________________________________________________________
    """.format(
            state
        )
        return save_blocks_output


    def contacts_output(self):
        """FISH function: get contacts data from 3DEC analysis:

        Returns
        -------

        """
        contacts_output = """
    ;___________________________________________________________________________
    fish define contacts_output
    loop foreach ic block.contact.list()
    ii=io.out('contact'+' '+'='+' '+string(ic)+' '+string(block.contact.type(ic))+' '+string(block.region(block.contact.b1(ic)))+' '+string(block.region(block.contact.b2(ic)))+' '+string(block.contact.pos(ic))+' '+string(block.contact.normal(ic)))
        loop foreach si block.contact.subcontactlist(ic)
            ii=io.out('subcontact'+' '+'='+' '+string(block.subcontact.pos(si))+' '+string(block.subcontact.force.norm(si))+' '+string(block.subcontact.force.shear(si))+' '+string(si)+' '+string(block.subcontact.disp.norm(si))+' '+string(block.subcontact.disp.shear(si)))
            fi = block.subcontact.face(si)
            if fi then
                fo = block.face.bface(fi)
                ii = io.out('face centroid'+' '+'='+' '+string(block.face.pos(fo)))
            endif
            si = block.subcontact.next(si)
        endloop
    ic = block.contact.next(ic)
    endloop
    end
    ;___________________________________________________________________________
    """
        return contacts_output


    def save_contacts_output(self, state):
        save_contacts_output = """
    ;___________________________________________________________________________
    log on
    log-file '{}.txt'
    @contacts_output
    log off
    ;___________________________________________________________________________
    """.format(
            state
        )
        return save_contacts_output

    def get_gravity_input(self, material_name):

        if not self.jkn or not self.jks:
            raise ValueError ("Missing Joint Stiffness values")

        if not self.damping:
            raise ValueError ("Missing damping value")

        main_string = ";" + time.strftime("%d/%m/%Y") + " " + time.strftime("%H:%M:%S")
        create_header = """
model new
model large-strain on
program call 'geometry.dat'

block contact generate-subcontacts
block property density {0} range group 'Supports'
block contact property stiffness-normal {1} stiffness-shear {2} friction {3}
block contact material-table default property stiffness-normal {1} stiffness-shear {2}
block fix range group 'Supports'

block property density {0} range group 'Blocks'
block contact generate-subcontacts
block contact property stiffness-normal {1} stiffness-shear {2} friction {3}
block contact material-table default property stiffness-normal {1} stiffness-shear {2}

block mechanical damping {4}
""".format(
            self.material[material_name]["density"],
            self.jkn,
            self.jks,
            self.material[material_name]["friction_angle"],
            self.damping
        )
        main_string += create_header
        main_string += self.blocks_output()
        main_string += self.contacts_output()
        main_string += self.save_blocks_output("init_state")
        main_string += self.save_analysis("init")
        main_string += self.restore_analysis("init")
        main_string +=  '\n'
        main_string += self.gravity_equilibrium(steps, keyword, ratio, time_step, final_ratio, time_final_step)
        main_string += self.save_blocks_output("grav_state")
        main_string += self.save_contacts_output("contact_grav")
        main_string += self.save_analysis("grav")
        main_string += "exit()"
        return main_string



    def set_gravity_analysis(self, material_name, steps=10, keyword="ratio-local", ratio=1e-06, time_step=0.02, final_ratio=1e-05, time_final_step=1):

        caller_frame = inspect.stack()[1]
        caller_filename = caller_frame.filename
        current_directory = os.path.dirname(os.path.abspath(caller_filename))

        check_and_delete_gravity_files(current_directory)

        if not self.jkn or not self.jks:
            raise ValueError ("Missing Joint Stiffness values")

        if not self.damping:
            raise ValueError ("Missing damping value")

        main_string = ";" + time.strftime("%d/%m/%Y") + " " + time.strftime("%H:%M:%S")
        create_header = """
model new
model large-strain on
program call 'geometry.dat'

block contact generate-subcontacts
block property density {0} range group 'Supports'
block contact property stiffness-normal {1} stiffness-shear {2} friction {3}
block contact material-table default property stiffness-normal {1} stiffness-shear {2}
block fix range group 'Supports'

block property density {0} range group 'Blocks'
block contact generate-subcontacts
block contact property stiffness-normal {1} stiffness-shear {2} friction {3}
block contact material-table default property stiffness-normal {1} stiffness-shear {2}

block mechanical damping {4}
""".format(
            self.material[material_name]["density"],
            self.jkn,
            self.jks,
            self.material[material_name]["friction_angle"],
            self.damping
        )
        main_string += create_header
        main_string += self.blocks_output()
        main_string += self.contacts_output()
        main_string += self.save_blocks_output("init_state")
        main_string += self.save_analysis("init")
        main_string += self.restore_analysis("init")
        main_string +=  '\n'
        main_string += self.gravity_equilibrium(steps, keyword, ratio, time_step, final_ratio, time_final_step)
        main_string += self.save_blocks_output("grav_state")
        main_string += self.save_contacts_output("contact_grav")
        main_string += self.save_analysis("grav")
        main_string += "exit()"
        caller_frame = inspect.stack()[1]
        caller_filename = caller_frame.filename
        output_path = os.path.dirname(os.path.abspath(caller_filename))
        filename = "gravity.dat"
        with open(os.path.join(output_path,filename), 'w') as file:
            file.write(main_string)
        return filename
