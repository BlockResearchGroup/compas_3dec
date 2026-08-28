# compas_3dec

`compas_3dec` is a COMPAS integration for preparing, running, and
post-processing rigid-block analyses with 3DEC by Itasca Consulting Group.

## Installation

```bash
pip install compas_3dec
```

Install COMPAS DEM interoperability support with:

```bash
pip install "compas_3dec[dem]"
```

For local development, clone the repository and install the development and
documentation dependencies with:

```bash
pip install "compas_dem @ git+https://github.com/BlockResearchGroup/compas_dem.git@main"
pip install -e ".[dev,docs]"
```

The 3DEC executable is proprietary and must be installed separately.

## Usage

```python
from compas_3dec import ThreeDECAnalysisBuilder, ThreeDECSolver

builder = ThreeDECAnalysisBuilder.from_meshes(meshes, name="Arch gravity")
builder.set_material(density=2500, young_modulus=25e9, poisson_ratio=0.2)
builder.set_supports([0, 9])
builder.set_contact_properties()
builder.add_gravity()

analysis = builder.build()
results = ThreeDECSolver(workspace=r"C:\path\to\runs").solve(analysis)
```

Inputs can also be translated from a `compas_dem` problem with
`ThreeDECAnalysisBuilder.from_dem_problem`.

Native results can be processed selectively or converted to the limited
`compas_dem.Results` contract:

```python
contacts = results.postprocess_contacts(analysis)
failure = results.postprocess_failure(analysis)
dem_results = results.to_compas_dem_results(analysis)
```

## Development

```bash
pytest
ruff check .
ruff format .
mkdocs serve
```

Automated tests live in `tests/`. Executable analysis and visualisation
scripts live in `scripts/`. Generated solver runs should be stored outside the
repository or in an ignored `runs/` directory.
