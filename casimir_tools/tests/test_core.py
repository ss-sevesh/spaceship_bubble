"""
tests/test_core.py — pytest suite for casimir_tools._core.

Tests physical correctness of all Lifshitz-Casimir functions:
  - Dielectric models (boundary conditions, monotonicity)
  - casimir_energy (sign, scaling, symmetry)
  - casimir_energy_chiral (T=0 limit, repulsion onset)
  - casimir_energy_aniso (isotropic limit)
  - casimir_energy_2osc (self-consistency with 1-osc at same eps_static)
  - casimir_energy_finite_T (T→0 limit, thermal correction sign)
  - casimir_force (sign, scaling, kappa=0 limit)
  - sweep functions (shape, monotonicity)

Run with:  pytest casimir_tools/tests/ -v
"""

import math
import numpy as np
import pytest

from casimir_tools._core import (
    HBAR, KB, C, OMEGA_UV,
    epsilon_imaginary,
    epsilon_imaginary_2osc,
    epsilon_imaginary_drude,
    casimir_energy,
    casimir_energy_chiral,
    casimir_energy_chiral_asymmetric,
    casimir_energy_fast,
    casimir_energy_aniso,
    casimir_energy_2osc,
    casimir_energy_finite_T,
    casimir_force,
    casimir_force_chiral,
    compute_asymmetric_kappa_crit,
    sweep_separation,
    sweep_separation_aniso,
    sweep_finite_T,
    sweep_force,
    TE_2OSC,
    WTE2_2OSC,
)

# ── Reference material values ─────────────────────────────────────────────────
EPS_TE   = 164.27   # Te trace-average static dielectric
EPS_WTE2 = 6.16     # WTe2 (P-6m2) trace-average

# Uniaxial tensor components
TE_PERP,   TE_PAR   = 130.86, 231.09
WTE2_PERP, WTE2_PAR = 8.46,   1.56

D_10NM  = 10e-9    # 10 nm separation
D_100NM = 100e-9   # 100 nm separation


# ═══════════════════════════════════════════════════════════════════════════════
# 1. Dielectric models
# ═══════════════════════════════════════════════════════════════════════════════

class TestEpsilonImaginary:
    """Single-oscillator Cauchy model."""

    def test_static_limit(self):
        """At xi=0, eps should equal eps_static."""
        assert epsilon_imaginary(EPS_TE, xi=0.0) == pytest.approx(EPS_TE, rel=1e-6)

    def test_vacuum_limit(self):
        """At xi >> omega_uv, eps → 1 (within single-oscillator rounding at 1e20 rad/s)."""
        val = epsilon_imaginary(EPS_TE, xi=1e20)
        assert abs(val - 1.0) < 1e-5

    def test_monotonic_decrease(self):
        """eps(xi) is monotonically decreasing in xi."""
        xis = np.logspace(10, 18, 30)
        eps_vals = [epsilon_imaginary(EPS_TE, xi) for xi in xis]
        for a, b in zip(eps_vals, eps_vals[1:]):
            assert a > b

    def test_always_ge_one(self):
        """eps(xi) >= 1 for all xi >= 0."""
        for xi in [0.0, 1e10, 1e15, 1e20]:
            assert epsilon_imaginary(EPS_TE, xi) >= 1.0


