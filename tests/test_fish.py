import pytest

from compas_3dec.solver import ThreeDECFish7
from compas_3dec.solver import ThreeDECFish9
from compas_3dec.solver import fish_dialect


@pytest.mark.parametrize(
    ("version", "dialect_type"),
    [
        ("7.0", ThreeDECFish7),
        ("9.0", ThreeDECFish9),
        ("9.5", ThreeDECFish9),
    ],
)
def test_version_selects_fish_dialect_once(version, dialect_type):
    assert isinstance(fish_dialect(version), dialect_type)


def test_fish_output_uses_solver_ids_instead_of_pointer_strings():
    text = fish_dialect("9.0").definitions()

    assert "block.gp.id(gp)" in text
    assert "block.contact.id(contact)" in text
    assert "block.subcontact.id(subcontact)" in text
    assert "block.gp.next" not in text
    assert "block.contact.next" not in text
    assert "block.subcontact.next" not in text
    assert "block.subcontact.stress.shear(subcontact)->" not in text


def test_fish_output_schema_records_scalar_shear_stress():
    dialect = fish_dialect("7.0")

    assert dialect.output_schema == 3
    assert "block.subcontact.stress.shear(subcontact)" in dialect.definitions()
    assert "block.subcontact.state(subcontact)" in dialect.definitions()


def test_unsupported_major_version_is_rejected():
    with pytest.raises(ValueError, match="Supported versions are 7 and 9"):
        fish_dialect("8.0")
