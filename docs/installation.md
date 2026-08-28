# Installation

Stable releases can be installed from PyPI:

```bash
pip install compas_3dec
```

Install COMPAS DEM interoperability support with:

```bash
pip install "compas_3dec[dem]"
```

For local development, create the development environment and install the package:

```bash
conda env create -f environment.yml
conda activate compas-3dec-dev
```

Alternatively, install the cloned repository in editable mode:

```bash
pip install "compas_dem @ git+https://github.com/BlockResearchGroup/compas_dem.git@main"
pip install -e .
```

The proprietary 3DEC executable is not installed by this package. The solver
searches standard Itasca locations, or its path can be supplied explicitly.
