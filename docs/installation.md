# Installation

Create the development environment and install the package:

```bash
conda env create -f environment.yml
conda activate compas-3dec-dev
```

For a minimal installation:

```bash
pip install -e .
```

The proprietary 3DEC executable is not installed by this package. The solver
searches standard Itasca locations, or its path can be supplied explicitly.
