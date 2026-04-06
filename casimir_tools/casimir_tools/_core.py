"""
casimir_tools._core — Self-contained Lifshitz-Casimir computation engine.

Implements the full Lifshitz formalism for zero-temperature and finite-temperature
Casimir energy and force between planar dielectric half-spaces, with extensions
for chiral media, uniaxial anisotropy, and multi-oscillator dielectric models.

All functions are SI throughout. No external dependencies beyond numpy/scipy.

References
----------
[1] Lifshitz (1956) Sov. Phys. JETP 2, 73.
[2] Dzyaloshinskii, Lifshitz, Pitaevskii (1961) Adv. Phys. 10, 165.
[3] Zhao et al. (2009) Phys. Rev. Lett. 103, 103602.  [chiral Casimir]
[4] Bimonte et al. (2009) Phys. Rev. A 79, 042906.     [uniaxial Lifshitz]
[5] Parsegian (2006) Van der Waals Forces. Cambridge UP.
"""

from __future__ import annotations

import numpy as np
from scipy.integrate import quad
from typing import Callable

# ── Physical constants (SI) ───────────────────────────────────────────────────
HBAR     = 1.0545718e-34   # J·s
KB       = 1.380649e-23    # J/K
C        = 2.99792458e8    # m/s
OMEGA_UV = 2.0e16          # rad/s — single-oscillator UV pole (~13 eV)

# ── Default 2-oscillator parameters for Te and WTe2 (P-6m2) ─────────────────
# Literature-grounded 2-oscillator Sellmeier parameters
# Te:   ω1 = IR phonon 160 cm⁻¹ (Caldwell & Fan 1959); ω2 = UV ~3 eV (Stuke 1965)
# WTe2: ω2 = interband ~4 eV (Ali et al., Nature 514, 205, 2014)
TE_2OSC   = {"C1": 45.77,  "omega1": 3.0e13, "C2": 117.50, "omega2": 4.5e15}
WTE2_2OSC = {"C1":  0.30,  "omega1": 5.0e13, "C2":   4.86, "omega2": 6.0e15}

# ── Dielectric models ─────────────────────────────────────────────────────────

def epsilon_imaginary(eps_static: float, xi: float,
                      omega_uv: float = OMEGA_UV) -> float:
    """Single-oscillator Cauchy model: eps(i*xi) = 1 + (eps0-1)/(1+(xi/wUV)^2)."""
    return 1.0 + (eps_static - 1.0) / (1.0 + (xi / omega_uv) ** 2)


def epsilon_imaginary_2osc(C1: float, omega1: float,
                            C2: float, omega2: float,
                            xi: float) -> float:
    """
    Two-oscillator Sellmeier: eps(i*xi) = 1 + C1/(1+(xi/w1)^2) + C2/(1+(xi/w2)^2).

    At xi=0: eps = 1 + C1 + C2 = eps_static.
    Resolves IR phonon (omega1) and UV electronic (omega2) contributions.
    """
    return (1.0
            + C1 / (1.0 + (xi / omega1) ** 2)
            + C2 / (1.0 + (xi / omega2) ** 2))


def epsilon_imaginary_drude(xi: float, omega_p: float, gamma: float) -> float:
    """
    Drude-model dielectric at imaginary frequency i*xi for free-electron metals.

        eps_Drude(i*xi) = 1 + omega_p² / (xi * (xi + gamma))

    Reference: Lambrecht & Reynaud (2000) Eur. Phys. J. D 8, 309.
    Gold: omega_p = 1.37e16 rad/s, gamma = 5.32e13 rad/s.

    Args:
        xi:      Imaginary frequency (rad/s), must be > 0.
        omega_p: Plasma frequency (rad/s).
        gamma:   Damping rate (rad/s).

    Returns:
        eps(i*xi) >= 1.0.
    """
    return 1.0 + omega_p ** 2 / (xi * (xi + gamma))


# ── Fresnel coefficients at imaginary frequency ───────────────────────────────

def _r_te(eps: float, p: float) -> float:
    """TE Fresnel amplitude: r = (p - q)/(p + q), q = sqrt(eps-1+p^2)."""
    q = np.sqrt(eps - 1.0 + p ** 2)
    return (p - q) / (p + q)


