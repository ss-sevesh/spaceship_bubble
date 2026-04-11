"""
test_lifshitz.py — Physics validation tests for the Lifshitz-Casimir calculator.

Tests are self-consistency checks and limit verifications that are robust to
material parameter choices.  No absolute value benchmarks are used unless the
formula and parameters are fully pinned.

Run with:
    uv run pytest tests/test_lifshitz.py -v
"""

import numpy as np
import pytest

from lifshitz import (
    HBAR, C, OMEGA_UV,
    epsilon_imaginary,
    epsilon_imaginary_2osc,
    epsilon_imaginary_drude_lorentz,
    casimir_energy,
    casimir_energy_aniso,
    casimir_energy_chiral,
    casimir_energy_chiral_asymmetric,
    casimir_energy_finite_T,
    casimir_energy_fast,
    casimir_energy_2osc,
    casimir_force,
    _hamaker_constant,
    _reflection_te,
    _reflection_tm,
    TE_2OSC, WTE2_2OSC,
)


# ── Representative material parameters ───────────────────────────────────────
EPS_TE   = 164.27   # Te static dielectric (mp-19, trace average)
EPS_WTE2 = 6.16     # WTe2 static dielectric (mp-1023926)
EPS_SIO2 = 3.9      # SiO2 (reference insulator)
EPS_AU   = 1.0e6    # Gold limit: very large eps -> beta -> 1


# ─────────────────────────────────────────────────────────────────────────────
# 1. Dielectric models
# ─────────────────────────────────────────────────────────────────────────────

class TestDielectricModels:
    def test_cauchy_static_limit(self):
        """eps(xi=0) == eps_static."""
        assert epsilon_imaginary(EPS_TE, 0.0) == pytest.approx(EPS_TE, rel=1e-10)

    def test_cauchy_high_freq_limit(self):
        """eps(xi >> omega_UV) -> 1 (vacuum limit)."""
        xi_large = 1e20   # rad/s, >> OMEGA_UV ~ 2e16
        eps = epsilon_imaginary(EPS_TE, xi_large)
        assert eps == pytest.approx(1.0, abs=1e-3)

    def test_cauchy_monotonic_decay(self):
        """eps(i*xi) must be monotonically decreasing in xi (Kramers-Kronig)."""
        xi_arr = np.logspace(10, 20, 30)
        eps_arr = np.array([epsilon_imaginary(EPS_TE, xi) for xi in xi_arr])
        assert np.all(np.diff(eps_arr) < 0), "eps(i*xi) must decrease with xi"

    def test_2osc_static_sum(self):
        """eps(0) == 1 + C1 + C2 for both Te and WTe2."""
        te = TE_2OSC
        eps0_te = epsilon_imaginary_2osc(te["C1"], te["omega1"], te["C2"], te["omega2"], 0.0)
        assert eps0_te == pytest.approx(1 + te["C1"] + te["C2"], rel=1e-10)

        wte2 = WTE2_2OSC
        eps0_wte2 = epsilon_imaginary_2osc(wte2["C1"], wte2["omega1"], wte2["C2"], wte2["omega2"], 0.0)
        assert eps0_wte2 == pytest.approx(1 + wte2["C1"] + wte2["C2"], rel=1e-10)

    def test_2osc_te_eps_static_value(self):
        """Te 2-oscillator eps(0) matches Materials Project value 164.27."""
        te = TE_2OSC
        eps0 = epsilon_imaginary_2osc(te["C1"], te["omega1"], te["C2"], te["omega2"], 0.0)
        assert eps0 == pytest.approx(164.27, abs=0.01)

    def test_2osc_high_freq(self):
        """eps(i*xi_large) -> 1 for both oscillators."""
        te = TE_2OSC
        eps_large = epsilon_imaginary_2osc(te["C1"], te["omega1"], te["C2"], te["omega2"], 1e22)
        assert eps_large == pytest.approx(1.0, abs=1e-3)

    def test_drude_lorentz_zero_pole(self):
        """Drude+Lorentz regularises xi=0 without crashing."""
        eps = epsilon_imaginary_drude_lorentz(0.0, omega_p=1e15, gamma=5e13,
                                               eps_inf=13.63, omega_uv=OMEGA_UV)
        assert np.isfinite(eps)
        assert eps > 1.0


# ─────────────────────────────────────────────────────────────────────────────
# 2. Fresnel reflection coefficients
# ─────────────────────────────────────────────────────────────────────────────