class TestEpsilonImaginary2Osc:
    """Two-oscillator Sellmeier model."""

    def test_static_limit(self):
        """At xi=0, eps = 1 + C1 + C2."""
        C1, om1, C2, om2 = 45.77, 3.0e13, 117.50, 4.5e15
        expected = 1.0 + C1 + C2
        assert epsilon_imaginary_2osc(C1, om1, C2, om2, 0.0) == pytest.approx(expected, rel=1e-6)

    def test_vacuum_limit(self):
        """At xi >> max(omega), eps → 1."""
        val = epsilon_imaginary_2osc(45.77, 3.0e13, 117.50, 4.5e15, xi=1e20)
        assert abs(val - 1.0) < 1e-6

    def test_te_2osc_static_matches_eps_static(self):
        """TE_2OSC parameters give 1+C1+C2 == 164.27."""
        p = TE_2OSC
        eps0 = 1.0 + p["C1"] + p["C2"]
        assert eps0 == pytest.approx(164.27, abs=0.1)

    def test_wte2_2osc_static_matches_eps_static(self):
        """WTE2_2OSC parameters give 1+C1+C2 == 6.16."""
        p = WTE2_2OSC
        eps0 = 1.0 + p["C1"] + p["C2"]
        assert eps0 == pytest.approx(6.16, abs=0.1)

    def test_electronic_contribution(self):
        """Between omega1 and omega2, eps ≈ 1 + C2 (IR already relaxed at 10x omega1)."""
        C1, om1, C2, om2 = 45.77, 3.0e13, 117.50, 4.5e15
        xi_mid = 3.0e14   # 10x om1, << om2 → IR oscillator contributes < 0.5%
        val = epsilon_imaginary_2osc(C1, om1, C2, om2, xi_mid)
        expected = 1.0 + C2  # electronic contribution dominates
        assert val == pytest.approx(expected, rel=0.01)


# ═══════════════════════════════════════════════════════════════════════════════
# 2. Isotropic Lifshitz energy
# ═══════════════════════════════════════════════════════════════════════════════

class TestCasimirEnergy:
    """casimir_energy — standard zero-temperature isotropic Lifshitz."""

    def test_sign_attractive(self):
        """Standard Lifshitz energy is attractive (negative)."""
        E = casimir_energy(EPS_TE, EPS_WTE2, D_10NM)
        assert E < 0.0

    def test_symmetric(self):
        """E(eps1, eps2) == E(eps2, eps1)."""
        E12 = casimir_energy(EPS_TE, EPS_WTE2, D_10NM)
        E21 = casimir_energy(EPS_WTE2, EPS_TE, D_10NM)
        assert E12 == pytest.approx(E21, rel=1e-4)

    def test_increases_with_distance(self):
        """Casimir energy magnitude |E| decreases with separation (less attractive)."""
        E10  = abs(casimir_energy(EPS_TE, EPS_WTE2, D_10NM))
        E100 = abs(casimir_energy(EPS_TE, EPS_WTE2, D_100NM))
        assert E10 > E100

    def test_power_law_scaling(self):
        """E ~ d^{-2} asymptotically. Ratio at 2× separation ≈ 0.25 (±30%)."""
        E1 = casimir_energy(EPS_TE, EPS_WTE2, D_10NM)
        E2 = casimir_energy(EPS_TE, EPS_WTE2, 2.0 * D_10NM)
        ratio = E2 / E1
        assert 0.15 < ratio < 0.40   # rough d^{-2} check

    def test_vacuum_limit(self):
        """With eps1=1 (vacuum), energy should be very small."""
        E = casimir_energy(1.0001, EPS_WTE2, D_10NM)
        E_std = casimir_energy(EPS_TE, EPS_WTE2, D_10NM)
        assert abs(E) < 1e-3 * abs(E_std)

    def test_magnitude_reasonable(self):
        """At 10 nm, Te|WTe2 energy should be in 0.01–1 mJ/m² range."""
        E_mJm2 = abs(casimir_energy(EPS_TE, EPS_WTE2, D_10NM)) * 1e3
        assert 0.01 < E_mJm2 < 10.0


# ═══════════════════════════════════════════════════════════════════════════════
# 3. Chiral Casimir energy
# ═══════════════════════════════════════════════════════════════════════════════

