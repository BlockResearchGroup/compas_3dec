import time
from enum import Enum
import os
from compas.geometry import normalize_vector, scale_vector, Vector


class ThreedecConfig:
    def __init__(self, model):
        self.material = {}
        self.jkn = None
        self.jks = None
        self.model = model


    def add_material(self, name, density, friction_angle, young_modulus, poisson_ratio):
        self.material[name] = {
            "density": density,
            "friction_angle": friction_angle,
            "young_modulus": young_modulus,
            "poisson_ratio": poisson_ratio,
        }
        return self.material[name]

    # =============================================================================
    # joint stiffness
    # =============================================================================
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

    # =============================================================================
    # damping
    # =============================================================================
    # refer to this link for documentation:
    # https://docs.itascacg.com/3dec700/3dec/block/doc/manual/block_manual/block_commands/block/cmd_block.mechanical.html#block.mechanical

    def set_damping_global(self, fac=False, f1=None, f2=None):
        header = "block mech damping global"

        if fac:
            header = "block mech damping global" + " " + str(fac) + " " + str(f1) + " " + str(f2)
        return header


    def set_damping_local(self,  custom = False, f=None):
        header = "block mech damping local"

        if custom:
            header = "block mech damping local" + " " + str(f)
        return header


    def set_damping_contact(self, damping_value):
        pass

    def set_damping_combined(self, damping_value):
        pass

    def set_damping_maxwell(self, damping_value):
        pass

    def set_damping_rayleigh(self, f1, f2, keyword):
        """This form of the command is normally used for dynamic calculations when a
        certain fraction of critical damping is required over a given frequency range.
        This type of damping is known as Rayleigh damping, where f1 = the fraction of
        critical damping operating at the center frequency of f2. See below for further
        discussion.
        keywords:
            mass = Restrict the damping to mass-proportional only.
            stiffness = Restrict the damping to stiffness-proportional only.
        """
        header = "block mech damping rayleigh" + " " + str(f1) + " " + str(f2) + " " + str(keyword)
        return header


    # =============================================================================
    # gravity.dat
    # =============================================================================
    def gravity_equilibrium(
        self, steps=10, keyword="ratio-local", ratio=1e-06, time=0.02, final_ratio=1e-06, time_final_step=1
    ):
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

        g = -9.806 / steps
        g = round(g, 3)
        text = ";===========================================================================" + "\n"
        text += ";GRAVITY APPLIED IN" + " " + str(steps) + " " + "STEPS " + "\n"
        text += ";===========================================================================" + "\n"
        for i in range(steps):
            gr = g * (i + 1)
            # header = ';^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^' + '\n'
            header = ";_____GRAVITY_____" + " " + "step" + " " + str(i + 1) + "\n"
            header += "model gravity" + " " + "0" + " " + "0" + " " + str(gr) + "\n"
            header += "model solve" + " " + str(keyword) + " " + str(ratio) + " " + "time" + " " + str(time) + "\n"
            text += header
        text += (
            "model solve"
            + " "
            + str(keyword)
            + " "
            + str(final_ratio)
            + " "
            + "time"
            + " "
            + str(time_final_step)
            + "\n"
        )
        return text

    def set_gravity_analysis(
        self,
        material_name,
        steps=10,
        keyword="ratio-local",
        ratio=1e-06,
        time_step=0.02,
        final_ratio=1e-05,
        time_final_step=1,
        ):

        self._check_and_delete_gravity_files(self.model.working_path)
        if not self.jkn or not self.jks:
            raise ValueError("Missing Joint Stiffness values")

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
    {4}
    """.format(
            self.material[material_name]["density"],
            self.jkn,
            self.jks,
            self.material[material_name]["friction_angle"],
            self.set_damping_global(),
        )
        main_string += create_header
        main_string += self.blocks_output()
        main_string += self.contacts_output()
        main_string += self.save_blocks_output("init_state")
        main_string += self.save_analysis("init")
        main_string += self.restore_analysis("init")
        main_string += "\n"
        main_string += self.gravity_equilibrium(steps, keyword, ratio, time_step, final_ratio, time_final_step)
        main_string += self.save_blocks_output("grav_state")
        main_string += self.save_contacts_output("contact_grav")
        main_string += self.save_analysis("grav")
        main_string += "exit()"
        output_path = self.model.working_path
        filename = "gravity.dat"
        with open(os.path.join(output_path, filename), "w") as file:
            file.write(main_string)
        return filename

    # =============================================================================
    # displacement.dat
    # =============================================================================

    def check_and_exit(self,solve_ratio):

        check_and_exit = """
