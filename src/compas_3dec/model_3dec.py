from compas_model.model import Model
from compas_model.elements import BlockElement, InterfaceElement

class Model_3dec(Model):
    """Class representing a general model of hierarchically organised elements, with interactions.

    Attributes
    ----------
    elements : dict
        The elements of the model mapped by their guid.
    tree : :class:`ElementTree`
        A hierarchical structure of the elements in the model.
    graph : :class:`InteractionGraph`
        A graph containing the interactions between the elements of the model on its edges.

    Notes
    -----
    Model elements are contained in the tree hierarchy in tree nodes.
    Model elements are contained in the interaction graph in graph nodes.
    Every model element can appear only once in the tree, and once in the graph.
    This means every element can have only one hierarchical parent.
    Every element can have many interactions with other elements.
    The interactions and hierarchical relations are independent.

    """

    def __init__(self, name=None):
        super(Model_3dec, self).__init__(name)

