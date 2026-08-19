from pathlib import Path

from compas_3dec import ThreeDECAnalysisBuilder
from compas_3dec import ThreeDECSolver
from compas_dem.templates import ArchTemplate


HERE = Path(__file__).parent
RUNS = HERE / "runs"


arch = ArchTemplate(
    rise=0.5,
    span=5.0,
    thickness=0.3,
    depth=0.3,
    n=10,
)

builder = ThreeDECAnalysisBuilder.from_meshes(
    arch.blocks(),
    name="Arch staged test",
)
builder.set_supports([0, 9])
builder.set_material(
    density=2500,
    young_modulus=25e9,
    poisson_ratio=0.2,
    name="Marble",
)
builder.set_contact_properties(
    kn=100e9,
    kt=70e9,
    friction=35.0,
)

# Gravity is always first. Later phases follow the order written below.
# Consecutive load calls are synchronized in one phase. To make the next
# boundary condition restore the preceding phase instead, insert:
# builder.start_new_phase()
builder.add_gravity(g=9.81, gravity_steps=10)

# Concentrated-load magnitudes are total forces in N.
builder.add_point_load(
    magnitude=1000,
    direction=[0, 0, -1],
    steps=10,
    point=[1.07, 0.30, 0.71],
    radius=0.02,
)
builder.add_point_load(
    magnitude=2000,
    direction=[0, 0, -1],
    steps=20,
    point=[1.60, 0.30, 0.60],
    radius=0.02,
)
builder.add_centroid_load(
    magnitude=3000,
    direction=[0, 0, -1],
    steps=10,
    blocks=[3],
)

# Surface load is traction in Pa (N/m2), not a total force.
builder.add_surface_load(
    block=8,
    face=4,
    load=[0, 0, -1000],
    steps=2,
)

# Displacement starts automatically from the completed load state.
builder.add_displacement(
    blocks=[9],
    magnitude=0.001,
    direction=[-1, 0, 0],
    steps=1,
)

# build() creates the portable ThreeDECAnalysis consumed by the solver.
analysis = builder.build()

solver = ThreeDECSolver(
    version="7.0",
    workspace=RUNS,
    suppress_output=False,
    timeout=None,
)
raw_results = solver.solve(analysis)
postprocessed = raw_results.postprocess(analysis)

print("Run ID:", raw_results.metadata.get("run_id"))
print("Blocks:", len(raw_results.blocks))
print("Gridpoints:", len(raw_results.gridpoints))
print("Contacts:", len(raw_results.contacts))
print("Converged:", raw_results.metadata.get("converged"))
print("Sliding contacts:", sum(contact["sliding"] for contact in postprocessed.contacts))
print("Cracked contacts:", sum(contact["cracked"] for contact in postprocessed.contacts))