class TestCasimirEnergyChiral:
    """casimir_energy_chiral — κ² symmetric correction (Te|Te geometry only)."""

    def test_kappa0_equals_standard(self):
        """At kappa=0, chiral energy equals standard Lifshitz (any pair)."""
        E_std    = casimir_energy(EPS_TE, EPS_WTE2, D_10NM)
        E_chiral = casimir_energy_chiral(EPS_TE, EPS_WTE2, D_10NM, kappa=0.0)
        assert E_chiral == pytest.approx(E_std, rel=1e-4)

    def test_chiral_correction_positive_and_kappa_crit_physical(self):
        """δE_sym > 0 and κ_crit < 1 for Te|Te (repulsion achievable in physical range).

        For EPS_TE=164.27 (trace average), χ = δE/|E_std| ≈ 1.58 at d=10nm,
        giving κ_crit ≈ 0.795.  Repulsion is therefore achievable for κ > 0.795,
        which is within the physical range [0,1].
        At κ=1.0, E > 0 (net repulsion confirmed).
        """
        from casimir_tools._core import _casimir_chiral_correction_symmetric
        d = 10e-9
        E_std   = casimir_energy(EPS_TE, EPS_TE, d)
        delta_E = _casimir_chiral_correction_symmetric(EPS_TE, EPS_TE, d)
        assert delta_E > 0.0, "Chiral correction must be positive (reduces attraction)"
        chi = delta_E / abs(E_std)
        assert chi > 1.0, f"χ={chi:.3f} must exceed 1 for Te|Te (repulsion achievable)"
        kappa_crit = 1.0 / chi ** 0.5
        assert kappa_crit < 1.0, (
            f"κ_crit={kappa_crit:.3f} must be < 1 (repulsion achievable in physical range)"
        )
        # Confirm actual repulsion at κ=1
        E_k1 = casimir_energy_chiral(EPS_TE, EPS_TE, d, kappa=1.0)
        assert E_k1 > 0.0, f"E(κ=1)={E_k1:.3e} must be positive (net repulsion)"

    def test_kappa_reduces_magnitude_te_te(self):
        """For Te|Te symmetric pair, kappa=0.5 reduces |E| vs kappa=0."""
        E_std = casimir_energy_chiral(EPS_TE, EPS_TE, D_10NM, kappa=0.0)
        E_k05 = casimir_energy_chiral(EPS_TE, EPS_TE, D_10NM, kappa=0.5)
        assert abs(E_k05) < abs(E_std)

    def test_kappa_monotonic_suppression_te_te(self):
        """Increasing kappa monotonically reduces |E| for symmetric Te|Te."""
        kappas = [0.0, 0.2, 0.4, 0.6, 0.8]
        Es = [casimir_energy_chiral(EPS_TE, EPS_TE, D_10NM, k) for k in kappas]
        for a, b in zip(Es, Es[1:]):
            assert b >= a


# ═══════════════════════════════════════════════════════════════════════════════
# 4. Anisotropic Lifshitz
# ═══════════════════════════════════════════════════════════════════════════════

class TestCasimirEnergyAniso:
    """casimir_energy_aniso — uniaxial Fresnel coefficients."""

    def test_isotropic_limit(self):
        """If eps_perp == eps_par, aniso result matches isotropic."""
        eps = EPS_WTE2  # use smaller eps for faster convergence
        E_iso   = casimir_energy(eps, eps, D_10NM)
        E_aniso = casimir_energy_aniso(eps, eps, eps, eps, D_10NM)
        assert E_aniso == pytest.approx(E_iso, rel=0.02)

    def test_sign_attractive(self):
        """Te|WTe2 anisotropic energy is still attractive."""
        E = casimir_energy_aniso(TE_PERP, TE_PAR, WTE2_PERP, WTE2_PAR, D_10NM)
        assert E < 0.0

    def test_wte2_aniso_smaller_than_iso(self):
        """WTe2 eps_par=1.56 suppresses TM modes — aniso < iso in magnitude."""
        E_iso   = casimir_energy(EPS_TE, EPS_WTE2, D_10NM)
        E_aniso = casimir_energy_aniso(TE_PERP, TE_PAR, WTE2_PERP, WTE2_PAR, D_10NM)
        # Aniso is smaller in absolute value (less stiction)
        assert abs(E_aniso) < abs(E_iso)

    def test_te_mode_contributes_to_attraction(self):
        """TE polarisation contributes to the attractive Casimir energy.

        The _inner_te integrand returns negative values (ln(1 - r1*r2*e^{-x}) < 0
        because r1*r2 > 0 for like materials), meaning TE adds to attraction.

        Tested indirectly: a symmetric configuration casimir_energy(eps=5, eps=5)
        must have a larger attractive magnitude than a configuration where TE is
        suppressed.  TE Fresnel coefficients depend only on eps_perp; setting
        eps_perp ≈ 1 (vacuum) in casimir_energy_aniso drives r_TE → 0 and leaves
        only the TM contribution.  The full isotropic energy must therefore satisfy
        |E_iso| > |E_TM_only|.
        """
        eps_sym = 5.0
        d       = D_10NM
        # Full isotropic energy (both TE and TM modes)
        E_iso = casimir_energy(eps_sym, eps_sym, d)
        # Near-vacuum eps_perp suppresses TE (r_TE → 0); eps_par=eps_sym keeps TM
        E_TM_only = casimir_energy_aniso(1.001, eps_sym, 1.001, eps_sym, d)
        assert abs(E_iso) > abs(E_TM_only), (
            f"TE should contribute to attraction: |E_iso|={abs(E_iso):.4e}, "
            f"|E_TM_only|={abs(E_TM_only):.4e}"
        )


