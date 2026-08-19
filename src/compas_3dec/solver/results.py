from compas.data import Data


class ThreeDECRawResults(Data):
    """Serializable native records produced directly by 3DEC."""

    CURRENT_SCHEMA_VERSION = 2

    def __init__(
        self,
        blocks=None,
        gridpoints=None,
        contacts=None,
        metadata=None,
        schema_version=None,
        name=None,
    ):
        super().__init__(name=name)
        self.schema_version = schema_version or self.CURRENT_SCHEMA_VERSION
        self.blocks = list(blocks or [])
        self.gridpoints = list(gridpoints or [])
        self.contacts = list(contacts or [])
        self.metadata = dict(metadata or {})

    @property
    def __data__(self):
        return {
            "name": self.name,
            "schema_version": self.schema_version,
            "blocks": self.blocks,
            "gridpoints": self.gridpoints,
            "contacts": self.contacts,
            "metadata": self.metadata,
        }

    @classmethod
    def __from_data__(cls, data):
        return cls(
            name=data.get("name"),
            schema_version=data.get("schema_version", 1),
            blocks=data.get("blocks", []),
            gridpoints=data.get("gridpoints", []),
            contacts=data.get("contacts", []),
            metadata=data.get("metadata", {}),
        )

    def to_compas_dem_results(self, analysis):
        """Convert these records to the limited ``compas_dem.Results`` contract."""
        from compas_3dec.postprocessing import ThreeDECPostProcessor

        return ThreeDECPostProcessor(analysis, self).to_compas_dem_results()

    def postprocess(self, analysis, **kwargs):
        """Derive selected mechanics from these native records."""
        from compas_3dec.postprocessing import ThreeDECPostProcessor

        return ThreeDECPostProcessor(analysis, self).process(**kwargs)

    def postprocess_blocks(self, analysis):
        """Compute only updated rigid-block transformations."""
        return self.postprocess(analysis, components=("blocks",))

    def postprocess_contacts(self, analysis):
        """Compute canonical contact forces, resultants, and application points."""
        return self.postprocess(analysis, components=("contacts",))

    def postprocess_failure(self, analysis, **kwargs):
        """Compute contact mechanics and failure-state indicators."""
        return self.postprocess(analysis, components=("contacts", "failure"), **kwargs)