def _r_tm(eps: float, p: float) -> float:
    """TM Fresnel amplitude: r = (eps*p - q)/(eps*p + q), q = sqrt(eps-1+p^2)."""
    q = np.sqrt(eps - 1.0 + p ** 2)
    return (eps * p - q) / (eps * p + q)


def _r_te_aniso(eps_perp: float, p: float) -> float:
    """TE anisotropic Fresnel: uses eps_perp only."""
    return _r_te(eps_perp, p)


def _r_tm_aniso(eps_perp: float, eps_par: float, p: float) -> float:
    """TM anisotropic Fresnel for uniaxial medium (optic axis along z):
    q^TM = sqrt(eps_perp/eps_par * (eps_par - 1 + p^2))."""
    q_sq = (eps_perp / eps_par) * (eps_par - 1.0 + p ** 2)
    if q_sq < 0.0:
        import warnings
        warnings.warn(
            f"_r_tm_aniso: q²={q_sq:.3e} < 0 "
            f"(eps_perp={eps_perp:.2f}, eps_par={eps_par:.2f}, p={p:.2f}). "
            "Unphysical anisotropic region — returning 0.",
            RuntimeWarning, stacklevel=2,
        )
        return 0.0
    q = np.sqrt(q_sq)
    return (eps_perp * p - q) / (eps_perp * p + q)


# ── Inner p-integrands ────────────────────────────────────────────────────────

def _inner_te(p: float, xi: float,
              eps_fn1: Callable, eps_fn2: Callable, d: float) -> float:
    r1 = _r_te(eps_fn1(xi), p)
    r2 = _r_te(eps_fn2(xi), p)
    arg = r1 * r2 * np.exp(-2.0 * p * xi * d / C)
    return 0.0 if arg >= 1.0 else p * np.log(1.0 - arg)


def _inner_tm(p: float, xi: float,
              eps_fn1: Callable, eps_fn2: Callable, d: float) -> float:
    r1 = _r_tm(eps_fn1(xi), p)
    r2 = _r_tm(eps_fn2(xi), p)
    arg = r1 * r2 * np.exp(-2.0 * p * xi * d / C)
    return 0.0 if arg >= 1.0 else p * np.log(1.0 - arg)


def _outer(xi: float, eps_fn1: Callable, eps_fn2: Callable, d: float) -> float:
    if xi == 0.0:
        return 0.0
    # p_max must cover the evanescent tail exp(-2p·ξd/c) ≈ 0 for p ≫ c/(ξd).
    # Clamp to 1e6 so the inner quad never faces an astronomically wide interval
    # (which would make limit=N subintervals useless for small-ξ near-field).
    p_max = min(max(20.0, 5.0 * C / (xi * d)), 1.0e6)
    # Use limit=200 to handle both the near-field oscillations (large p_max)
    # and the Drude-model IR pole region.
    I_te, _ = quad(_inner_te, 1.0, p_max, args=(xi, eps_fn1, eps_fn2, d),
                   limit=200, epsrel=1e-5)
    I_tm, _ = quad(_inner_tm, 1.0, p_max, args=(xi, eps_fn1, eps_fn2, d),
                   limit=200, epsrel=1e-5)
    return xi ** 2 * (I_te + I_tm)


# ── Zero-temperature isotropic Lifshitz ──────────────────────────────────────

def casimir_energy(eps_static1: float, eps_static2: float, d: float,
                   omega_uv: float = OMEGA_UV) -> float:
    """
    Lifshitz-Casimir energy per unit area at T=0 (full double integral).

    Args:
        eps_static1, eps_static2: Static dielectric constants.
        d:   Gap separation (m).
        omega_uv: UV pole frequency (rad/s).

    Returns:
        E (J/m²). Negative = attractive.
    """
    f1 = lambda xi: epsilon_imaginary(eps_static1, xi, omega_uv)
    f2 = lambda xi: epsilon_imaginary(eps_static2, xi, omega_uv)
    xi_max = 10.0 * omega_uv
    result, _ = quad(_outer, 0.0, xi_max, args=(f1, f2, d),
                     limit=100, epsabs=1e-60, epsrel=1e-4,
                     points=[omega_uv])
    return HBAR / (4.0 * np.pi ** 2 * C ** 2) * result


