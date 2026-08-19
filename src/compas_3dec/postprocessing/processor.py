class ThreeDECPostProcessor:
    """Coordinate selective postprocessing of native 3DEC results.

    Parameters
    ----------
    analysis : :class:`compas_3dec.analysis.ThreeDECAnalysis`
        Prepared analysis associated with the result records.
    raw_results : :class:`compas_3dec.solver.ThreeDECRawResults`
        Native records exported by 3DEC.
    """

    def __init__(self, analysis, raw_results):
        self.analysis = analysis
        self.raw_results = raw_results

    def process(self, components=None, **options):
        """Compute the requested postprocessing components."""
        from .mechanics import postprocess_raw_results

        return postprocess_raw_results(self.analysis, self.raw_results, components=components, **options)

    def blocks(self):
        """Compute updated rigid-block transformations only."""
        return self.process(components=("blocks",))

    def contacts(self):
        """Compute canonical contact mechanics only."""
        return self.process(components=("contacts",))

    def failure(self, **options):
        """Compute contact mechanics and failure-state indicators."""
        return self.process(components=("contacts", "failure"), **options)

    def to_compas_dem_results(self):
        """Create the limited result contract consumed by COMPAS DEM."""
        from .compas_dem import create_compas_dem_results

        return create_compas_dem_results(self.analysis, self.raw_results)
