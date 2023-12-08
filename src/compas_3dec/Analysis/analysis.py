import os
import time
from compas_3dec.datastructures import Assembly_3dec
from compas_3dec.mechanical import MechParam
from compas_3dec.utilities import (
    blocks_output,
    save_blocks_output,
    save_analysis,
    restore_analysis,
    contacts_output,
    save_contacts_output,
    gravity_equilibrium,
    find_duplicate_dict,
    overwrite_file,
    threedec7_support_description,
    threedec7_block_description

)

__all__ = ["selfweight", "geometry_dat_concave", "geometry_dat_convex", "main_dat_txt"]

class Analysis:
    """The Analysis class contains all the methods to setup a 3DEC analysis.

    Attributes
    ----------
    name : str
        Name of the analysis.

    settings : dict
        Dictionary to store analysis settings.

    assembly_3dec : compas_3dec.assembly.Assembly3D
        3DEC assembly object.

    mechparam : compas_3dec.parameters.MechParam
        3DEC mechanical parameters.

    Examples
    --------
    # change example
    >>> from compas_3dec.analysis import Analysis
    >>> from compas_3dec.geometry import Model
    >>> from compas_3dec.parameters import MechParam
    >>> model = Model.from_layers()
    >>> support_material = MechParam.material(density,friction, jkn, jks)
    >>> block_material = MechParam.material(density,friction, jkn, jks)
    >>> mechparam = MechParam.mechparam(support_material,block_material)
    >>> analysis = Analysis.selfweight(mechparam, model)
    """

    def __init__(self, name="Analysis"):
        self.settings = {}
        self.assembly_3dec = None
        self.mechparam = None
        self.name = name


    @classmethod
    def main_dat_txt(cls, parameters, path, title):
        """Create the main.dat file essential for running a 3DEC analysis. Once in
        3DEC, it calls the .dat files with the geometry of blocks and supports, gets the
        mechanical parameters, and applies gravity to the model. Moreover, it exports the
        3DEC results in .txt files and saves .sav files of the analysis.

        Parameters
        ----------
        parameters : MechParam
            Mechanical parameters.
        path : _str_
            Path where the .txt file will be saved.
        title : _str_
            The title given from the user to the analysis.

        Returns
        -------
        str
            The content of the main.dat file.
        """

        name = "main.dat"
        main_path = os.path.join(path, name)
        main_string = ";{} {}".format(time.strftime("%d/%m/%Y"), time.strftime("%H:%M:%S"))

        create_header = """
        model new
        model large-strain on
        program call 'support_geometry.dat'
        program call 'block_geometry.dat'

        block contact generate-subcontacts
        block property density {0} range group 'Supports'
        block contact property stiffness-normal {1} stiffness-shear {2} friction {3}
        block contact material-table default property stiffness-normal {1} stiffness-shear {2}
        block fix range group 'Supports'

        block property density 1000 range group 'Blocks'
        block contact generate-subcontacts
        block contact property stiffness-normal {1} stiffness-shear {2} friction {3}
        block contact material-table default property stiffness-normal {1} stiffness-shear {2}

        block mechanical damping {4}

        plot create
        plot clear
        plot active on
        plot background 'white'
        plot item create block
        """.format(
            parameters.parameters["density"],
            parameters.parameters["jkn"],
            parameters.parameters["jks"],
            parameters.parameters["friction"],
            "global",
        )
        main_string += create_header
        main_string += blocks_output()
        main_string += save_blocks_output("init_state")
        main_string += contacts_output()
        main_string += save_contacts_output("contacts_init")
        main_string += save_analysis(title, "init")
        main_string += restore_analysis(title, "init")
        main_string +=  '\n'
        main_string += gravity_equilibrium(10,'ratio-local',1e-4,0.02,1e-5,1)
        main_string += save_blocks_output("grav_state")
        main_string += save_contacts_output("contact_grav")
        main_string += save_analysis(title, "grav")
        main_string += "exit()"
        overwrite_file(main_path, main_string)
        return main_string

    @classmethod
    def main_dat(cls, parameters, path, title):
        """Create the main.dat file essential for running a 3DEC analysis. Once in
        3DEC, it calls the .dat files with the geometry of blocks and supports, gets the
        mechanical parameters, and applies gravity to the model.

        Parameters
        ----------
        parameters : MechParam
            Mechanical parameters.
        path : _str_
            Path where the .txt file will be saved.
        title : _str_
            The title given from the user to the analysis.

        Returns
        -------
        str
            The content of the main.dat file.
        """
        parameters = MechParam.standard_material()
        name = "main.dat"
        main_path = os.path.join(path, name)
        main_string = ";" + time.strftime("%d/%m/%Y") + " " + time.strftime("%H:%M:%S")
        create_header = """
        model new
        model large-strain on
        program call 'support_geometry.dat'
        program call 'block_geometry.dat'

        block contact generate-subcontacts
        block property density {0} range group 'Supports'
        block contact property stiffness-normal {1} stiffness-shear {2} friction {3}
        block contact material-table default property stiffness-normal {1} stiffness-shear {2}
        block fix range group 'Supports'

        block property density 1000 range group 'Blocks'
        block contact generate-subcontacts
        block contact property stiffness-normal {1} stiffness-shear {2} friction {3}
        block contact material-table default property stiffness-normal {1} stiffness-shear {2}

        block mechanical damping {4}

        plot create
        plot clear
        plot active on
        plot background 'white'
        plot item create block
        """.format(
            parameters.parameters["density"],
            parameters.parameters["jkn"],
            parameters.parameters["jks"],
            parameters.parameters["friction"],
            "global",
        )
        main_string += create_header
        main_string += save_analysis(title, "init")
        main_string += restore_analysis(title, "init")
        main_string +=  '\n'
        main_string += gravity_equilibrium(10,'ratio-local',1e-4,0.02,1e-5,1)
        main_string += save_analysis(title, "grav")
        main_string += "exit()"
        overwrite_file(main_path, main_string)
        return