# ── Chiral Casimir energy ─────────────────────────────────────────────────────

CHIRAL_FACTOR = 2.0   # κ² coefficient for Hamaker fast model only.
# Used in casimir_energy_fast, casimir_force_chiral, compute_asymmetric_kappa_crit.
# NOT used in casimir_energy_chiral (which uses the full Lifshitz double integral).
# Value differs from src/lifshitz.py (1.0); both are rough upper bounds for speed.


def _hamaker(eps1: float, eps2: float, omega_uv: float = OMEGA_UV) -> float:
    """Non-retarded London-Hamaker constant (J)."""
    beta1 = (eps1 - 1.0) / (eps1 + 1.0)
    beta2 = (eps2 - 1.0) / (eps2 + 1.0)
    return (3.0 * HBAR * omega_uv / (4.0 * np.sqrt(2.0))) * beta1 * beta2


def casimir_energy_fast(eps1: float, eps2: float, d: float,
                        kappa: float = 0.0,
                        omega_uv: float = OMEGA_UV) -> float:
    """
    Fast Hamaker approximation with chiral correction (for optimizers).

        E = -A/(12*pi*d^2) * (1 - CHIRAL_FACTOR * kappa^2)
    """
    A = _hamaker(eps1, eps2, omega_uv)
    return -A / (12.0 * np.pi * d ** 2) * (1.0 - CHIRAL_FACTOR * kappa ** 2)


def _inner_chiral_symmetric(p: float, xi: float,
                            eps_fn1: Callable, eps_fn2: Callable,
                            d: float) -> float:
    """
    Inner integrand for the symmetric chiral Casimir correction (Zhao et al. 2009).

    Computes the TE-TM cross-coupling product (κ² coefficient) for two chiral plates:

        p · (r₁^TM·r₂^TE + r₁^TE·r₂^TM) · exp(−2·p·ξ·d/c)

    For identical chirality: r^TM > 0, r^TE < 0 → cross term negative
    → _casimir_chiral_correction_symmetric returns positive δE (reduces attraction).
    """
    e1 = eps_fn1(xi)
    e2 = eps_fn2(xi)
    r1_te = _r_te(e1, p)
    r1_tm = _r_tm(e1, p)
    r2_te = _r_te(e2, p)
    r2_tm = _r_tm(e2, p)
    cross = r1_tm * r2_te + r1_te * r2_tm
    return p * cross * np.exp(-2.0 * p * xi * d / C)


def _casimir_chiral_correction_symmetric(eps_static1: float, eps_static2: float,
                                          d: float,
                                          omega_uv: float = OMEGA_UV) -> float:
    """
    Full Lifshitz κ² coefficient for the symmetric chiral correction (Zhao 2009).

    Returns δE_sym in J/m². Positive = correction reduces attraction.

        δE_sym = −2·(ħ/4π²c²) · ∫₀^∞ ξ² dξ ∫₁^∞ p dp
                    (r₁^TM·r₂^TE + r₁^TE·r₂^TM) · exp(−2pξd/c)

    Use casimir_energy_chiral() which calls this for the full non-retarded result.
    """
    eps_fn1 = lambda xi: epsilon_imaginary(eps_static1, xi, omega_uv)
    eps_fn2 = lambda xi: epsilon_imaginary(eps_static2, xi, omega_uv)

    def outer(xi: float) -> float:
        if xi == 0.0:
            return 0.0
        p_max = min(max(20.0, 5.0 * C / (xi * d)), 1.0e6)
        I, _ = quad(_inner_chiral_symmetric, 1.0, p_max,
                    args=(xi, eps_fn1, eps_fn2, d),
                    limit=200, epsrel=1e-4)
        return xi ** 2 * I

    xi_max = 10.0 * omega_uv
    raw, _ = quad(outer, 0.0, xi_max, limit=80, epsrel=1e-3, points=[omega_uv])
    prefactor = HBAR / (4.0 * np.pi ** 2 * C ** 2)
    # Negative of raw: cross term integrand is negative, delta_E is positive
    return -2.0 * prefactor * raw


