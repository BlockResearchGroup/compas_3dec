from compas_3dec.datastructures.input import Material, Input


def from_model(model):

    # convert model to input data-structure for 3DEC
    meshes = []
    is_support = []
    for element in model.elements():
        meshes.append(element.shape)
        is_support.append(element.is_support)
    
    materials = {}
    for material in model.materials():
        materials[material.name] = (Material(name=material.name, E=material.Ecm, poisson=material.poisson, rho=material.rho))

    compounds = []
    for indices in model.graph.connected_nodes():
        compounds.append(indices)

    # main input data-structure for 3DEC
    input = Input(
        meshes=meshes,
        is_support=is_support,
        compounds=compounds,
        materials=materials,
        contact_properties=None)

    print(input)
    return input
