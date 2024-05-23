






class Material(object):

    @property
    def __data__(self):
        # type: () -> dict
        return {
            "name": self.name,
            "E": self.E,
            "poisson": self.poisson,
            "rho": self.rho,
        }
    
    def __repr__(self):
        return self.name + " E: " + str(self.E) + " poisson: " + str(self.poisson) + " rho: " + str(self.rho)

    def __init__(self,
                 name="",  # type: str
                 E=None,   # type: float
                 poisson=None,   # type: float
                 rho=None,  # type: float
                 ):
        self.name = name
        self.E = E
        self.poisson = poisson
        self.rho = rho

    @property
    def G(self):
        return self.E / (2 * (1 + self.poisson))

class Input(object):
    """ Input data for 3DEC analysis."""

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

    def __init__(self,
                 meshes=None,  # type: compas.datastructures.Mesh | None
                 is_support=None,  # type: list[bool] | None
                 compounds=None,  # type: list[list[int]] | None
                 materials=None,  # type: dict[Material] | None
                 contact_properties=None,  # type: list[Contact_Property] | None
                 ):
        self.meshes = meshes
        self.is_support = is_support
        self.compounds = compounds
        self.materials = materials
        self.is_valid()

    def has_valid_geometry(self, meshes):
        """Check if meshes are valid:
        a) meshes are welded
        b) meshes are closed
        c) meshes are valid

        this function will modify the input meshes"""

        copy_meshes = []
        for mesh in meshes:
            copy_meshes.append(mesh.copy())

        if not meshes:
            raise Exception("Meshes not defined.")

        for mesh in copy_meshes:

            mesh.weld(3)

            if not mesh.is_closed():
                raise Exception("Mesh is not closed.")

            if not mesh.is_valid():
                raise Exception("Mesh is not valid.")

        self.meshes = copy_meshes

    def has_supports(self):

        if not self.is_support:
            from colorama import Fore, Style
            print(Fore.RED + "Supports not defined." + Style.RESET_ALL)

        support_count = 0
        for is_support in self.is_support:
            if is_support:
                support_count += 1

        if support_count == 0:
            raise Exception("Supports not defined.")

    def has_compounds(self):
        if not self.compounds:
            raise Exception("Compounds not defined. By default each mesh is a compound.")

        self.compounds = [[i] for i in range(len(self.meshes))]

    def is_valid(self):
        """ Check if input is valid. Validation is done in the individual functions."""
        self.has_valid_geometry(self.meshes)
        self.has_supports()
        self.has_compounds()

    def __repr__(self):

        len_blocks = 0
        len_supports = 0
        for flag in self.is_support:
            if flag:
                len_supports += 1
            else:
                len_blocks += 1

        message = "=" * 80 + "\n"
        message += "Number of meshes:\n"
        message += str(len(self.meshes)) + "\n"
        message += "=" * 80 + "\n"
        message += "Type of elements:\n"
        message += "number of blocks: " + str(len_blocks) + ", number of supports: " + str(len_supports) + "\n"
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


