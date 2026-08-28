# Contributing

Contributions are welcome and very much appreciated!

## Code contributions

We accept code contributions through pull requests.
In short, this is how that works.

1. Fork [the repository](https://github.com/BlockResearchGroup/compas_3dec) and clone the fork.
2. Create a virtual environment using your tool of choice (e.g. `virtualenv`, `conda`, etc).
3. Install development dependencies:

   ```bash
   pip install "compas_dem @ git+https://github.com/BlockResearchGroup/compas_dem.git@main"
   pip install -e ".[dev,docs]"
   ```

4. Make sure all tests pass:

   ```bash
   python -m pytest
   ```

5. Create a feature branch from the **main** branch and make your changes.
6. Make sure all tests still pass:

   ```bash
   python -m ruff check .
   python -m ruff format --check .
   python -m pytest
   ```

   The real external integration smoke tests are skipped by default because
   they launch a licensed local 3DEC executable. To run the complete
   `COMPAS DEM -> compas_3dec` and headless `COMPAS-Masonry -> COMPAS DEM ->
   compas_3dec` checks on Windows Command Prompt, use:

   ```bat
   set "COMPAS_3DEC_EXECUTABLE=C:\Program Files\Itasca\3DEC700\exe64\3dec700_console.exe"
   set "COMPAS_3DEC_VERSION=7.0"
   python -m pytest tests/test_external_integrations.py -s
   ```

   The masonry test is skipped when `compas_masonry` is not installed. It
   verifies the headless solve and session result round-trip; Rhino drawing is
   intentionally checked separately in Rhino.

7. Add yourself to the *Contributors* section of `AUTHORS.md`.
8. Commit your changes and push your branch to GitHub.
9. Create a [pull request](https://help.github.com/articles/about-pull-requests/) through the GitHub website.

During development, use [pyinvoke](http://docs.pyinvoke.org/) tasks on the
command line to ease recurring operations:

* `invoke clean`: Clean all generated artifacts.
* `invoke check`: Run various code and documentation style checks.
* `invoke docs`: Generate documentation.
* `invoke test`: Run all tests and checks in one swift command.
* `invoke`: Show available tasks.

## Bug reports

When [reporting a bug](https://github.com/BlockResearchGroup/compas_3dec/issues) please include:

* Operating system name and version.
* Any details about your local setup that might be helpful in troubleshooting.
* Detailed steps to reproduce the bug.

## Feature requests

When [proposing a new feature](https://github.com/BlockResearchGroup/compas_3dec/issues) please include:

* Explain in detail how it would work.
* Keep the scope as narrow as possible, to make it easier to implement.