;===========================================================================
; check equilibrium
;===========================================================================
fish define check_and_exit
    local ratio = mech.solve('ratio-local')
    if ratio > {} then
        system.command('exit')
    endif
end
@check_and_exit
    """.format(solve_ratio)
        return check_and_exit


    def get_model_timestep(self):
        with open(os.path.join(self.model.working_path, "grav_state.txt"), "r") as fo:
            for line in fo:
                line = line.strip()
                if not line:
                    continue
                parts = line.split()
                if not len(parts):
                    continue
                if parts[0] == "timestep":
                    timestep = float(parts[2])
        return timestep



    def set_block_displacement(self, region = 0, displacement_direction = [0,0,-1], displ_magnitude_per_step=0.001):
        displacement_direction = normalize_vector(displacement_direction)
        single_displacement_vector = scale_vector(displacement_direction, displ_magnitude_per_step)
        header = "block apply velocity-x " + str(single_displacement_vector[0]) + " range region " + str(region) + "\n"
        header += "block apply velocity-y " + str(single_displacement_vector[1]) + " range region " + str(region) + "\n"
        header += "block apply velocity-z " + str(single_displacement_vector[2]) + " range region " + str(region) + "\n"

        equilibrium = "block apply velocity-x 0.0 range region " + str(region) + "\n"
        equilibrium += "block apply velocity-y 0.0 range region " + str(region) + "\n"
        equilibrium += "block apply velocity-z 0.0 range region " + str(region) + "\n"

        displacement_data = [header, equilibrium]
        return displacement_data


    def set_blocks_displacement(self, regions, displacement_direction = [0,0,-1], displ_magnitude_per_step=0.001):
        displacement_direction = normalize_vector(displacement_direction)
        single_displacement_vector = scale_vector(displacement_direction, displ_magnitude_per_step)
        regions_str = ' '.join(str(r) for r in regions)
        header = "block apply velocity-x " + str(single_displacement_vector[0]) + " range region " + regions_str + "\n"
        header += "block apply velocity-y " + str(single_displacement_vector[1]) + " range region " + regions_str + "\n"
        header += "block apply velocity-z " + str(single_displacement_vector[2]) + " range region " + regions_str + "\n"

        equilibrium = "block apply velocity-x 0.0 range region " + regions_str + "\n"
        equilibrium += "block apply velocity-y 0.0 range region " + regions_str + "\n"
        equilibrium += "block apply velocity-z 0.0 range region " + regions_str + "\n"

        displacement_data = [header, equilibrium]
        return displacement_data


    def set_displacement_analysis(self, displacements_list, total_displacement = 0.0, displ_magnitude_per_step=0.001, solver_ratio = 0.00001, solver_time = 3, displacement_capacity = False):
        #get the model timestep calculated by 3DEC from the gravity file
        timestep = self.get_model_timestep()
        #number of solver cycles to reach the total displacement
        number_of_cycles = int(displ_magnitude_per_step/(displ_magnitude_per_step * timestep))

        if not os.path.join(self.model.working_path, "grav_state.txt"):
            raise ValueError("Missing gravity file: compute gravity first")

        main_string = ";" + time.strftime("%d/%m/%Y") + " " + time.strftime("%H:%M:%S")
        main_string += 2 * "\n"
        main_string += self.restore_analysis("grav")
        main_string += self.set_damping_local()
        main_string += 2 * "\n"
        main_string += self.blocks_output()
        main_string += self.contacts_output() + "\n"

        displacement_steps = int(total_displacement / displ_magnitude_per_step)
        if displacement_capacity:
            displacement_steps = 10000
        for step in range(displacement_steps+1):
            step_name =  "Displacement_step" + "_" + str(step+1) + "_distance_" + str((step+1)*displ_magnitude_per_step) + "m"
            main_string += ";==========================================================================="+ "\n"
            main_string += "; "+ str(step_name) +  "\n"
            main_string += ";==========================================================================="+ "\n"
            for displacement in displacements_list:
                main_string += displacement[0]
            main_string += "model cycle " + str(number_of_cycles) + "\n"
            main_string += "\n"
            main_string += ";==========================================================================="+ "\n"
            main_string += "; Equilibrium calculation" +  "\n"
            main_string += ";==========================================================================="+ "\n"
            for displacement in displacements_list:
                main_string += displacement[1]
            main_string += "model solve unbalanced-maximum {} time".format(solver_ratio) + " " + str(solver_time) + "\n"
            main_string += self.save_blocks_output(step_name)
            step_name_contact = step_name + "_contacts"
            main_string += self.save_contacts_output(step_name_contact)
            main_string += self.save_analysis(step_name)
            main_string += self.check_and_exit(solver_ratio)
            main_string += "\n"

            output_path = self.model.working_path
            filename = "displacement.dat"
            with open(os.path.join(output_path, filename), "w") as file:
                file.write(main_string)
        return filename


    # =============================================================================
    # load.dat
    # =============================================================================
    def _load_box(self, point,precision):
        """Create a bounding box range around a point 3D adding +/- the precision
            which can be used after the command 'boundary load' in 3DEC.
        point: xyz
            3D point where to apply the point load.
        precision: float
            dimension to add and subtract in x,y,z direction to the point 3D
            to create the box.
        """
        x1 = point[0]-precision
        x2 = point[0]+precision
        y1 = point[1]-precision
        y2 = point[1]+precision
        z1 = point[2]-precision
        z2 = point[2]+precision
        pl = 'range x '+ str(x1)+' ,'+ str(x2)+' y ' +str(y1)+' ,' +str(y2) +' z ' +str(z1)+' ,' +str(z2)
        return pl

    def _load_along_direction(self, pt1, pt2, load):
        vec = Vector.from_start_end(pt1,pt2)
        vec = normalize_vector(vec)
        load_components = ('xload ' + str(vec[0]*load)+' yload '+ str(vec[1]*load)+' zload '+ str(vec[2]*load))
        return load_components


    def set_point_load(self, application_point, direction_point, load_magnitude, radius, subcontacts_per_point):
        magnitude_per_point = load_magnitude / subcontacts_per_point
        load_vector = Vector.from_start_end(direction_point, application_point)
        load_vector = normalize_vector(load_vector)
        load_vector = scale_vector(load_vector, magnitude_per_point)
        string = "block gridpoint force-x " + str(load_vector[0]) + " range sphere c " + str(application_point[0]) + " " + str(application_point[1]) + " " + str(application_point[2]) + " r " + str(radius) + "\n"
        string += "block gridpoint force-y " + str(load_vector[1]) + " range sphere c " + str(application_point[0]) + " " + str(application_point[1]) + " " + str(application_point[2]) + " r " + str(radius) + "\n"
        string += "block gridpoint force-z " + str(load_vector[2]) + " range sphere c " + str(application_point[0]) + " " + str(application_point[1]) + " " + str(application_point[2]) + " r " + str(radius) + "\n"
        return string

    def set_points_load(self, points_list, load_magnitude, load_vector, radius, subcontacts_per_point):
        magnitude_per_point = load_magnitude / subcontacts_per_point
        for point in points_list:
            load_direction = normalize_vector(load_vector)
            load = scale_vector(load_direction, magnitude_per_point)
            string = "block gridpoint force-x " + str(load[0]) + " range sphere c " + str(point[0]) + " " + str(point[1]) + " " + str(point[2]) + " r " + str(radius) + "\n"
            string += "block gridpoint force-y " + str(load[1]) + " range sphere c " + str(point[0]) + " " + str(point[1]) + " " + str(point[2]) + " r " + str(radius) + "\n"
            string += "block gridpoint force-z " + str(load[2]) + " range sphere c " + str(point[0]) + " " + str(point[1]) + " " + str(point[2]) + " r " + str(radius) + "\n"
        return string

    def set_load_analysis(self, load_string, total_load, load_magnitude_per_step, number_of_cycles = 35000, load_capacity = False, solver_ratio = 0.00001):

        if not os.path.join(self.model.working_path, "grav_state.txt"):
            raise ValueError("Missing gravity file: compute gravity first")

        main_string = ";" + time.strftime("%d/%m/%Y") + " " + time.strftime("%H:%M:%S")
        main_string += 2 * "\n"
        main_string += self.restore_analysis("grav")
        main_string += self.set_damping_global()
        main_string += 2 * "\n"
        main_string += self.blocks_output()
        main_string += self.contacts_output() + "\n"

        load_steps = int(total_load / load_magnitude_per_step)
        if load_capacity:
            load_steps = 10000
        for step in range(load_steps+1):
            step_name =  "Load_step" + "_" + str(step+1) + "_load_magnitude_" + str((step+1)*load_magnitude_per_step) + "m"
            main_string += ";==========================================================================="+ "\n"
            main_string += "; "+ str(step_name) +  "\n"
            main_string += ";==========================================================================="+ "\n"
            main_string += load_string
            main_string += "model cycle " + str(number_of_cycles) + "\n"
            main_string += "\n"
            main_string += self.save_blocks_output(step_name)
            step_name_contact = step_name + "_contacts"
            main_string += self.save_contacts_output(step_name_contact)
            main_string += self.save_analysis(step_name)
            main_string += self.check_and_exit(solver_ratio)
            main_string += "\n"
            output_path = self.model.working_path
            filename = "load.dat"
            with open(os.path.join(output_path, filename), "w") as file:
                file.write(main_string)
        return filename


    # =============================================================================
    # stress.dat
    # =============================================================================
    def set_stress_capacity_analysis():
        pass

    # =============================================================================
    # FISH output functions
    # =============================================================================
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

;===========================================================================
; get blocks data
;===========================================================================
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
    """

        return blocks_output

    def save_blocks_output(self, state):
        save_blocks_output = """
;===========================================================================
; save blocks output
;===========================================================================
log on
log-file '{}.txt'
@blocks_output
log off
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
;===========================================================================
; get contacts data
;===========================================================================
fish define contacts_output
loop foreach ic block.contact.list()
ii=io.out('contact'+' '+'='+' '+string(ic)+' '+string(block.contact.type(ic))+' '+string(block.region(block.contact.b1(ic)))+' '+string(block.region(block.contact.b2(ic)))+' '+string(block.contact.pos(ic))+' '+string(block.contact.normal(ic)))
    loop foreach si block.contact.subcontactlist(ic)
        ii=io.out('subcontact'+' '+'='+' '+string(block.subcontact.pos(si))+' '+string(block.subcontact.force.norm(si))+' '+string(block.subcontact.force.shear(si))+' '+string(si)+' '+string(block.subcontact.disp.norm(si))+' '+string(block.subcontact.disp.shear(si))+' '+string(block.subcontact.stress.norm(si))+' '+string(block.subcontact.stress.shear(si))+' '+string(block.subcontact.area(si)))
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

    """
        return contacts_output

    def save_contacts_output(self, state):
        save_contacts_output = """
;===========================================================================
; save contacts output
;===========================================================================
log on
log-file '{}.txt'
@contacts_output
log off
    """.format(
            state
        )
        return save_contacts_output

    # =============================================================================
    # analysis utilities
    # =============================================================================
    def save_analysis(self, stage):
        """
        Stages:     init
                    grav
                    step
        """
        save_analysis = """
;===========================================================================
; save analysis
;===========================================================================
model save "./{}.sav" compress
""".format(
            stage
        )
        return save_analysis

    def restore_analysis(self, stage):
        """
        Stages:     init
                    grav
                    step
        """
        restore_analysis = """
;===========================================================================
; restore analysis
;===========================================================================
model restore "./{}.sav"
""".format(
            stage
        )
        return restore_analysis

    def _check_and_delete_gravity_files(self, current_directory):
        # Get the current working directory
        # current_directory = os.getcwd()
        print(f"Checking in the current directory: {current_directory}")

        # List of files to check and potentially delete
        files_to_check = ["init_state.txt", "grav_state.txt", "contact_grav.txt"]

        # Iterate through each file in the list
        for file_name in files_to_check:
            # Construct the full path to the file
            full_path = os.path.join(current_directory, file_name)

            # Check if the file exists
            if os.path.exists(full_path):
                # If the file exists, delete it
                os.remove(full_path)
                print(f"Deleted {file_name}")
            else:
                # If the file does not exist, print a message
                print(f"{file_name} does not exist in the current directory and was not deleted")