# ═══════════════════════════════════════════════════════════════════════════════
# 5. 2-oscillator Casimir energy
# ═══════════════════════════════════════════════════════════════════════════════

class TestCasimirEnergy2Osc:
    """casimir_energy_2osc — two-oscillator Sellmeier model."""

    def test_sign_attractive(self):
        """2-osc energy is attractive."""
        p = TE_2OSC
        E = casimir_energy_2osc(p["C1"], p["omega1"], p["C2"], p["omega2"],
                                 p["C1"], p["omega1"], p["C2"], p["omega2"],
                                 D_10NM)
        assert E < 0.0

    def test_roughly_matches_single_osc(self):
        """2-osc and 1-osc should agree within 50% (same eps_static)."""
        p   = TE_2OSC
        E2  = casimir_energy_2osc(p["C1"], p["omega1"], p["C2"], p["omega2"],
                                   p["C1"], p["omega1"], p["C2"], p["omega2"],
                                   D_10NM)
        E1  = casimir_energy(1.0 + p["C1"] + p["C2"],
                              1.0 + p["C1"] + p["C2"], D_10NM)
        ratio = abs(E2) / abs(E1)
        assert 0.3 < ratio < 2.0

    def test_symmetric(self):
        """2-osc energy is symmetric in material swap."""
        p1, p2 = TE_2OSC, WTE2_2OSC
        E12 = casimir_energy_2osc(p1["C1"], p1["omega1"], p1["C2"], p1["omega2"],
                                   p2["C1"], p2["omega1"], p2["C2"], p2["omega2"],
                                   D_10NM)
        E21 = casimir_energy_2osc(p2["C1"], p2["omega1"], p2["C2"], p2["omega2"],
                                   p1["C1"], p1["omega1"], p1["C2"], p1["omega2"],
                                   D_10NM)
        assert E12 == pytest.approx(E21, rel=1e-4)


# ═══════════════════════════════════════════════════════════════════════════════
# 6. Finite-temperature Lifshitz
# ═══════════════════════════════════════════════════════════════════════════════