def casimir_energy_chiral(eps_static1: float, eps_static2: float,
                          d: float, kappa: float = 0.0,
                          omega_uv: float = OMEGA_UV) -> float:
    """
    Casimir energy with symmetric chiral κ² correction (full Lifshitz double integral).

    Correct for two chiral plates with the same chirality κ (Zhao et al. 2009,
    PRL 103, 103602). For the asymmetric Te|WTe₂ heterostructure (only plate 1
    chiral), use casimir_energy_chiral_asymmetric() instead.

        E_chiral(d, κ) = E_Lifshitz(d) + κ² · δE_sym(d)

    where δE_sym > 0 (reduces or reverses the Casimir attraction).

    Args:
        eps_static1, eps_static2: Static dielectric constants.
        d:          Gap separation (m).
        kappa:      Effective chirality parameter κ = κ₀·sin(θ). Default 0.0.
        omega_uv:   UV oscillator pole frequency (rad/s).

    Returns:
        E (J/m²). Negative = attractive, positive = chiral repulsion.
    """
    E_std = casimir_energy(eps_static1, eps_static2, d, omega_uv)
    if kappa == 0.0:
        return E_std
    delta_E = _casimir_chiral_correction_symmetric(eps_static1, eps_static2, d, omega_uv)
    return E_std + kappa ** 2 * delta_E


# ── Anisotropic (uniaxial) Lifshitz ──────────────────────────────────────────

def casimir_energy_aniso(eps_perp1: float, eps_par1: float,
                          eps_perp2: float, eps_par2: float,
                          d: float,
                          omega_uv: float = OMEGA_UV) -> float:
    """
    Lifshitz-Casimir energy for two uniaxial half-spaces.

    Optic axis along z (interface normal). TE uses eps_perp; TM uses the
    geometric combination eps_perp/eps_par.
    """
    ep_f1 = lambda xi: epsilon_imaginary(eps_perp1, xi, omega_uv)
    ea_f1 = lambda xi: epsilon_imaginary(eps_par1,  xi, omega_uv)
    ep_f2 = lambda xi: epsilon_imaginary(eps_perp2, xi, omega_uv)
    ea_f2 = lambda xi: epsilon_imaginary(eps_par2,  xi, omega_uv)

    def outer_aniso(xi: float) -> float:
        if xi == 0.0:
            return 0.0
        ep1 = ep_f1(xi); ea1 = ea_f1(xi)
        ep2 = ep_f2(xi); ea2 = ea_f2(xi)
        p_max = min(max(20.0, 5.0 * C / (xi * d)), 1.0e6)

        def i_te(p: float) -> float:
            r1 = _r_te_aniso(ep1, p)
            r2 = _r_te_aniso(ep2, p)
            arg = r1 * r2 * np.exp(-2.0 * p * xi * d / C)
            return 0.0 if arg >= 1.0 else p * np.log(1.0 - arg)

        def i_tm(p: float) -> float:
            r1 = _r_tm_aniso(ep1, ea1, p)
            r2 = _r_tm_aniso(ep2, ea2, p)
            arg = r1 * r2 * np.exp(-2.0 * p * xi * d / C)
            return 0.0 if arg >= 1.0 else p * np.log(1.0 - arg)

        I_te, _ = quad(i_te, 1.0, p_max, limit=200, epsrel=1e-5)
        I_tm, _ = quad(i_tm, 1.0, p_max, limit=200, epsrel=1e-5)
        return xi ** 2 * (I_te + I_tm)

    xi_max = 10.0 * omega_uv
    result, _ = quad(outer_aniso, 0.0, xi_max, limit=100,
                     epsabs=1e-60, epsrel=1e-4, points=[omega_uv])
    return HBAR / (4.0 * np.pi ** 2 * C ** 2) * result


# ── 2-oscillator dielectric Lifshitz ─────────────────────────────────────────

