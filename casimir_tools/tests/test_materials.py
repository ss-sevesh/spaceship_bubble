"""
tests/test_materials.py — pytest suite for casimir_tools._materials.

Tests the material database completeness and consistency.
"""

import pytest
from casimir_tools._materials import MATERIALS, load_material


REQUIRED_KEYS = {"formula", "eps_static", "n", "eps_perp", "eps_par", "2osc", "notes"}
OSC_KEYS      = {"C1", "omega1", "C2", "omega2"}


class TestMaterialDatabase:
    """MATERIALS dict structure and physical consistency."""

    def test_all_expected_materials_present(self):
        for name in ["Te", "WTe2_hex", "WTe2_Td", "Au", "Si"]:
            assert name in MATERIALS

    @pytest.mark.parametrize("name", ["Te", "WTe2_hex", "WTe2_Td", "Si"])
    def test_required_keys_present(self, name):
        mat = MATERIALS[name]
        for k in REQUIRED_KEYS:
            assert k in mat, f"{name} missing key {k}"

    @pytest.mark.parametrize("name", ["Te", "WTe2_hex", "WTe2_Td", "Si"])
    def test_2osc_params_sum_to_eps_static(self, name):
        """1 + C1 + C2 should match eps_static within 5%."""
        mat  = MATERIALS[name]
        osc  = mat["2osc"]
        eps0 = 1.0 + osc["C1"] + osc["C2"]
        assert eps0 == pytest.approx(mat["eps_static"], rel=0.05)

    @pytest.mark.parametrize("name", ["Te", "WTe2_hex", "WTe2_Td", "Si"])
    def test_eps_static_positive(self, name):
        assert MATERIALS[name]["eps_static"] > 1.0

    @pytest.mark.parametrize("name", ["Te", "WTe2_hex", "WTe2_Td", "Si"])
    def test_2osc_frequencies_ordered(self, name):
        """IR pole omega1 should be << UV pole omega2."""
        osc = MATERIALS[name]["2osc"]
        assert osc["omega1"] < osc["omega2"]

    @pytest.mark.parametrize("name", ["Te", "WTe2_hex", "WTe2_Td", "Si"])
    def test_2osc_strengths_positive(self, name):
        osc = MATERIALS[name]["2osc"]
        assert osc["C1"] >= 0.0
        assert osc["C2"] >= 0.0

    def test_te_eps_electronic_consistent_with_n(self):
        """For Te: eps_electronic ≈ n². 2-osc C2 ≈ n² - 1."""
        te   = MATERIALS["Te"]
        n    = te["n"]
        C2   = te["2osc"]["C2"]
        eps_elec_from_n  = n ** 2
        eps_elec_from_C2 = 1.0 + C2
        assert eps_elec_from_C2 == pytest.approx(eps_elec_from_n, rel=0.05)


class TestLoadMaterial:
    """load_material helper function."""

    def test_load_te(self):
        mat = load_material("Te")
        assert mat["formula"] == "Te"
        assert mat["eps_static"] == pytest.approx(164.27, abs=0.1)

    def test_load_wte2_hex(self):
        mat = load_material("WTe2_hex")
        assert mat["eps_static"] == pytest.approx(6.16, abs=0.1)

    def test_load_wte2_td(self):
        mat = load_material("WTe2_Td")
        assert mat["spacegroup"] == "Pmn2_1"

    def test_load_unknown_raises_key_error(self):
        with pytest.raises(KeyError, match="Unknown material"):
            load_material("Unobtainium")

    def test_load_si(self):
        mat = load_material("Si")
        assert mat["eps_static"] == pytest.approx(11.9, abs=0.1)