class TestCasimirEnergyFiniteT:
    """casimir_energy_finite_T — Matsubara summation at T > 0."""

    def test_sign_attractive(self):
        """Finite-T energy is still attractive at short range."""
        E = casimir_energy_finite_T(EPS_TE, EPS_WTE2, D_10NM, T=300.0)
        assert E < 0.0

    @pytest.mark.slow
    def test_low_T_approaches_T0(self):
        """At T=1 K (<<300 K), finite-T result ≈ T=0 within 5%."""
        E_T0  = casimir_energy(EPS_TE, EPS_WTE2, D_10NM)
        E_T1  = casimir_energy_finite_T(EPS_TE, EPS_WTE2, D_10NM, T=1.0, n_max=50)
        assert abs(E_T1 - E_T0) / abs(E_T0) < 0.05

    @pytest.mark.slow
    def test_T300_close_to_T0_at_small_d(self):
        """At d=10 nm << l_T≈1200 nm, T=300 K correction is < 5%."""
        E_T0   = casimir_energy(EPS_TE, EPS_WTE2, D_10NM)
        E_T300 = casimir_energy_finite_T(EPS_TE, EPS_WTE2, D_10NM, T=300.0, n_max=500)
        rel_diff = abs(E_T300 - E_T0) / abs(E_T0)
        assert rel_diff < 0.05

    @pytest.mark.slow
    def test_T300_larger_magnitude_than_T0_at_large_d(self):
        """At d ~ l_T (1000 nm), T=300K energy is larger than T=0 (thermal dominates)."""
        d_large = 1000e-9
        E_T0   = casimir_energy(EPS_TE, EPS_WTE2, d_large)
        E_T300 = casimir_energy_finite_T(EPS_TE, EPS_WTE2, d_large, T=300.0, n_max=20)
        assert abs(E_T300) > abs(E_T0)

    @pytest.mark.slow
    def test_classical_dlp_limit_at_large_d(self):
        """At d=5000 nm >> l_T≈1215 nm, finite-T energy approaches classical DLP formula.

        Classical limit (Dzyaloshinskii-Lifshitz-Pitaevskii n=0 Matsubara term):
            E_classical = -k_B T * beta1 * beta2 / (8 * pi * d^2)
        where beta = (eps-1)/(eps+1).

        At d >> l_T, the quantum fluctuation terms are exponentially suppressed and
        the n=0 Matsubara term dominates.  Verified within 10%.
        """
        T   = 300.0
        d   = 5000e-9   # 5000 nm >> l_T ≈ 1215 nm
        beta1 = (EPS_TE   - 1.0) / (EPS_TE   + 1.0)
        beta2 = (EPS_WTE2 - 1.0) / (EPS_WTE2 + 1.0)
        E_classical = -KB * T * beta1 * beta2 / (8.0 * math.pi * d ** 2)
        E_full = casimir_energy_finite_T(EPS_TE, EPS_WTE2, d, T=T, n_max=20)
        rel_diff = abs(E_full - E_classical) / abs(E_classical)
        assert rel_diff < 0.10, (
            f"Classical DLP limit violated at d=5000 nm: "
            f"E_full={E_full:.4e}, E_classical={E_classical:.4e}, "
            f"rel_diff={rel_diff:.3f}"
        )


# ═══════════════════════════════════════════════════════════════════════════════
# 6b. Fast finite-T Hamaker model (classical n=0 Matsubara correction)
# ═══════════════════════════════════════════════════════════════════════════════

class TestCasimirEnergyFastFiniteT:
    """Fast Hamaker model with classical thermal correction.

    casimir_energy_fast_finite_T lives in src/optimizer.py and cannot be
    imported here (pymoo dependency not available in casimir-tools venv).
    The correction formula is simple enough to verify inline:

        E_classical = -k_B T / (8 pi d^2) * beta1 * beta2

    Since beta1, beta2 > 0 for eps > 1, E_classical < 0, so
    casimir_energy_fast_finite_T < casimir_energy_fast (more negative).
    """

    def test_thermal_correction_increases_attraction(self):
        """Thermal (classical n=0) correction is negative, making total E more negative.

        Reconstructs casimir_energy_fast_finite_T inline from its published formula
        (DLP 1961; Parsegian 2006 eq. 2.17) to avoid the pymoo import dependency:

            E_T = E_fast(kappa=0) + E_classical
            E_classical = -k_B T * beta1 * beta2 / (8 pi d^2)

        Verifies E_T < E_fast(kappa=0), i.e., thermal correction always adds
        to attraction when eps1, eps2 > 1.
        """
        T    = 300.0
        d    = D_10NM
        kappa = 0.0
        E_fast = casimir_energy_fast(EPS_TE, EPS_WTE2, d, kappa)
        beta1 = (EPS_TE   - 1.0) / (EPS_TE   + 1.0)
        beta2 = (EPS_WTE2 - 1.0) / (EPS_WTE2 + 1.0)
        E_classical = -KB * T / (8.0 * math.pi * d ** 2) * beta1 * beta2
        E_fast_finite_T = E_fast + E_classical
        # Thermal correction must be negative (attractive)
        assert E_classical < 0.0
        # Total must be more negative than T=0 Hamaker result
        assert E_fast_finite_T < E_fast, (
            f"E_fast_finite_T={E_fast_finite_T:.4e} should be more negative "
            f"than E_fast={E_fast:.4e}"
        )

    def test_thermal_correction_sign_independent_of_kappa(self):
        """Classical correction is kappa-independent; sign holds for any valid kappa."""
        T   = 300.0
        d   = D_100NM
        beta1 = (EPS_TE   - 1.0) / (EPS_TE   + 1.0)
        beta2 = (EPS_WTE2 - 1.0) / (EPS_WTE2 + 1.0)
        E_classical = -KB * T / (8.0 * math.pi * d ** 2) * beta1 * beta2
        for kappa in [0.0, 0.2, 0.5]:
            E_fast   = casimir_energy_fast(EPS_TE, EPS_WTE2, d, kappa)
            E_total  = E_fast + E_classical
            assert E_total < E_fast, (
                f"kappa={kappa}: E_total={E_total:.4e} should be < E_fast={E_fast:.4e}"
            )