def casimir_energy_2osc(C1_1: float, omega1_1: float, C2_1: float, omega2_1: float,
                         C1_2: float, omega1_2: float, C2_2: float, omega2_2: float,
                         d: float) -> float:
    """Casimir energy using 2-oscillator Sellmeier dielectric for both materials."""
    f1 = lambda xi: epsilon_imaginary_2osc(C1_1, omega1_1, C2_1, omega2_1, xi)
    f2 = lambda xi: epsilon_imaginary_2osc(C1_2, omega1_2, C2_2, omega2_2, xi)
    xi_max = 10.0 * max(omega2_1, omega2_2)
    # scipy.quad requires breakpoints to be sorted and strictly within (0, xi_max).
    pts = sorted(set(
        p for p in [omega1_1, omega2_1, omega1_2, omega2_2]
        if 0.0 < p < xi_max
    ))
    result, _ = quad(_outer, 0.0, xi_max, args=(f1, f2, d),
                     limit=150, epsabs=1e-60, epsrel=1e-4, points=pts)
    return HBAR / (4.0 * np.pi ** 2 * C ** 2) * result


# ── Finite-temperature Lifshitz (Matsubara) ───────────────────────────────────

def casimir_energy_finite_T(eps_static1: float, eps_static2: float,
                             d: float, T: float = 300.0,
                             omega_uv: float = OMEGA_UV,
                             n_max: int = 800) -> float:
    """
    Finite-temperature Lifshitz energy via Matsubara summation.

        E(d,T) = k_B T/(2π) × Σ'_n ∫ p dp [ln(1-r1^TE r2^TE e^{-2pξ_n d/c})
                                             + ln(1-r1^TM r2^TM e^{-2pξ_n d/c})]

    ξ_n = n × 2πk_BT/ℏ.  Prime: n=0 term weighted ½.
    Thermal length at 300 K: l_T = ℏc/(2πk_BT) ≈ 1.2 µm.

    Args:
        eps_static1, eps_static2: Static dielectric constants.
        d:      Gap (m).
        T:      Temperature (K). Default 300 K.
        omega_uv: UV pole (rad/s).
        n_max:  Matsubara terms. 800 is safe for d ≥ 1 nm at 300 K.

    Returns:
        E (J/m²). Negative = attractive.
    """
    xi_1   = 2.0 * np.pi * KB * T / HBAR
    f1     = lambda xi: epsilon_imaginary(eps_static1, xi, omega_uv)
    f2     = lambda xi: epsilon_imaginary(eps_static2, xi, omega_uv)
    pre    = KB * T / (2.0 * np.pi)
    total  = 0.0

    for n in range(n_max + 1):
        xi_n = n * xi_1

        if xi_n == 0.0:
            # Classical n=0 term: only TM survives (r^TE = 0 at xi = 0).
            # Integrate in k_perp-space (u = k_perp * d) using static betas.
            # Ref: DLP (1961) Adv. Phys. 10, 165, eq. (3.16).
            beta1_s   = (eps_static1 - 1.0) / (eps_static1 + 1.0)
            beta2_s   = (eps_static2 - 1.0) / (eps_static2 + 1.0)
            beta_prod = beta1_s * beta2_s

            def _inner_n0_kperp(u: float) -> float:
                arg = beta_prod * np.exp(-2.0 * u)
                if arg >= 1.0 or arg <= -1.0:
                    return 0.0
                return u * np.log(1.0 - arg)

            I0_kperp, _ = quad(_inner_n0_kperp, 0.0, 50.0, limit=100, epsrel=1e-6)
            total += 0.5 * I0_kperp / d ** 2   # weight 1/2; 1/d^2 from u = k_perp * d
        else:
            # (xi_n/c)^2 spectral weight: arises from k_perp dk_perp = (xi_n/c)^2 p dp.
            # Omitting this factor causes ~10^13 magnitude error. Ref: Bordag et al.
            # (2009) eq. 7.13; DLP (1961). Matches src/lifshitz.py:1807.
            xic_sq = (xi_n / C) ** 2
            p_max  = max(20.0, 5.0 * C / (xi_n * d))
            I_te, _ = quad(_inner_te, 1.0, p_max,
                           args=(xi_n, f1, f2, d), limit=80, epsrel=1e-4)
            I_tm, _ = quad(_inner_tm, 1.0, p_max,
                           args=(xi_n, f1, f2, d), limit=80, epsrel=1e-4)
            contrib = xic_sq * (I_te + I_tm)
            total  += contrib
            if n > 10 and abs(contrib) < 1e-12 * abs(total):
                break

    return pre * total


# ── Casimir force F = -dE/dd ──────────────────────────────────────────────────