class TestFresnelCoefficients:
    def test_te_sign_for_eps_gt_1(self):
        """r^TE < 0 for eps > 1 (standard dielectrics)."""
        for eps in [2.0, 5.0, 50.0, 164.0]:
            r = _reflection_te(eps, p=1.0)
            assert r < 0, f"r^TE should be negative for eps={eps}"

    def test_tm_sign_for_eps_gt_1(self):
        """r^TM > 0 for eps > 1."""
        for eps in [2.0, 5.0, 50.0, 164.0]:
            r = _reflection_tm(eps, p=1.0)
            assert r > 0, f"r^TM should be positive for eps={eps}"

    def test_te_vacuum_limit(self):
        """r^TE(eps=1) = 0 (no reflection at vacuum-vacuum interface)."""
        r = _reflection_te(1.0, p=1.5)
        assert r == pytest.approx(0.0, abs=1e-12)

    def test_tm_vacuum_limit(self):
        """r^TM(eps=1) = 0."""
        r = _reflection_tm(1.0, p=1.5)
        assert r == pytest.approx(0.0, abs=1e-12)

    def test_reflection_bounds(self):
        """|r| <= 1 for all physical parameters."""
        for eps in [1.5, 10.0, 100.0]:
            for p in [1.0, 2.0, 5.0]:
                assert abs(_reflection_te(eps, p)) <= 1.0
                assert abs(_reflection_tm(eps, p)) <= 1.0


# ─────────────────────────────────────────────────────────────────────────────
# 3. Casimir energy — sign and ordering
# ─────────────────────────────────────────────────────────────────────────────

class TestCasimirEnergySign:
    @pytest.mark.parametrize("d_nm", [5.0, 10.0, 50.0])
    def test_energy_is_negative(self, d_nm):
        """Casimir energy between two dielectrics (eps > 1) must be attractive (< 0)."""
        E = casimir_energy(EPS_TE, EPS_WTE2, d_nm * 1e-9)
        assert E < 0, f"E should be negative (attractive) at d={d_nm} nm, got {E}"

    @pytest.mark.parametrize("d_nm", [5.0, 10.0, 50.0])
    def test_force_is_negative(self, d_nm):
        """Casimir force between two dielectrics must be attractive (F < 0)."""
        F = casimir_force(EPS_TE, EPS_WTE2, d_nm * 1e-9)
        assert F < 0, f"F should be negative (attractive) at d={d_nm} nm, got {F}"

    def test_energy_monotonic_with_separation(self):
        """|E| must decrease as d increases (energy weakens with separation)."""
        ds = [5e-9, 10e-9, 20e-9, 50e-9]
        Es = [casimir_energy(EPS_TE, EPS_WTE2, d) for d in ds]
        for i in range(len(Es) - 1):
            assert Es[i] < Es[i + 1], (
                f"|E(d_small)| should be larger: E[{i}]={Es[i]:.3e} vs E[{i+1}]={Es[i+1]:.3e}")

    def test_symmetric_config_stronger(self):
        """E(Te|Te) should have larger |E| than E(Te|WTe2) at same d (higher eps1=eps2)."""
        d = 20e-9
        E_sym  = casimir_energy(EPS_TE, EPS_TE, d)
        E_asym = casimir_energy(EPS_TE, EPS_WTE2, d)
        assert abs(E_sym) > abs(E_asym), "Te|Te should have stronger Casimir energy than Te|WTe2"


# ─────────────────────────────────────────────────────────────────────────────
# 4. Self-consistency: F = -dE/dd (numerical derivative check)
# ─────────────────────────────────────────────────────────────────────────────

class TestForceSelfConsistency:
    @pytest.mark.parametrize("d_nm", [10.0, 30.0, 80.0])
    def test_force_equals_minus_denergy_dd(self, d_nm):
        """F(d) ≈ -(E(d+δ) - E(d-δ)) / (2δ) — central-difference self-consistency."""
        d = d_nm * 1e-9
        delta = d * 0.002   # 0.2% step
        E_plus  = casimir_energy(EPS_TE, EPS_WTE2, d + delta)
        E_minus = casimir_energy(EPS_TE, EPS_WTE2, d - delta)
        F_numerical = -(E_plus - E_minus) / (2.0 * delta)
        F_analytic  = casimir_force(EPS_TE, EPS_WTE2, d)
        # Allow 1% relative tolerance (quadrature + finite-difference error)
        assert F_analytic == pytest.approx(F_numerical, rel=0.01), (
            f"At d={d_nm} nm: F_analytic={F_analytic:.4e}, F_numerical={F_numerical:.4e}")


# ─────────────────────────────────────────────────────────────────────────────
# 5. Anisotropic limit: isotropic recovery
# ─────────────────────────────────────────────────────────────────────────────

class TestAnisotropicLimit:
    @pytest.mark.parametrize("eps,d_nm", [(EPS_TE, 10.0), (EPS_WTE2, 25.0)])
    def test_isotropic_recovery(self, eps, d_nm):
        """casimir_energy_aniso(eps, eps, eps, eps, d) == casimir_energy(eps, eps, d)."""
        d = d_nm * 1e-9
        E_iso   = casimir_energy(eps, eps, d)
        E_aniso = casimir_energy_aniso(eps, eps, eps, eps, d)
        assert E_aniso == pytest.approx(E_iso, rel=0.005), (
            f"Anisotropic formula should recover isotropic at eps={eps}, d={d_nm} nm. "
            f"Got E_iso={E_iso:.4e}, E_aniso={E_aniso:.4e}")


