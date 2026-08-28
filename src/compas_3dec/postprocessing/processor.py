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
        """Compute the requested post-processing components.

        Parameters
        ----------
        components : sequence[str], optional
            Any of ``"blocks"``, ``"contacts"``, or ``"failure"``.
            All components are computed by default.
        **options : dict, optional
            Mechanics and failure thresholds.

        Returns
        -------
        :class:`ThreeDECPostProcessedResults`
            Selected derived mechanics.
        """
        from .mechanics import postprocess_raw_results

        return postprocess_raw_results(self.analysis, self.raw_results, components=components, **options)

    def blocks(self):
        """Compute updated rigid-block transformations only.

        Returns
        -------
        :class:`ThreeDECPostProcessedResults`
            Block transformations without contact mechanics.
        """
        return self.process(components=("blocks",))

    def contacts(self):
        """Compute canonical contact mechanics only.

        Returns
        -------
        :class:`ThreeDECPostProcessedResults`
            Contact mechanics without failure indicators.
        """
        return self.process(components=("contacts",))

    def failure(self, **options):
        """Compute contact mechanics and failure-state indicators.

        Parameters
        ----------
        **options : dict, optional
            Mechanics and failure thresholds.

        Returns
        -------
        :class:`ThreeDECPostProcessedResults`
            Contact mechanics with opening, sliding, and hinge indicators.
        """
        return self.process(components=("contacts", "failure"), **options)

    def to_compas_dem_results(self, include_native=False):
        """Create the compact result contract consumed by COMPAS DEM.

        Parameters
        ----------
        include_native : bool, optional
            Include duplicated native diagnostic records. Default is ``False``.

        Returns
        -------
        :class:`compas_dem.problem.Results`
            Compact solver-independent result contract.
        """
        from .compas_dem import create_compas_dem_results

        return create_compas_dem_results(self.analysis, self.raw_results, include_native=include_native)