def _inner_te_force(p: float, xi: float,
                    eps_fn1: Callable, eps_fn2: Callable, d: float) -> float:
    r1  = _r_te(eps_fn1(xi), p)
    r2  = _r_te(eps_fn2(xi), p)
    x   = r1 * r2 * np.exp(-2.0 * p * xi * d / C)
    if x >= 1.0 or x <= 0.0:
        return 0.0
    return p * (2.0 * p * xi / C) * x / (1.0 - x)


def _inner_tm_force(p: float, xi: float,
                    eps_fn1: Callable, eps_fn2: Callable, d: float) -> float:
    r1  = _r_tm(eps_fn1(xi), p)
    r2  = _r_tm(eps_fn2(xi), p)
    x   = r1 * r2 * np.exp(-2.0 * p * xi * d / C)
    if x >= 1.0 or x <= 0.0:
        return 0.0
    return p * (2.0 * p * xi / C) * x / (1.0 - x)


def casimir_force(eps_static1: float, eps_static2: float, d: float,
                  omega_uv: float = OMEGA_UV) -> float:
    """
    Lifshitz-Casimir force per unit area F(d) = -dE/dd (N/m²). Negative = attractive.
    """
    f1 = lambda xi: epsilon_imaginary(eps_static1, xi, omega_uv)
    f2 = lambda xi: epsilon_imaginary(eps_static2, xi, omega_uv)

    def outer_f(xi: float) -> float:
        if xi == 0.0:
            return 0.0
        p_max = min(max(20.0, 5.0 * C / (xi * d)), 1.0e6)
        I_te, _ = quad(_inner_te_force, 1.0, p_max,
                       args=(xi, f1, f2, d), limit=200, epsrel=1e-5)
        I_tm, _ = quad(_inner_tm_force, 1.0, p_max,
                       args=(xi, f1, f2, d), limit=200, epsrel=1e-5)
        return xi ** 2 * (I_te + I_tm)

    xi_max = 10.0 * omega_uv
    result, _ = quad(outer_f, 0.0, xi_max, args=(),
                     limit=100, epsabs=1e-60, epsrel=1e-4, points=[omega_uv])
    return -HBAR / (4.0 * np.pi ** 2 * C ** 2) * result


def casimir_force_chiral(eps_static1: float, eps_static2: float,
                          d: float, kappa: float,
                          omega_uv: float = OMEGA_UV) -> float:
    """Chiral Casimir force: F_chiral = F_std + kappa^2 * delta_F."""
    F_std   = casimir_force(eps_static1, eps_static2, d, omega_uv)
    dE_dd   = -2.0 * CHIRAL_FACTOR * _hamaker(eps_static1, eps_static2, omega_uv) \
              / (12.0 * np.pi * d ** 3)
    delta_F = -dE_dd   # sign: F = -dE/dd, delta_F from d/dd of -chiral*A/12pi/d^2
    return F_std + kappa ** 2 * delta_F


# ── Asymmetric chiral Casimir (Silveirinha 2010) ──────────────────────────────
#
# Correct formula for the physical Te(κ₁≠0) | vac | WTe₂(κ₂=0) heterostructure.
# Zhao et al. (2009) assumes symmetric chiral plates (κ₁≠0, κ₂≠0); for the
# asymmetric case the leading correction is second-order in scattering, giving
# an extra exp(−2pξd/c) suppression (i.e., exp(−4pξd/c) total).
#
# Reference: Silveirinha, M. G. (2010). Phys. Rev. B 82, 085101.

def _inner_chiral_asymmetric(p: float, xi: float,
                              eps_fn1: Callable, eps_fn2: Callable,
                              d: float) -> float:
    """
    Inner integrand for the asymmetric chiral Casimir correction.

    Computes the four-amplitude product (κ₁² coefficient) for the case where
    only plate 1 is chiral (κ₂ = 0):

        p · r₁^TM · r₁^TE · r₂^TM · r₂^TE · exp(−4·p·ξ·d/c)

    Both (r^TM · r^TE) factors are negative for ε > 1, so the product is
    positive → δE_asym > 0 after the prefactor (reduces attraction).
    """
    e1   = eps_fn1(xi)
    e2   = eps_fn2(xi)
    rTE1 = _r_te(e1, p)
    rTM1 = _r_tm(e1, p)
    rTE2 = _r_te(e2, p)
    rTM2 = _r_tm(e2, p)
    product = rTM1 * rTE1 * rTM2 * rTE2
    return p * product * np.exp(-4.0 * p * xi * d / C)