# ─────────────────────────────────────────────────────────────────────────────
# 6. Chiral correction
# ─────────────────────────────────────────────────────────────────────────────

class TestChiralCorrection:
    def test_kappa0_returns_standard(self):
        """casimir_energy_chiral(kappa=0) == casimir_energy."""
        d = 20e-9
        E_std    = casimir_energy(EPS_TE, EPS_WTE2, d)
        E_chiral = casimir_energy_chiral(EPS_TE, EPS_WTE2, d, kappa=0.0)
        assert E_chiral == pytest.approx(E_std, rel=1e-10)

    def test_chirality_reduces_attraction(self):
        """Increasing kappa must reduce |E| (move toward zero or repulsion)."""
        d = 10e-9
        E0   = casimir_energy_chiral(EPS_TE, EPS_TE, d, kappa=0.0)
        E05  = casimir_energy_chiral(EPS_TE, EPS_TE, d, kappa=0.5)
        E10  = casimir_energy_chiral(EPS_TE, EPS_TE, d, kappa=1.0)
        assert abs(E05) < abs(E0),  "kappa=0.5 should reduce |E| vs kappa=0"
        assert abs(E10) < abs(E05), "kappa=1.0 should reduce |E| further"

    def test_fast_model_kappa0_matches_hamaker(self):
        """casimir_energy_fast(kappa=0) == -A / (12π d²)."""
        d = 20e-9
        from lifshitz import _hamaker_constant
        A = _hamaker_constant(EPS_TE, EPS_WTE2)
        E_hamaker = -A / (12.0 * np.pi * d ** 2)
        E_fast    = casimir_energy_fast(EPS_TE, EPS_WTE2, d, kappa=0.0)
        assert E_fast == pytest.approx(E_hamaker, rel=1e-10)


# ─────────────────────────────────────────────────────────────────────────────
# 7. Finite-temperature Matsubara summation
# ─────────────────────────────────────────────────────────────────────────────

class TestFiniteTemperature:
    def test_finite_T_negative(self):
        """Finite-T energy must be negative (attractive) for standard dielectrics."""
        E = casimir_energy_finite_T(EPS_TE, EPS_WTE2, 20e-9, T=300.0)
        assert E < 0

    def test_small_thermal_correction_at_d_much_less_than_lT(self):
        """At d << l_T (1.2 µm at 300 K), thermal correction must be < 5%."""
        d = 10e-9   # 10 nm << l_T ≈ 1.2 µm at 300 K  (d/l_T ≈ 0.008)
        E_T0   = casimir_energy(EPS_TE, EPS_WTE2, d)
        E_T300 = casimir_energy_finite_T(EPS_TE, EPS_WTE2, d, T=300.0, n_max=800)
        # Fractional thermal correction at d=10nm should be tiny
        frac_correction = abs(E_T300 - E_T0) / abs(E_T0)
        assert frac_correction < 0.05, (
            f"Thermal correction at d=10nm should be <5% of T=0 result. "
            f"Got {frac_correction*100:.2f}%: E_T0={E_T0:.4e}, E_T300={E_T300:.4e}")

    def test_finite_T_monotonic_d(self):
        """|E_T(d)| must decrease as d increases at finite T."""
        ds = [5e-9, 15e-9, 50e-9]
        Es = [casimir_energy_finite_T(EPS_TE, EPS_WTE2, d, T=300.0, n_max=100) for d in ds]
        for i in range(len(Es) - 1):
            assert Es[i] < Es[i + 1], (
                f"|E_T(d_small)| should exceed |E_T(d_large)|: "
                f"E[{i}]={Es[i]:.3e} vs E[{i+1}]={Es[i+1]:.3e}")

    def test_thermal_correction_adds_at_large_d(self):
        """At d >> l_T (1.2 µm at 300K), |E_T| > |E_T0| (thermal enhancement)."""
        d_large = 5e-6   # 5 µm >> l_T
        E_T300 = casimir_energy_finite_T(EPS_TE, EPS_WTE2, d_large, T=300.0, n_max=20)
        E_T0   = casimir_energy(EPS_TE, EPS_WTE2, d_large)
        assert abs(E_T300) > abs(E_T0), (
            "At d >> l_T, finite-T energy should exceed T=0 (classical enhancement)")


# ─────────────────────────────────────────────────────────────────────────────
# 8. Prefactor correctness — SI unit check
# ─────────────────────────────────────────────────────────────────────────────

