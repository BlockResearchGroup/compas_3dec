import os
import compas
import time
import compas_rhino
from compas_3dec.Geometry import Model
from compas_3dec.Parameters import MechParam
from compas_3dec.Utilities import overwrite_file
from compas_3dec.Utilities import threedec7_support_description
from compas_3dec.Utilities import threedec7_block_description
from compas_3dec.Utilities import main_file



__all__ = ['selfweight']


class Analysis():
    """The Analysis class contains all the methods to setup a 3DEC analysis.

    Examples
    --------
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
        self.model = None
        self.mechparam = None
        self.name = name

    # @property
    # def data(self):
    #     """dict : A data dict representing the shape data structure for serialization.
    #     """
    #     data = {
    #         'mechparam': self.mechparam.data,
    #         'model': self.model.data,
    #         'name': self.name,
    #         'settings': self.settings
    #     }
    #     return data

    # @data.setter
    # def data(self, data):
    #     if 'data' in data:
    #         data = data['data']
    #     self.settings = data.get('settings') or {}
    #     self.name = data.get('name')

    #     mechparamdata = data.get('mechparam', None)
    #     modeldata = data.get('model', None)

    #     self.mechparam = None
    #     self.model = None

    #     if mechparamdata:
    #         self.mechparam = MechParam.from_data(mechparamdata)
    #     if modeldata:
    #         self.model = Model.from_data(modeldata)

    @classmethod
    # model = Model.from_rhino_select(path)
    # mechparam = MechParam.standard_material()
    # path = os.path.dirname(__file__)


    # def selfweight(cls, model, mechparam, path):
    #     supports = []
    #     blocks = []
    #     for node in model.nodes():
    #         if model.graph.node_attribute(node, "is_support") == True:
    #             support = model.node_block(node)
    #             supports.append(support)
    #         else:
    #             block = model.node_block(node)
    #             blocks.append(block)
    #             group = model.graph.node_attribute(node, "3dec_group")
    #     # create support_geometry.dat
    #     name = 'support_geometry.dat'
    #     geometry_path = os.path.join(path, name)
    #     string = ';__create geometry__' + '\n'
    #     for i in range(len(supports)):
    #         string += threedec7_support_description(supports[i], precision=10)
    #     overwrite_file(geometry_path, string)
    #     # create block_geometry.dat
    #     name = 'block_geometry.dat'
    #     geometry_path = os.path.join(path, name)
    #     string = ';__create geometry__' + '\n'
    #     for i in range(len(blocks)):
    #         string += threedec7_block_description(
    #             blocks[i], group, precision=10)
    #     overwrite_file(geometry_path, string)
    #     main_file(mechparam, path)
    #     return


    def selfweight(cls, model, mechparam, path):
        title = compas_rhino.rs.GetString("Analysis Title")
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