def _casimir_chiral_correction_asymmetric(eps_static1: float, eps_static2: float,
                                           d: float,
                                           omega_uv: float = OMEGA_UV) -> float:
    """
    κ² coefficient of the asymmetric chiral Casimir correction (Silveirinha 2010).

    Returns δE_asym in J/m².  Positive = asymmetric correction reduces attraction.

        δE_asym = 2·(ħ/2π²c²) · ∫ ξ² dξ ∫ p dp
                    r₁^TM·r₁^TE·r₂^TM·r₂^TE · exp(−4pξd/c)

    Physical consequence for Te|WTe₂:
        δE_asym / δE_sym ≈ 2%  →  κ_crit_asym ≈ 5.8 (unphysical, κ ≤ 1)
    """
    eps_fn1 = lambda xi: epsilon_imaginary(eps_static1, xi, omega_uv)
    eps_fn2 = lambda xi: epsilon_imaginary(eps_static2, xi, omega_uv)

    def outer(xi: float) -> float:
        if xi == 0.0:
            return 0.0
        p_max = min(max(20.0, 2.5 * C / (xi * d)), 1.0e6)
        I, _ = quad(_inner_chiral_asymmetric, 1.0, p_max,
                    args=(xi, eps_fn1, eps_fn2, d),
                    limit=150, epsrel=1e-4)
        return xi ** 2 * I

    xi_max = 10.0 * omega_uv
    raw, _ = quad(outer, 0.0, xi_max, limit=80, epsrel=1e-3, points=[omega_uv])
    prefactor = HBAR / (4.0 * np.pi ** 2 * C ** 2)
    return 2.0 * prefactor * raw


def casimir_energy_chiral_asymmetric(eps_static1: float, eps_static2: float,
                                      d: float, kappa: float = 0.0,
                                      omega_uv: float = OMEGA_UV) -> float:
    """
    Casimir energy with ASYMMETRIC chiral correction (plate 1 chiral only).

    Correct formula for the physical Te | vac | WTe₂ heterostructure where
    Te carries chirality κ and WTe₂ is non-chiral (κ₂ = 0, Silveirinha 2010).

        E(d, κ) = E_Lifshitz(d) + κ² · δE_asym(d)

    Note: δE_asym << δE_sym (≈ 2% ratio).  For Te|WTe₂, κ_crit_asym ≈ 5.8
    lies outside the physical range κ ≤ 1 — chirality-driven repulsion is NOT
    achievable in this heterostructure.  Use casimir_energy_chiral() with a
    symmetric Te|Te geometry for repulsion (κ_crit_sym ≈ 0.806).

    Args:
        eps_static1: Static dielectric of chiral plate (Te, ε_eff ≈ 130–145).
        eps_static2: Static dielectric of non-chiral plate (WTe₂, ε ≈ 8.46).
        d:           Gap separation (m).
        kappa:       Chirality parameter κ = κ₀ · sin(θ).
        omega_uv:    UV oscillator frequency (rad/s).

    Returns:
        Casimir energy per unit area (J/m²).  Negative = attractive.
    """
    E_std = casimir_energy(eps_static1, eps_static2, d, omega_uv)
    if kappa == 0.0:
        return E_std
    delta_E_asym = _casimir_chiral_correction_asymmetric(
        eps_static1, eps_static2, d, omega_uv)
    return E_std + kappa ** 2 * delta_E_asym


