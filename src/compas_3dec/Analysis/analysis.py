import os
import compas
from compas_3dec.Geometry import Model
from compas_3dec.Parameters import MechParam
from compas_3dec.Utilities import overwrite_file
from compas_3dec.Utilities import threedec7_support_description
from compas_3dec.Utilities import threedec7_block_description



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




    def selfweight(cls,model,mechparam,path):

        supports = []
        blocks = []
        for node in model.nodes():
            if model.graph.node_attribute(node, "is_support") == True:
                support = model.node_block(node)
                supports.append(support)
            else:
                block = model.node_block(node)
                blocks.append(block)

        name = 'support_geometry.dat'
        geometry_path = os.path.join(path, name)
        string = ';__create geometry__' + '\n'
        for i in range(len(supports)):
            # string += threedec_support_description_concave(supports[i], 2, i, precision=10)
            string += threedec7_support_description(supports[i], 2, i, precision=10)
        overwrite_file(geometry_path, string)

        name = 'block_geometry.dat'
        geometry_path = os.path.join(path, name)
        string = ';__create geometry__' + '\n'
        for i in range(len(blocks)):
            # string += threedec_block_description_concave(
            #     blocks[i], 1, (i + len(supports)), precision=10)
            string += threedec7_block_description(
                blocks[i], 1, (i + len(supports)), precision=10)
        overwrite_file(geometry_path, string)

        return