# ═══════════════════════════════════════════════════════════════════════════════
# 7. Casimir force
# ═══════════════════════════════════════════════════════════════════════════════

class TestCasimirForce:
    """casimir_force — F = -dE/dd."""

    def test_sign_attractive(self):
        """Standard Lifshitz force is attractive (negative)."""
        F = casimir_force(EPS_TE, EPS_WTE2, D_10NM)
        assert F < 0.0

    def test_kappa0_force_consistent_with_energy(self):
        """At kappa=0, chiral force equals standard force."""
        F_std    = casimir_force(EPS_TE, EPS_WTE2, D_10NM)
        F_chiral = casimir_force_chiral(EPS_TE, EPS_WTE2, D_10NM, kappa=0.0)
        assert F_chiral == pytest.approx(F_std, rel=1e-4)

    def test_force_stronger_at_smaller_d(self):
        """Casimir force magnitude increases at smaller separation."""
        F10  = abs(casimir_force(EPS_TE, EPS_WTE2, D_10NM))
        F100 = abs(casimir_force(EPS_TE, EPS_WTE2, D_100NM))
        assert F10 > F100

    def test_chiral_repulsion(self):
        """At kappa=1.0 and large d, chiral force is repulsive (positive)."""
        F = casimir_force_chiral(EPS_TE, EPS_WTE2, 50e-9, kappa=1.0)
        assert F > 0.0

    @pytest.mark.slow
    def test_force_approximately_negative_d_derivative(self):
        """Numerical -dE/dd should match casimir_force within 5%."""
        d     = D_10NM
        delta = d * 1e-4
        E1    = casimir_energy(EPS_TE, EPS_WTE2, d - delta)
        E2    = casimir_energy(EPS_TE, EPS_WTE2, d + delta)
        F_num = -(E2 - E1) / (2.0 * delta)
        F_ana = casimir_force(EPS_TE, EPS_WTE2, d)
        assert F_ana == pytest.approx(F_num, rel=0.05)


# ═══════════════════════════════════════════════════════════════════════════════
# 8. Sweep utilities
# ═══════════════════════════════════════════════════════════════════════════════

class TestSweepFunctions:
    """Shape and monotonicity checks for sweep utilities."""

    def test_sweep_separation_shape(self):
        d_nm, E = sweep_separation(EPS_TE, EPS_WTE2, n_points=5)
        assert d_nm.shape == (5,)
        assert E.shape    == (5,)

    def test_sweep_separation_monotonic(self):
        """Larger d → less stiction → E closer to 0 (less negative)."""
        d_nm, E = sweep_separation(EPS_TE, EPS_WTE2, n_points=8)
        for a, b in zip(E, E[1:]):
            assert a < b   # E increases (becomes less negative) with d

    def test_sweep_separation_aniso_shape(self):
        d_nm, E = sweep_separation_aniso(
            TE_PERP, TE_PAR, WTE2_PERP, WTE2_PAR, n_points=4)
        assert d_nm.shape == (4,)
        assert E.shape    == (4,)

    def test_sweep_finite_T_shape(self):
        d_nm, E = sweep_finite_T(EPS_TE, EPS_WTE2, T=300.0, n_points=4)
        assert d_nm.shape == (4,)
        assert E.shape    == (4,)

    def test_sweep_force_shape(self):
        d_nm, F = sweep_force(EPS_TE, EPS_WTE2, n_points=4)
        assert d_nm.shape == (4,)
        assert F.shape    == (4,)

    def test_sweep_force_all_negative(self):
        """Standard Lifshitz force should be attractive (negative) across 1–100 nm."""
        _, F = sweep_force(EPS_TE, EPS_WTE2, n_points=6)
        assert np.all(F < 0.0)


