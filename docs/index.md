# COMPAS 3DEC

`compas_3dec` provides a direct COMPAS interface for preparing, running, and
post-processing rigid-block analyses with Itasca 3DEC.

```python
from compas_3dec import ThreeDECAnalysisBuilder, ThreeDECSolver
```

An analysis can be built directly from meshes or translated from a
`compas_dem` problem. Both routes produce the same portable analysis object.
