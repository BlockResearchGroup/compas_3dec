import os
import compas
import time
# import compas_rhino
from compas_3dec.datastructures import Assembly_3dec
from compas_3dec.mechanical import MechParam
from compas_3dec.utilities import overwrite_file
from compas_3dec.utilities import threedec7_support_description
from compas_3dec.utilities import threedec7_block_description
# from compas_3dec.utilities import main_file
from compas_3dec.utilities import blocks_output, save_blocks_output, save_analysis, restore_analysis, contacts_output, save_contacts_output



__all__ = ['selfweight',
           'geometry_dat',
           'main_dat'
           ]


class Analysis():
    """The Analysis class contains all the methods to setup a 3DEC analysis.

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
    def selfweight(cls, model, mechparam, path):
        # title = compas_rhino.rs.GetString("Analysis Title")
        string_s = ';__create geometry__' + '\n'
        string_b = ';__create geometry__' + '\n'
        for node in model.nodes():
            if model.graph.node_attribute(node, "is_support") == True:
                support = model.node_block(node)
                # create support_geometry.dat
                name = 'support_geometry.dat'
                geometry_path_s = os.path.join(path, name)
                string_s += threedec7_support_description(support,node, precision=10)
            else:
                block = model.node_block(node)
                group = model.graph.node_attribute(node, "3dec_group")
                name = 'block_geometry.dat'
                geometry_path_b = os.path.join(path, name)
                string_b += threedec7_block_description(
                block, group,node, precision=10)
        overwrite_file(geometry_path_s, string_s)
        overwrite_file(geometry_path_b, string_b)
        main_file(mechparam, path,title)
        return

    @classmethod
    def geometry_dat(cls, assembly_3dec, path):
        """Create .dat files for 3DEC with the Block's geometry from an
        Assembly_3DEC object.

        Parameters
        ----------
        assembly_3dec : _type_
            _description_
        path : _type_
            _description_
        """
        # title = compas_rhino.rs.GetString("Analysis Title")
        string_s = ';__create geometry__' + '\n'
        string_b = ';__create geometry__' + '\n'
        for node in assembly_3dec.nodes():
            if assembly_3dec.graph.node_attribute(node, "is_support") == True:
                support = assembly_3dec.node_block(node)
                name = 'support_geometry.dat'
                geometry_path_s = os.path.join(path, name)
                string_s += threedec7_support_description(support,node, precision=10)
            else:
                block = assembly_3dec.node_block(node)
                group = assembly_3dec.graph.node_attribute(node, "3dec_group")
                name = 'block_geometry.dat'
                geometry_path_b = os.path.join(path, name)
                string_b += threedec7_block_description(
                block, group,node, precision=10)
        overwrite_file(geometry_path_s, string_s)
        overwrite_file(geometry_path_b, string_b)
        return

    @classmethod
    def main_dat(cls,parameters, path,title):
        parameters = MechParam.standard_material()
        name = 'main.dat'
        main_path = os.path.join(path, name)
        main_string = ';' + time.strftime("%d/%m/%Y") + ' ' + time.strftime("%H:%M:%S")
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
        """.format(parameters.parameters['density'], parameters.parameters['jkn'], parameters.parameters['jks'], parameters.parameters['friction'], 'global')
        main_string += create_header
        main_string += blocks_output()
        main_string += save_blocks_output('init')
        main_string += contacts_output()
        main_string += save_contacts_output('init')
        main_string += save_analysis(title,'init')
        main_string += restore_analysis(title,'init')
        main_string += """
        model gravity 0 0 -9.806
        model solve ratio-local 1e-06
        """
        main_string += save_blocks_output('grav')
        main_string += save_contacts_output('grav')
        main_string += save_analysis(title,'grav')
        overwrite_file(main_path, main_string)

        return