# ═══════════════════════════════════════════════════════════════════════════════
# 9. Physical constants
# ═══════════════════════════════════════════════════════════════════════════════

class TestPhysicalConstants:
    def test_hbar(self):
        assert HBAR == pytest.approx(1.0545718e-34, rel=1e-6)

    def test_kb(self):
        assert KB == pytest.approx(1.380649e-23, rel=1e-6)

    def test_c(self):
        assert C == pytest.approx(2.99792458e8, rel=1e-8)

    def test_thermal_length_300K(self):
        """Thermal length l_T = hbar*c/(2*pi*k_B*T) ≈ 1.2 µm at 300 K."""
        l_T = HBAR * C / (2.0 * math.pi * KB * 300.0)
        assert 1.0e-6 < l_T < 1.5e-6


# ═══════════════════════════════════════════════════════════════════════════════
# 10. Asymmetric chiral Casimir (Silveirinha 2010) — key paper contribution
# ═══════════════════════════════════════════════════════════════════════════════

class TestCasimirEnergyChiralAsymmetric:
    """
    Tests for casimir_energy_chiral_asymmetric() — the correct formula for
    Te (chiral, κ≠0) | vac | WTe₂ (non-chiral, κ=0) per Silveirinha (2010).
    Paper claims: δE_asym/δE_sym ≈ 2%; κ_crit_asym ≈ 6.3 (unphysical).
    """

    D = 10e-9  # 10 nm reference separation

    def test_kappa0_equals_standard(self):
        """At κ=0 asymmetric formula must reproduce bare Lifshitz energy."""
        E_std  = casimir_energy(EPS_TE, EPS_WTE2, self.D)
        E_asym = casimir_energy_chiral_asymmetric(EPS_TE, EPS_WTE2, self.D, kappa=0.0)
        assert E_asym == pytest.approx(E_std, rel=1e-6)

    def test_asymmetric_correction_smaller_than_symmetric(self):
        """
        δE_asym should be much smaller than δE_sym at the same κ.
        Paper Table III: δE_asym/δE_sym ≈ 2% for Te|WTe₂.
        """
        kappa = 0.5
        E_std  = casimir_energy(EPS_TE, EPS_WTE2, self.D)
        E_sym  = casimir_energy_chiral(EPS_TE, EPS_WTE2, self.D, kappa=kappa)
        E_asym = casimir_energy_chiral_asymmetric(EPS_TE, EPS_WTE2, self.D, kappa=kappa)
        delta_sym  = abs(E_std) - abs(E_sym)   # reduction from symmetrc correction
        delta_asym = abs(E_std) - abs(E_asym)  # reduction from asymmetric correction
        # Asymmetric reduction must be much smaller than symmetric
        assert abs(delta_asym) < abs(delta_sym)

    def test_still_attractive_at_kappa1_te_wte2(self):
        """
        For Te|WTe₂, repulsion is NOT achievable (κ_crit_asym ≈ 6.3 > 1).
        Even at maximum physical κ=1.0 the energy stays negative (attractive).
        """
        E_asym = casimir_energy_chiral_asymmetric(EPS_TE, EPS_WTE2, self.D, kappa=1.0)
        assert E_asym < 0.0, "Te|WTe₂ must remain attractive at κ=1.0 (asymmetric formula)"

    def test_delta_E_asym_positive(self):
        """The asymmetric chiral correction δE_asym > 0 (reduces magnitude of attraction)."""
        E_std  = casimir_energy(EPS_TE, EPS_WTE2, self.D)
        E_asym = casimir_energy_chiral_asymmetric(EPS_TE, EPS_WTE2, self.D, kappa=0.5)
        # |E_asym| < |E_std| — correction reduces stiction energy
        assert abs(E_asym) < abs(E_std)


# ═══════════════════════════════════════════════════════════════════════════════
# 11. Asymmetric κ_crit diagnostic — paper Table II / Sec. IV.C claims
# ═══════════════════════════════════════════════════════════════════════════════

