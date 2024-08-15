from compas_3dec.datastructures.input import Material, Input, Block


def from_model(model):

    # convert model to input data-structure for 3DEC
    blocks = []
    for element in model.elements():
        blocks.append(Block(element.shape, element.is_support))

    materials = {}
    for material in model.materials():
        materials[material.name] = Material(
            name=material.name, E=material.Ecm, poisson=material.poisson, rho=material.rho
        )

    compounds = []
    for indices in model.graph.connected_nodes():
        compounds.append(indices)

    # main input data-structure for 3DEC
    input = Input(blocks=blocks, compounds=compounds, materials=materials)

    print(input)
    return input
