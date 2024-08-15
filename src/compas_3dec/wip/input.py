class Material(object):
    @property
    def __data__(self):
        # type: () -> dict
        return {
            "name": self.name,
            "E": self.E,
            "poisson": self.poisson,
            "rho": self.rho,
            "group": self.group,
        }

    def __repr__(self):
        return (
            self.name
            + " E: "
            + str(self.E)
            + " poisson: "
            + str(self.poisson)
            + " rho: "
            + str(self.rho)
            + " group: "
            + str(self.group)
        )

    def __init__(
        self,
        name="",  # type: str
        E=None,  # type: float
        poisson=None,  # type: float
        rho=None,  # type: float
        group=None,  # type: str
    ):
        self.name = name
        self.E = E
        self.poisson = poisson
        self.rho = rho
        self.group = group

    @property
    def G(self):
        return self.E / (2 * (1 + self.poisson))


class Block(object):
    @property
    def __data__(self):
        # type: () -> dict
        return {
            "mesh": self.mesh,
            "is_support": self.is_support,
            "group": self.group,
        }

    def __init__(
        self,
        mesh=None,  # type: compas.datastructures.Mesh
        is_support=False,  # type: bool
        group=None,  # type: str
    ):
        self.mesh = mesh
        self.is_support = is_support
        self.group = group


class Input(object):
    """Input data for 3DEC analysis."""

    @property
    def __data__(self):
        # type: () -> dict
        return {
            "meshes": self.meshes,
            "is_support": self.is_support,
            "compounds": self.compounds,
            "materials": self.materials,
            "contact_properties": self.contact_properties,
        }

    def __init__(
        self,
        blocks=None,  # type: Block
        compounds=None,  # type: list[list[int]] | None
        materials=None,  # type: dict[Material] | None
    ):
        self.blocks = blocks
        self.compounds = compounds
        self.materials = materials
        self.is_valid()

    def has_valid_geometry(self):
        """Check if meshes are valid:
        a) meshes are welded
        b) meshes are closed
        c) meshes are valid

        this function will modify the input meshes"""

        copy_meshes = []
        for block in self.blocks:
            copy_meshes.append(block.mesh.copy())
            if block is None:
                raise Exception("Mesh not defined.")

        for mesh in copy_meshes:

            mesh.weld(3)

            if not mesh.is_closed():
                raise Exception("Mesh is not closed.")

            if not mesh.is_valid():
                raise Exception("Mesh is not valid.")

        for i, block in enumerate(self.blocks):
            block.mesh = copy_meshes[i]

    def has_supports(self):

        support_count = 0
        for block in self.blocks:
            if block.is_support:
                support_count += 1

        if support_count == 0:
            raise Exception("Supports not defined.")

    def has_compounds(self):
        if not self.compounds:
            print("Compounds not defined. By default each mesh is a compound.")

        self.compounds = [[i] for i in range(len(self.blocks))]

    def is_valid(self):
        """Check if input is valid. Validation is done in the individual functions."""
        self.has_valid_geometry()
        self.has_supports()
        self.has_compounds()

    def __repr__(self):

        len_blocks = 0
        len_supports = 0
        for block in self.blocks:
            if block.is_support:
                len_supports += 1
            else:
                len_blocks += 1

        message = "=" * 80 + "\n"
        message += "Number of blocks:\n"
        message += str(len(self.blocks)) + "\n"
        message += "=" * 80 + "\n"
        message += "Type of elements:\n"
        number_of_supports = 0
        message += "number of blocks: " + str(len_blocks) + ", number of supports: " + str(number_of_supports) + "\n"
        message += "=" * 80 + "\n"
        message += "Materials:\n"
        message += str(self.materials) + "\n"
        if not self.materials:
            message += "WARNING: Materials not defined.\n"
        message += "=" * 80 + "\n"
        message += "Compounds:\n"
        message += str(self.compounds) + "\n"
        message += "=" * 80 + "\n"
        return message