class TestPrefactorSI:
    def test_prefactor_value(self):
        """Check HBAR/(4π²c²) value in SI units."""
        expected = HBAR / (4.0 * np.pi ** 2 * C ** 2)
        assert expected == pytest.approx(2.970e-51, rel=0.01), (
            f"Prefactor ħ/(4π²c²) = {expected:.4e} J·s³/m², expected ~2.97e-51")

    def test_energy_order_of_magnitude(self):
        """At d=10 nm, Te|WTe2 energy should be O(10^-3 J/m²) — MEMS-relevant."""
        E = casimir_energy(EPS_TE, EPS_WTE2, 10e-9)
        assert 1e-5 < abs(E) < 1.0, (
            f"E at d=10nm should be in [1e-5, 1] J/m², got {abs(E):.3e}")

    def test_hamaker_constant_te_wte2(self):
        """Hamaker constant for Te|WTe2 should be O(1e-19 J)."""
        A = _hamaker_constant(EPS_TE, EPS_WTE2)
        assert 1e-21 < A < 1e-17, f"Hamaker A={A:.3e} J out of expected range"


# ─────────────────────────────────────────────────────────────────────────────
# 9. 2-oscillator vs single-oscillator: sign and ordering
# ─────────────────────────────────────────────────────────────────────────────

class TestTwoOscillatorModel:
    @pytest.mark.parametrize("d_nm", [10.0, 30.0])
    def test_2osc_energy_negative(self, d_nm):
        """2-oscillator Casimir energy must be attractive."""
        te = TE_2OSC; wte2 = WTE2_2OSC
        E = casimir_energy_2osc(
            te["C1"], te["omega1"], te["C2"], te["omega2"],
            wte2["C1"], wte2["omega1"], wte2["C2"], wte2["omega2"],
            d_nm * 1e-9)
        assert E < 0, f"E_2osc at d={d_nm}nm should be negative"

    def test_2osc_vs_1osc_same_sign(self):
        """Both models should give the same sign (attractive)."""
        d = 20e-9
        te = TE_2OSC; wte2 = WTE2_2OSC
        E_2osc = casimir_energy_2osc(
            te["C1"], te["omega1"], te["C2"], te["omega2"],
            wte2["C1"], wte2["omega1"], wte2["C2"], wte2["omega2"], d)
        E_1osc = casimir_energy(EPS_TE, EPS_WTE2, d)
        assert np.sign(E_2osc) == np.sign(E_1osc)


# ─────────────────────────────────────────────────────────────────────────────
# 10. Asymmetric chiral correction (Silveirinha 2010) — Te|WTe2 heterostructure
# ─────────────────────────────────────────────────────────────────────────────

class TestAsymmetricChiralCorrection:
    """casimir_energy_chiral_asymmetric — Te chiral, WTe2 non-chiral."""

    def test_kappa0_returns_standard(self):
        """At kappa=0, asymmetric chiral energy == standard Lifshitz."""
        d = 20e-9
        E_std  = casimir_energy(EPS_TE, EPS_WTE2, d)
        E_asym = casimir_energy_chiral_asymmetric(EPS_TE, EPS_WTE2, d, kappa=0.0)
        assert E_asym == pytest.approx(E_std, rel=1e-10)

    def test_te_wte2_stays_attractive_at_kappa1(self):
        """Te|WTe2 must remain attractive at kappa=1.0 (kappa_crit_asym ≈ 6.3)."""
        E = casimir_energy_chiral_asymmetric(EPS_TE, EPS_WTE2, 20e-9, kappa=1.0)
        assert E < 0.0, "Te|WTe2 must be attractive at kappa=1 (asymmetric formula)"

    def test_asymm_correction_smaller_than_symm(self):
        """delta_E_asym << delta_E_sym for Te|WTe2 (Silveirinha: ~2% ratio)."""
        d = 10e-9
        E_std  = casimir_energy(EPS_TE, EPS_WTE2, d)
        E_sym  = casimir_energy_chiral(EPS_TE, EPS_WTE2, d, kappa=0.5)
        E_asym = casimir_energy_chiral_asymmetric(EPS_TE, EPS_WTE2, d, kappa=0.5)
        delta_sym  = abs(E_std) - abs(E_sym)
        delta_asym = abs(E_std) - abs(E_asym)
        assert abs(delta_asym) < abs(delta_sym), (
            "Asymmetric correction must be smaller than symmetric")

    def test_asymm_correction_reduces_magnitude(self):
        """Even small asymmetric correction must reduce |E| vs kappa=0."""
        d = 10e-9
        E0   = casimir_energy_chiral_asymmetric(EPS_TE, EPS_WTE2, d, kappa=0.0)
        E05  = casimir_energy_chiral_asymmetric(EPS_TE, EPS_WTE2, d, kappa=0.5)
        assert abs(E05) < abs(E0)