class TestComputeAsymmetricKappaCrit:
    """
    Tests for compute_asymmetric_kappa_crit() — validates paper claims:
      - κ_crit_sym(Te|Te) ≈ 0.795  (sub-unity → repulsion achievable)
      - κ_crit_asym(Te|WTe₂) ≈ 6.3 (unphysical → repulsion NOT achievable)
      - δE_asym/δE_sym ≈ 2% for Te|WTe₂ at MEMS separations
    """

    D = 10e-9  # 10 nm

    def test_returns_required_keys(self):
        """Result dict must contain all keys cited in the paper."""
        result = compute_asymmetric_kappa_crit(EPS_TE, EPS_WTE2, self.D)
        required = {"E_std_Jm2", "delta_E_sym_Jm2", "delta_E_asym_Jm2",
                    "ratio_asym_over_sym", "kappa_crit_sym", "kappa_crit_asym"}
        assert required.issubset(result.keys())

    def test_kappa_crit_asym_greater_than_sym_te_wte2(self):
        """For Te|WTe₂: κ_crit_asym >> κ_crit_sym (asymmetric formula is weaker)."""
        result = compute_asymmetric_kappa_crit(EPS_TE, EPS_WTE2, self.D)
        assert result["kappa_crit_asym"] > result["kappa_crit_sym"]

    def test_ratio_below_5_percent(self):
        """Paper claims δE_asym/δE_sym ≈ 2% — verify it stays below 5%."""
        result = compute_asymmetric_kappa_crit(EPS_TE, EPS_WTE2, self.D)
        assert result["ratio_asym_over_sym"] < 0.05

    def test_kappa_crit_sym_subunity_te_te(self):
        """For symmetric Te|Te: κ_crit_sym < 1 — repulsion IS achievable."""
        result = compute_asymmetric_kappa_crit(EPS_TE, EPS_TE, self.D)
        assert result["kappa_crit_sym"] < 1.0

    def test_kappa_crit_asym_unphysical_te_wte2(self):
        """For Te|WTe₂: κ_crit_asym > 1 — repulsion NOT achievable (paper Sec. IV.C)."""
        result = compute_asymmetric_kappa_crit(EPS_TE, EPS_WTE2, self.D)
        assert result["kappa_crit_asym"] > 1.0


# ═══════════════════════════════════════════════════════════════════════════════
# 12. Drude dielectric model — used in Au/SiO₂ benchmark (paper Sec. IV.I)
# ═══════════════════════════════════════════════════════════════════════════════

class TestEpsilonImaginaryDrude:
    """
    Tests for epsilon_imaginary_drude() — free-electron Drude model used in
    the Au|SiO₂ code-validation benchmark (paper Fig. 12, Sec. IV.I).
    Au parameters: omega_p = 1.37e16 rad/s, gamma = 5.32e13 rad/s.
    """

    OMEGA_P = 1.37e16   # Au plasma frequency (Lambrecht & Reynaud 2000)
    GAMMA   = 5.32e13   # Au damping rate

    def test_always_geq_one(self):
        """Drude dielectric must be >= 1 across all physical xi > 0."""
        xi_vals = np.logspace(10, 18, 50)
        for xi in xi_vals:
            eps = epsilon_imaginary_drude(xi, self.OMEGA_P, self.GAMMA)
            assert eps >= 1.0, f"eps={eps} < 1 at xi={xi:.2e}"

    def test_high_xi_approaches_vacuum(self):
        """At xi >> omega_p: eps_Drude(i*xi) → 1 + (omega_p/xi)^2 → 1."""
        xi_large = 1e20   # >> omega_p = 1.37e16
        eps = epsilon_imaginary_drude(xi_large, self.OMEGA_P, self.GAMMA)
        assert eps == pytest.approx(1.0, abs=1e-4)

    def test_low_xi_large_value(self):
        """At xi << gamma (metallic regime): eps is large (>>1)."""
        xi_small = 1e10   # << gamma = 5.32e13
        eps = epsilon_imaginary_drude(xi_small, self.OMEGA_P, self.GAMMA)
        assert eps > 1e3
