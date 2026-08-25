# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] 2026-08-20

### Added

* Added responsive hidden 3DEC execution with concise stage and load/displacement-step progress callbacks.
* Added configurable sequential stages, including optional grouping of compatible load boundary-condition groups.

### Changed

* Reduced COMPAS DEM result conversion size by making duplicated native 3DEC mechanics records opt-in.
* Improved Rhino result drawing and result-state handling for staged analyses.

### Removed