def compute_asymmetric_kappa_crit(eps_static1: float, eps_static2: float,
                                   d: float,
                                   omega_uv: float = OMEGA_UV) -> dict:
    """
    Compare symmetric (Zhao 2009) and asymmetric (Silveirinha 2010) κ_crit.

    Returns dict with keys: E_std_Jm2, delta_E_sym_Jm2, delta_E_asym_Jm2,
    ratio_asym_over_sym, kappa_crit_sym, kappa_crit_asym.
    """
    E_std   = casimir_energy(eps_static1, eps_static2, d, omega_uv)
    E_vdw   = casimir_energy_fast(eps_static1, eps_static2, d, kappa=0.0,
                                   omega_uv=omega_uv)
    dE_sym  = -CHIRAL_FACTOR * E_vdw          # δE_sym from fast model
    dE_asym = _casimir_chiral_correction_asymmetric(
                  eps_static1, eps_static2, d, omega_uv)
    kc_sym  = np.sqrt(abs(E_std) / dE_sym)  if dE_sym  > 0 else float("inf")
    kc_asym = np.sqrt(abs(E_std) / dE_asym) if dE_asym > 0 else float("inf")
    return {
        "E_std_Jm2":           E_std,
        "delta_E_sym_Jm2":     dE_sym,
        "delta_E_asym_Jm2":    dE_asym,
        "ratio_asym_over_sym":  dE_asym / dE_sym if dE_sym != 0 else float("nan"),
        "kappa_crit_sym":       kc_sym,
        "kappa_crit_asym":      kc_asym,
    }


# ── Sweep utilities ───────────────────────────────────────────────────────────

def sweep_separation(eps1: float, eps2: float,
                     d_min_nm: float = 1.0, d_max_nm: float = 100.0,
                     n_points: int = 50) -> tuple[np.ndarray, np.ndarray]:
    """E vs d sweep (isotropic, T=0)."""
    d_nm = np.logspace(np.log10(d_min_nm), np.log10(d_max_nm), n_points)
    E    = [casimir_energy(eps1, eps2, d * 1e-9) for d in d_nm]
    return d_nm, np.array(E)


def sweep_separation_aniso(eps_perp1: float, eps_par1: float,
                            eps_perp2: float, eps_par2: float,
                            d_min_nm: float = 1.0, d_max_nm: float = 100.0,
                            n_points: int = 40) -> tuple[np.ndarray, np.ndarray]:
    """E vs d sweep (uniaxial anisotropic, T=0)."""
    d_nm = np.logspace(np.log10(d_min_nm), np.log10(d_max_nm), n_points)
    E    = [casimir_energy_aniso(eps_perp1, eps_par1, eps_perp2, eps_par2, d * 1e-9)
            for d in d_nm]
    return d_nm, np.array(E)


def sweep_separation_2osc(mat1: dict, mat2: dict,
                           d_min_nm: float = 1.0, d_max_nm: float = 100.0,
                           n_points: int = 40) -> tuple[np.ndarray, np.ndarray]:
    """E vs d sweep using 2-oscillator dielectric model."""
    d_nm = np.logspace(np.log10(d_min_nm), np.log10(d_max_nm), n_points)
    E = [casimir_energy_2osc(
            mat1["C1"], mat1["omega1"], mat1["C2"], mat1["omega2"],
            mat2["C1"], mat2["omega1"], mat2["C2"], mat2["omega2"],
            d * 1e-9) for d in d_nm]
    return d_nm, np.array(E)


def sweep_finite_T(eps1: float, eps2: float,
                   T: float = 300.0,
                   d_min_nm: float = 1.0, d_max_nm: float = 2000.0,
                   n_points: int = 40,
                   omega_uv: float = OMEGA_UV) -> tuple[np.ndarray, np.ndarray]:
    """E vs d sweep at finite temperature T (Matsubara summation)."""
    d_nm = np.logspace(np.log10(d_min_nm), np.log10(d_max_nm), n_points)
    E = [casimir_energy_finite_T(eps1, eps2, d * 1e-9, T=T, omega_uv=omega_uv)
         for d in d_nm]
    return d_nm, np.array(E)


def sweep_force(eps1: float, eps2: float,
                d_min_nm: float = 1.0, d_max_nm: float = 100.0,
                n_points: int = 50,
                kappa: float = 0.0,
                omega_uv: float = OMEGA_UV) -> tuple[np.ndarray, np.ndarray]:
    """Force F = -dE/dd sweep (with optional chirality)."""
    d_nm = np.logspace(np.log10(d_min_nm), np.log10(d_max_nm), n_points)
    if kappa == 0.0:
        F = [casimir_force(eps1, eps2, d * 1e-9, omega_uv) for d in d_nm]
    else:
        F = [casimir_force_chiral(eps1, eps2, d * 1e-9, kappa, omega_uv)
             for d in d_nm]
    return d_nm, np.array(F)
