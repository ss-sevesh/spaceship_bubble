"""
lifshitz.py — Lifshitz Casimir energy calculator.

Implements the zero-temperature Lifshitz formula for Casimir interaction
energy per unit area between two planar dielectric half-spaces separated
by a vacuum gap of width d:

    E(d) = (hbar / 4*pi^2 * c^2)
             * int_0^inf xi^2 dxi
             * int_1^inf p dp
             * sum_pol ln(1 - r1^pol * r2^pol * exp(-2*p*xi*d/c))

where:
  - xi is imaginary frequency (Matsubara frequency in the T=0 limit)
  - p = kappa_0 * c / xi >= 1  (normalised perpendicular wavevector)
  - r^TE, r^TM are Fresnel reflection coefficients at imaginary frequency
    for TE and TM polarisation (defined from the vacuum-gap side)

Reflection coefficients at imaginary frequency (both from vacuum side):

    q_i(xi, p) = sqrt(eps_i(i*xi) - 1 + p^2)        [normalised kappa in medium i]

    r_i^TE = (p - q_i) / (p + q_i)                   [< 0 for eps_i > 1]
    r_i^TM = (eps_i * p - q_i) / (eps_i * p + q_i)   [> 0 for eps_i > 1]

Dielectric at imaginary frequency uses the single-oscillator Cauchy model:

    eps(i*xi) = 1 + (eps_static - 1) / (1 + (xi / omega_UV)^2)

References:
    Lifshitz (1956) Sov. Phys. JETP 2, 73.
    Parsegian (2006) Van der Waals Forces. Cambridge UP, ch. 2.
    Dzyaloshinskii, Lifshitz, Pitaevskii (1961) Adv. Phys. 10, 165.
"""

import json
import warnings
import numpy as np
from pathlib import Path
from scipy.integrate import quad
from typing import Callable

# ── Physical constants (SI) ──────────────────────────────────────────────────
HBAR     = 1.0545718e-34   # J*s   — reduced Planck constant
C        = 2.99792458e8    # m/s   — speed of light in vacuum
KB       = 1.380649e-23    # J/K   — Boltzmann constant
OMEGA_UV = 2.0e16          # rad/s — UV pole ~13 eV (typical semiconductor)


def epsilon_imaginary_drude_lorentz(xi: float, omega_p: float, gamma: float,
                                     eps_inf: float,
                                     omega_uv: float = OMEGA_UV) -> float:
    """
    Combined Drude + single-Lorentz model for semimetals/metals at imaginary freq.

    Appropriate for Td-WTe₂ (type-II Weyl semimetal) which has both free-carrier
    (Drude) and interband (Lorentz) contributions:

        eps(i*xi) = eps_inf / (1 + (xi/omega_UV)^2)   [Lorentz / interband]
                  + omega_p^2 / (xi*(xi + gamma))      [Drude / free carrier]

    At xi -> 0:  Drude term diverges -> metal.
    At xi >> gamma, xi << omega_UV:  eps -> eps_inf (electronic dielectric).
    At xi >> omega_UV:  eps -> 1 (vacuum limit).

    Note on eps_inf: use only the ELECTRONIC (interband) dielectric constant,
    NOT the full static value.  The Drude term already accounts for free carriers.

    Td-WTe2 parameters (from DFT-HSE06 + literature):
        omega_p  = 1.0e15 rad/s  (~0.66 eV, Weyl-pocket plasma frequency)
        gamma    = 5.0e13 rad/s  (Drude damping from residual resistivity)
        eps_inf  = 13.63         (electronic dielectric, td_wte2_dft.json)
        omega_uv = 2.0e16 rad/s  (UV interband cutoff)

    References:
        Soluyanov et al., Nature 527, 495 (2015) — Td-WTe2 band structure
        Wu et al., Phys. Rev. B 95, 085128 (2017) — optical conductivity of WTe2
        Lambrecht & Reynaud, Eur. Phys. J. D 8, 309 (2000) — Drude model form

    Args:
        xi:       Imaginary frequency (rad/s); must be > 0.
        omega_p:  Plasma frequency (rad/s).
        gamma:    Drude damping rate (rad/s).
        eps_inf:  High-frequency (electronic) dielectric constant.
        omega_uv: UV Lorentz pole frequency (rad/s).

    Returns:
        Real-valued eps(i*xi) >= 1.
    """
    if xi <= 0.0:
        xi = 1.0e-10 * gamma   # regularise xi=0 pole
    drude   = omega_p ** 2 / (xi * (xi + gamma))
    lorentz = (eps_inf - 1.0) / (1.0 + (xi / omega_uv) ** 2)
    return 1.0 + drude + lorentz


def epsilon_imaginary_drude(xi: float, omega_p: float, gamma: float) -> float:
    """
    Drude-model dielectric at imaginary frequency i*xi for free-electron metals.

        eps_Drude(i*xi) = 1 + omega_p^2 / (xi * (xi + gamma))

    At xi >> gamma:  eps -> 1 + (omega_p/xi)^2  (plasma contribution).
    At xi << gamma:  eps -> 1 + omega_p^2/(gamma*xi) -> large (metallic).
    At xi -> 0:      diverges (metallic pole); the outer integrand returns 0
                     at xi=0 so this limit is never evaluated in practice.

    Reference:
        Lambrecht, A. & Reynaud, S. (2000). Eur. Phys. J. D 8, 309-318.
        Gold parameters: omega_p = 1.37e16 rad/s, gamma = 5.32e13 rad/s.
        Also: Decca, R.S. et al. (2007). Phys. Rev. D 75, 077101.

    Args:
        xi:      Imaginary frequency (rad/s); must be > 0.
        omega_p: Plasma frequency (rad/s).  Au: 1.37e16.
        gamma:   Drude damping rate (rad/s). Au: 5.32e13.

    Returns:
        Real-valued eps(i*xi) >= 1.
    """
    if xi <= 0.0:
        xi = 1.0e-10 * gamma   # regularise pole; xi=0 is skipped by _outer_integrand
    return 1.0 + omega_p ** 2 / (xi * (xi + gamma))


# Drude parameters for gold — Lambrecht & Reynaud (2000); Decca et al. (2007)
AU_DRUDE = dict(omega_p=1.37e16, gamma=5.32e13)


def epsilon_imaginary(eps_static: float, xi: float,
                      omega_uv: float = OMEGA_UV) -> float:
    """
    Single-oscillator Cauchy model for dielectric function at imaginary freq i*xi.

        eps(i*xi) = 1 + (eps0 - 1) / (1 + (xi / omega_UV)^2)

    Satisfies Kramers-Kronig causality; monotonically decreasing in xi.

    Args:
        eps_static: Static (zero-frequency) dielectric constant eps0.
        xi:         Imaginary frequency xi (rad/s), must be >= 0.
        omega_uv:   UV pole frequency (rad/s).

    Returns:
        Real-valued eps(i*xi) >= 1.
    """
    return 1.0 + (eps_static - 1.0) / (1.0 + (xi / omega_uv) ** 2)


def _reflection_te(eps_i: float, p: float) -> float:
    """
    TE Fresnel reflection amplitude at imaginary frequency (vacuum side).

        r^TE = (p - q_i) / (p + q_i),   q_i = sqrt(eps_i - 1 + p^2)

    Args:
        eps_i: Dielectric of medium i at imaginary frequency.
        p:     Normalised perpendicular wavevector kappa_0*c/xi >= 1.

    Returns:
        r^TE; negative for eps_i > 1.
    """
    q = np.sqrt(eps_i - 1.0 + p ** 2)
    return (p - q) / (p + q)


def _reflection_tm(eps_i: float, p: float) -> float:
    """
    TM Fresnel reflection amplitude at imaginary frequency (vacuum side).

        r^TM = (eps_i*p - q_i) / (eps_i*p + q_i),   q_i = sqrt(eps_i - 1 + p^2)

    Args:
        eps_i: Dielectric of medium i at imaginary frequency.
        p:     Normalised perpendicular wavevector kappa_0*c/xi >= 1.

    Returns:
        r^TM; positive for eps_i > 1.
    """
    q = np.sqrt(eps_i - 1.0 + p ** 2)
    return (eps_i * p - q) / (eps_i * p + q)


def _inner_integrand_te(p: float, xi: float,
                         eps_fn1: Callable, eps_fn2: Callable,
                         d: float) -> float:
    """
    Inner (p) integrand for TE contribution at fixed xi.

    Args:
        p:       Normalised wavevector (>= 1).
        xi:      Imaginary frequency (rad/s).
        eps_fn1: Callable eps1(xi).
        eps_fn2: Callable eps2(xi).
        d:       Gap separation (m).

    Returns:
        p * ln(1 - r1^TE * r2^TE * exp(-2*p*xi*d/c)).
    """
    e1 = eps_fn1(xi)
    e2 = eps_fn2(xi)
    r1 = _reflection_te(e1, p)
    r2 = _reflection_te(e2, p)
    arg = r1 * r2 * np.exp(-2.0 * p * xi * d / C)
    if arg >= 1.0:
        return 0.0
    return p * np.log(1.0 - arg)


def _inner_integrand_tm(p: float, xi: float,
                         eps_fn1: Callable, eps_fn2: Callable,
                         d: float) -> float:
    """
    Inner (p) integrand for TM contribution at fixed xi.

    Args:
        p:       Normalised wavevector (>= 1).
        xi:      Imaginary frequency (rad/s).
        eps_fn1: Callable eps1(xi).
        eps_fn2: Callable eps2(xi).
        d:       Gap separation (m).

    Returns:
        p * ln(1 - r1^TM * r2^TM * exp(-2*p*xi*d/c)).
    """
    e1 = eps_fn1(xi)
    e2 = eps_fn2(xi)
    r1 = _reflection_tm(e1, p)
    r2 = _reflection_tm(e2, p)
    arg = r1 * r2 * np.exp(-2.0 * p * xi * d / C)
    if arg >= 1.0:
        return 0.0
    return p * np.log(1.0 - arg)


def _outer_integrand(xi: float,
                     eps_fn1: Callable, eps_fn2: Callable,
                     d: float) -> float:
    """
    Outer (xi) integrand: integrate inner integrand over p in [1, p_max].

    The exponential factor exp(-2*p*xi*d/c) suppresses the integrand for
    p >> c/(xi*d); we truncate at p_max = 20 for efficiency.

    Args:
        xi:      Imaginary frequency (rad/s).
        eps_fn1: Callable eps1(xi).
        eps_fn2: Callable eps2(xi).
        d:       Gap separation (m).

    Returns:
        xi^2 * (I_TE + I_TM) where I_TE, I_TM are the p-integrals.
    """
    if xi == 0.0:
        return 0.0

    p_max = min(max(20.0, 5.0 * C / (xi * d)), 1.0e6)  # clamped; evanescent tail is 0 beyond c/(xi*d)

    I_te, _ = quad(_inner_integrand_te, 1.0, p_max,
                   args=(xi, eps_fn1, eps_fn2, d),
                   limit=200, epsrel=1e-5)
    I_tm, _ = quad(_inner_integrand_tm, 1.0, p_max,
                   args=(xi, eps_fn1, eps_fn2, d),
                   limit=200, epsrel=1e-5)

    return xi ** 2 * (I_te + I_tm)


def casimir_energy(eps_static1: float, eps_static2: float, d: float,
                   omega_uv: float = OMEGA_UV) -> float:
    """
    Compute Lifshitz-Casimir energy per unit area E(d) in J/m^2.

    Full double integral (TE + TM) over imaginary frequency and
    normalised perpendicular wavevector:

        E(d) = (hbar / 4*pi^2 * c^2)
                 * int_0^xi_max xi^2 dxi
                 * int_1^p_max p dp
                 * [ln(1 - r1^TE r2^TE e^{-2pxid/c})
                  + ln(1 - r1^TM r2^TM e^{-2pxid/c})]

    Args:
        eps_static1: Static dielectric of material 1.
        eps_static2: Static dielectric of material 2.
        d:           Gap separation (m); must be > 0.
        omega_uv:    UV oscillator frequency for Cauchy model (rad/s).

    Returns:
        Casimir energy per unit area (J/m^2).  Negative = attractive.
    """
    eps_fn1 = lambda xi: epsilon_imaginary(eps_static1, xi, omega_uv)
    eps_fn2 = lambda xi: epsilon_imaginary(eps_static2, xi, omega_uv)

    # Upper limit: integrand negligible beyond ~10 * omega_UV
    xi_max = 10.0 * omega_uv

    result, _ = quad(
        _outer_integrand,
        0.0, xi_max,
        args=(eps_fn1, eps_fn2, d),
        limit=100,
        epsabs=1e-60,
        epsrel=1e-4,
        points=[omega_uv],   # hint: peak of dielectric dispersion
    )

    prefactor = HBAR / (4.0 * np.pi ** 2 * C ** 2)
    return prefactor * result


def load_eps_static(json_path: Path) -> float:
    """
    Extract isotropic static dielectric constant from a material JSON file.

    Uses the trace-average of the e_total_tensor diagonal as eps_0;
    falls back to the scalar e_total field if tensor is absent.

    Args:
        json_path: Path to material JSON (as saved by fetch_materials.py).

    Returns:
        Scalar static dielectric constant.
    """
    with open(json_path) as f:
        data = json.load(f)
    if "e_total_tensor" in data:
        tensor = np.array(data["e_total_tensor"])
        return float(np.trace(tensor) / 3.0)
    return float(data["e_total"])


def sweep_separation(eps1: float, eps2: float,
                     d_min_nm: float = 1.0, d_max_nm: float = 100.0,
                     n_points: int = 50) -> tuple[np.ndarray, np.ndarray]:
    """
    Compute Casimir energy over a range of separations.

    Args:
        eps1:      Static dielectric of material 1.
        eps2:      Static dielectric of material 2.
        d_min_nm:  Minimum separation in nanometres.
        d_max_nm:  Maximum separation in nanometres.
        n_points:  Number of sample points (log-spaced for d^-2 physics).

    Returns:
        Tuple (d_nm, E_Jm2) — separation array (nm) and energy array (J/m^2).
    """
    d_nm = np.logspace(np.log10(d_min_nm), np.log10(d_max_nm), n_points)
    E = []
    for i, d in enumerate(d_nm):
        e = casimir_energy(eps1, eps2, d * 1e-9)
        E.append(e)
        if (i + 1) % 10 == 0:
            print(f"    {i+1}/{n_points}  d={d:.1f} nm  E={e:.4e} J/m^2")
    return d_nm, np.array(E)


# ─────────────────────────────────────────────────────────────────────────────
# Chiral Casimir correction
# ─────────────────────────────────────────────────────────────────────────────

def _hamaker_constant(eps1: float, eps2: float,
                      omega_uv: float = OMEGA_UV) -> float:
    """
    Non-retarded Hamaker constant for two dielectric slabs across vacuum.

    Uses the London single-frequency approximation:

        A = (3 * hbar * omega_UV / (4 * sqrt(2))) * beta1 * beta2

    where beta_i = (eps_i - 1) / (eps_i + 1).

    Args:
        eps1:      Static dielectric of slab 1.
        eps2:      Static dielectric of slab 2.
        omega_uv:  UV absorption frequency (rad/s).

    Returns:
        Hamaker constant A (J).  Positive -> attractive vdW potential.
    """
    beta1 = (eps1 - 1.0) / (eps1 + 1.0)
    beta2 = (eps2 - 1.0) / (eps2 + 1.0)
    return (3.0 * HBAR * omega_uv / (4.0 * np.sqrt(2.0))) * beta1 * beta2


# Chiral Casimir factor — derivation and calibration
# ─────────────────────────────────────────────────────────────────────────────
# The leading-order chiral correction to the Lifshitz energy is (Zhao et al.
# 2009, Phys. Rev. Lett. 103, 103602; Bimonte et al. 2009, Phys. Rev. A 79,
# 042906):
#
#     E(d, kappa) = E_Lifshitz(d)  +  kappa^2 * delta_E(d)
#
# where delta_E arises from TE-TM cross-coupling in chiral media:
#
#     delta_E = -(hbar/4pi^2 c^2) * int_0^inf xi^2 dxi
#                * int_1^inf p dp
#                * 2*(r1^TM*r2^TE + r1^TE*r2^TM) * exp(-2*p*xi*d/c)
#
# This is implemented exactly in `_casimir_chiral_correction()` and
# `casimir_energy_chiral()`.
#
# For the fast Hamaker approximation used in the NSGA-II inner loop, we
# factor out E_vdw and write:
#
#     E_fast(d, kappa) = E_vdw(d) * (1 - CHIRAL_FACTOR * kappa^2)
#
# CHIRAL_FACTOR calibration — numerically verified by compute_chiral_factor_ratio():
#
#   chi(d) = delta_E(d) / |E_vdW(d)|
#   where delta_E uses the corrected prefactor ħ/(4π²c²) and E_vdW uses Hamaker.
#
#   Te|Te (symmetric, eps1=eps2=164.27):
#     d=5 nm  -> chi=1.70   d=10 nm -> chi=1.19
#     d=20 nm -> chi=0.70   d=50 nm -> chi=0.30
#
#   Te|WTe2 (heterostructure, eps1=164.27, eps2=6.16):
#     d=5 nm  -> chi=0.75   d=10 nm -> chi=0.64
#     d=20 nm -> chi=0.43   d=50 nm -> chi=0.20
#
# CHIRAL_FACTOR = 1.0 is a conservative upper bound close to the Te|Te ratio
# at d ≈ 8–10 nm (chi≈1.2).  For the optimizer's Te|WTe2 heterostructure it
# overestimates chi at all separations, biasing NSGA-II toward higher kappa_eff
# (conservative / robust design choice).
#
# Critical chirality in the fast model: kappa_c = 1/sqrt(CHIRAL_FACTOR) = 1.0.
# Note: chi values are halved relative to the pre-fix calibration because
# delta_E (from the full Lifshitz integral) scales with the prefactor correction
# while E_vdW (Hamaker) does not.
#
# NOTE: Publication-quality curves use casimir_energy_chiral() which integrates
# the full TE-TM cross-coupling with no empirical prefactor.  CHIRAL_FACTOR is
# only used in the fast-model inner loop of the NSGA-II optimizer.
# For the Te|WTe₂ asymmetric heterostructure the correct formula (Silveirinha
# 2010) gives χ_asym ≈ 2% of χ_sym; use casimir_energy_chiral_asymmetric()
# for physical Te|WTe₂ results (κ_crit_asym ≈ 6.3, repulsion not achievable).
CHIRAL_FACTOR = 1.0   # dimensionless kappa^2 coefficient in Hamaker fast model


def compute_chiral_factor_ratio(eps_static1: float = 164.27,
                                 eps_static2: float = 6.16,
                                 d_nm_list: list | None = None,
                                 omega_uv: float = OMEGA_UV) -> dict:
    """
    Numerically verify CHIRAL_FACTOR by computing delta_E / |E_vdW| at
    several separations for a given material pair.

    This provides transparency for the calibrated CHIRAL_FACTOR = 1.0 used
    in the fast optimizer (casimir_energy_fast).  Numerically verified values
    (corrected prefactor ħ/(4π²c²)):
      Te|Te:   chi = 1.70 (d=5nm), 1.19 (d=10nm), 0.70 (d=20nm), 0.30 (d=50nm)
      Te|WTe₂: chi = 0.75 (d=5nm), 0.64 (d=10nm), 0.43 (d=20nm), 0.20 (d=50nm)
    CHIRAL_FACTOR = 1.0 is a conservative upper-bound close to Te|Te at d≈8nm.
    For Te|WTe₂ it overestimates chi, biasing NSGA-II toward higher kappa_eff.

    The cross-coupling integral is (Zhao et al. 2009, PRL 103, 103602):
        delta_E(d) = -2*(ħ/4π²c²) ∫ ξ² dξ ∫ p dp
                     (r₁^TM·r₂^TE + r₁^TE·r₂^TM) exp(-2pξd/c)

    The Hamaker fast-model approximates this as:
        delta_E_fast(d) ≈ CHIRAL_FACTOR × |E_vdW(d)|
    where E_vdW = -A/(12πd²) is the non-retarded vdW energy.

    Args:
        eps_static1: Static dielectric of material 1 (default: Te, 164.27).
        eps_static2: Static dielectric of material 2 (default: WTe₂, 6.16).
        d_nm_list:   List of separations in nm to evaluate (default: [5, 10, 20]).
        omega_uv:    UV pole frequency for Cauchy model (rad/s).

    Returns:
        Dict mapping d_nm (float) -> dict with keys:
          'delta_E_Jm2'  — full Lifshitz kappa^2 coefficient (J/m²)
          'E_vdW_Jm2'    — Hamaker non-retarded energy (J/m²)
          'ratio'        — delta_E / |E_vdW|  (compare to CHIRAL_FACTOR)
    """
    if d_nm_list is None:
        d_nm_list = [5.0, 10.0, 20.0]

    A_ham = _hamaker_constant(eps_static1, eps_static2, omega_uv)
    results: dict = {}
    for d_nm in d_nm_list:
        d = d_nm * 1e-9
        delta_E = _casimir_chiral_correction(eps_static1, eps_static2, d, omega_uv)
        E_vdW   = -A_ham / (12.0 * np.pi * d ** 2)
        ratio   = delta_E / abs(E_vdW)
        results[d_nm] = {
            "delta_E_Jm2": delta_E,
            "E_vdW_Jm2":   E_vdW,
            "ratio":        ratio,
        }
    return results


def casimir_energy_fast(eps1: float, eps2: float, d: float,
                        kappa: float = 0.0,
                        omega_uv: float = OMEGA_UV) -> float:
    """
    Fast Casimir energy approximation for optimization (Hamaker + chiral factor).

    Uses the non-retarded London-Hamaker formula calibrated to the full
    Lifshitz chiral integral:

        E = -A / (12 * pi * d^2) * (1 - CHIRAL_FACTOR * kappa^2)

    Physical interpretation:
      - kappa = 0               -> standard van der Waals attraction
      - kappa = 1/sqrt(chi)     -> zero Casimir force (critical chirality)
      - kappa > 1/sqrt(chi)     -> chiral repulsion (sign change)
      - kappa = kappa0 * sin(theta) * (N_layers / N_layers_max)

    CHIRAL_FACTOR = 1.0 is calibrated to the full Lifshitz chiral integral
    with the corrected prefactor ħ/(4π²c²) (delta_E / |E_vdw| ≈ 1.2 at
    d = 10 nm for Te | vac | Te).

    Fast-model critical chirality: kappa_critical_fast = 1/sqrt(CHIRAL_FACTOR) = 1.0.
    This is the FAST MODEL estimate only — the exact Lifshitz integral gives
    kappa_crit(Te|Te, d=10 nm) ≈ 0.795 and kappa_crit(Te|Te, d=84 nm) ≈ 0.775.
    Never use kappa_critical = 1.0 as the exact value in publication results.

    NOTE: phenomenological approximation for the optimizer inner loop.
    Use casimir_energy_chiral() for exact symmetric (Te|Te) results.
    Use casimir_energy_chiral_asymmetric() for Te|WTe₂ results.

    Args:
        eps1:      Static dielectric of material 1.
        eps2:      Static dielectric of material 2.
        d:         Gap separation (m).
        kappa:     Effective chirality parameter (dimensionless, >= 0).
        omega_uv:  UV oscillator frequency (rad/s).

    Returns:
        Approximate Casimir energy per unit area (J/m^2).
        Negative = attractive, positive = chiral repulsion.
    """
    A = _hamaker_constant(eps1, eps2, omega_uv)
    E_vdw = -A / (12.0 * np.pi * d ** 2)
    return E_vdw * (1.0 - CHIRAL_FACTOR * kappa ** 2)


def _inner_chiral(p: float, xi: float,
                  eps_fn1: Callable, eps_fn2: Callable,
                  d: float) -> float:
    """
    Inner integrand for the leading-order chiral Casimir correction.

    Computes the TE-TM cross-coupling product (kappa^2 coefficient):

        p * (r1^TM * r2^TE + r1^TE * r2^TM) * exp(-2*p*xi*d/c)

    For identical chiral media: r1^TM = r2^TM > 0, r1^TE = r2^TE < 0,
    so the integrand is negative -> delta_E > 0 after sign flip in
    _casimir_chiral_correction, reducing |E_Casimir| (chiral repulsion).

    Args:
        p:       Normalised wavevector (>= 1).
        xi:      Imaginary frequency (rad/s).
        eps_fn1: Callable eps1(xi).
        eps_fn2: Callable eps2(xi).
        d:       Gap separation (m).

    Returns:
        Integrand value (dimensionless * xi^2 factor applied in outer loop).
    """
    e1 = eps_fn1(xi)
    e2 = eps_fn2(xi)
    rTE1 = _reflection_te(e1, p)
    rTM1 = _reflection_tm(e1, p)
    rTE2 = _reflection_te(e2, p)
    rTM2 = _reflection_tm(e2, p)
    cross = rTM1 * rTE2 + rTE1 * rTM2
    return p * cross * np.exp(-2.0 * p * xi * d / C)


def _casimir_chiral_correction(eps_static1: float, eps_static2: float,
                                d: float,
                                omega_uv: float = OMEGA_UV) -> float:
    """
    Compute the kappa^2 coefficient of the chiral Casimir energy correction.

    The total chiral energy is:
        E_chiral(d, kappa) = E_Lifshitz(d) + kappa^2 * delta_E(d)

    where delta_E > 0 (reduces attraction for same-handedness).

    Computing delta_E separately allows efficient sweeps over kappa or theta
    without repeating the expensive integral.

    Physical formula (leading order, Zhao et al. 2009):
        delta_E = -2 * (hbar / 4*pi^2*c^2) * int xi^2 dxi int p dp
                    (r1^TM*r2^TE + r1^TE*r2^TM) * exp(-2pxid/c)

    Args:
        eps_static1: Static dielectric of material 1.
        eps_static2: Static dielectric of material 2.
        d:           Gap separation (m).
        omega_uv:    UV oscillator frequency (rad/s).

    Returns:
        delta_E in J/m^2.  Positive = chiral correction reduces attraction.
    """
    eps_fn1 = lambda xi: epsilon_imaginary(eps_static1, xi, omega_uv)
    eps_fn2 = lambda xi: epsilon_imaginary(eps_static2, xi, omega_uv)

    def outer(xi: float) -> float:
        if xi == 0.0:
            return 0.0
        p_max = min(max(20.0, 5.0 * C / (xi * d)), 1.0e6)
        integral_val, _ = quad(_inner_chiral, 1.0, p_max,
                    args=(xi, eps_fn1, eps_fn2, d),
                    limit=200, epsrel=1e-4)
        return xi ** 2 * integral_val

    xi_max = 10.0 * omega_uv
    # epsrel=1e-3 (looser than main Lifshitz 1e-4): acceptable because δE ~ κ²×E_base
    # is a small correction; tighter tolerance offers no benefit at this perturbative level.
    raw, _ = quad(outer, 0.0, xi_max, limit=80, epsrel=1e-3, points=[omega_uv])

    prefactor = HBAR / (4.0 * np.pi ** 2 * C ** 2)
    # Negative of raw (cross term is negative) * 2 per chiral formula
    return -2.0 * prefactor * raw


def casimir_energy_chiral(eps_static1: float, eps_static2: float,
                           d: float, kappa: float = 0.0,
                           omega_uv: float = OMEGA_UV) -> float:
    """
    Casimir energy with chiral TE-TM correction (full Lifshitz + kappa^2 term).

    E(d, kappa) = E_Lifshitz(d) + kappa^2 * delta_E(d)

    where:
      - E_Lifshitz: standard TE+TM Lifshitz double integral
      - delta_E:    kappa^2 coefficient from TE-TM cross-mode coupling
      - kappa = kappa0 * sin(theta)  for a chiral metamaterial at angle theta

    For two identical chiral slabs: delta_E > 0, so increasing kappa reduces
    |E| and can drive the Casimir force repulsive (Dzyaloshinskii-Zhao mechanism).

    NOTE: This function uses the SYMMETRIC chiral formula (Zhao et al. 2009,
    PRL 103, 103602), which assumes both plates carry chirality kappa.  For the
    physical Te|WTe₂ heterostructure where only plate 1 (Te) is chiral (kappa != 0)
    and plate 2 (WTe₂) is a non-chiral anisotropic crystal (kappa2 = 0), use
    casimir_energy_chiral_asymmetric() instead, which implements the correct
    second-order scattering formula (Silveirinha 2010, Phys. Rev. B 82, 085101).

    Args:
        eps_static1: Static dielectric of material 1.
        eps_static2: Static dielectric of material 2.
        d:           Gap separation (m).
        kappa:       Chirality parameter kappa = kappa0 * sin(theta).
        omega_uv:    UV oscillator frequency (rad/s).

    Returns:
        Casimir energy per unit area (J/m^2).  Negative = attractive.
    """
    E_std = casimir_energy(eps_static1, eps_static2, d, omega_uv)
    if kappa == 0.0:
        return E_std
    delta_E = _casimir_chiral_correction(eps_static1, eps_static2, d, omega_uv)
    return E_std + kappa ** 2 * delta_E


# ─────────────────────────────────────────────────────────────────────────────
# Asymmetric chiral Casimir correction (plate 1 chiral, plate 2 non-chiral)
# ─────────────────────────────────────────────────────────────────────────────
#
# Physical derivation — Silveirinha (2010), Phys. Rev. B 82, 085101:
#
# For the Te(κ₁≠0) | vac | WTe₂(κ₂=0) system the Zhao 2009 leading-order
# term vanishes because it is proportional to κ₁·κ₂ (round-trip mode mixing
# requires chirality on BOTH sides).  The correct leading correction enters at
# order κ₁² from two successive TE↔TM scatterings at the chiral plate during a
# single round trip.  Expanding the round-trip matrix M̂ = R₁·e^{-kd}·R₂·e^{-kd}
# about the non-chiral diagonal part M̂₀ and collecting the κ₁² contribution
# from −½ Tr(M̂₁²) in the log expansion:
#
#   δE_asym = 2 · (ħ/4π²c²)
#             × ∫₀^∞ ξ² dξ ∫₁^∞ p dp
#             × r₁^TM(ε₁,p) · r₁^TE(ε₁,p) · r₂^TM(ε₂,p) · r₂^TE(ε₂,p)
#             × exp(−4·p·ξ·d/c)
#
# Sign:  r^TM > 0, r^TE < 0  for ε > 1, so the four-fold product is positive.
# The prefactor gives δE_asym > 0 → reduces attraction for increasing κ₁. ✓
#
# Key difference from symmetric formula:
#   Symmetric:  integrand ∝ (r₁^TM·r₂^TE + r₁^TE·r₂^TM)·exp(−2d)  [one round trip]
#   Asymmetric: integrand ∝ r₁^TM·r₁^TE·r₂^TM·r₂^TE·exp(−4d)       [two round trips]
#
# The extra exp(−2d) factor makes δE_asym << δE_sym at all MEMS-relevant
# separations, leading to a higher κ_crit for the physical heterostructure.
#
# Reference:
#   Silveirinha, M. G. (2010). Phys. Rev. B 82, 085101.
#   Bimonte, G. et al. (2009). Phys. Rev. A 79, 042906.

def _inner_chiral_asymmetric(p: float, xi: float,
                              eps_fn1: Callable, eps_fn2: Callable,
                              d: float) -> float:
    """
    Inner integrand for the asymmetric chiral Casimir correction.

    Computes the four-amplitude product (κ₁² coefficient) for the case where
    only plate 1 is chiral (κ₂ = 0):

        p · r₁^TM · r₁^TE · r₂^TM · r₂^TE · exp(−4·p·ξ·d/c)

    Both (r^TM · r^TE) factors are negative for ε > 1, so the product is
    positive → δE_asym > 0 after the prefactor (reduces attraction). ✓

    Args:
        p:       Normalised wavevector (>= 1).
        xi:      Imaginary frequency (rad/s).
        eps_fn1: Callable eps1(xi) — chiral plate (Te).
        eps_fn2: Callable eps2(xi) — non-chiral plate (WTe₂).
        d:       Gap separation (m).

    Returns:
        Integrand value (xi^2 factor applied in outer loop).
    """
    e1 = eps_fn1(xi)
    e2 = eps_fn2(xi)
    rTE1 = _reflection_te(e1, p)
    rTM1 = _reflection_tm(e1, p)
    rTE2 = _reflection_te(e2, p)
    rTM2 = _reflection_tm(e2, p)
    # Four-fold product: (r^TM·r^TE)₁ × (r^TM·r^TE)₂ — positive for ε > 1
    product = rTM1 * rTE1 * rTM2 * rTE2
    return p * product * np.exp(-4.0 * p * xi * d / C)


def _casimir_chiral_correction_asymmetric(eps_static1: float, eps_static2: float,
                                           d: float,
                                           omega_uv: float = OMEGA_UV) -> float:
    """
    Compute the κ² coefficient of the asymmetric chiral Casimir correction.

    Valid for the physical Te(κ≠0) | vac | WTe₂(κ=0) configuration.
    Implements the second-order scattering formula of Silveirinha (2010).

    The total chiral energy is:
        E_chiral(d, κ) = E_Lifshitz(d) + κ² · δE_asym(d)

    where δE_asym > 0 (reduces attraction; can drive repulsion for large κ).

    Physical formula (asymmetric, Silveirinha 2010 Eq. 15):
        δE_asym = 2 · (ħ/4π²c²) · ∫ ξ² dξ ∫ p dp
                    r₁^TM·r₁^TE·r₂^TM·r₂^TE · exp(−4pξd/c)

    Args:
        eps_static1: Static dielectric of chiral plate (Te).
        eps_static2: Static dielectric of non-chiral plate (WTe₂).
        d:           Gap separation (m).
        omega_uv:    UV oscillator frequency (rad/s).

    Returns:
        δE_asym in J/m².  Positive = asymmetric chiral correction reduces attraction.
    """
    eps_fn1 = lambda xi: epsilon_imaginary(eps_static1, xi, omega_uv)
    eps_fn2 = lambda xi: epsilon_imaginary(eps_static2, xi, omega_uv)

    def outer(xi: float) -> float:
        if xi == 0.0:
            return 0.0
        # p_max: exponential exp(-4pξd/c) suppresses integrand even faster
        p_max = min(max(20.0, 2.5 * C / (xi * d)), 1.0e6)
        integral_val, _ = quad(_inner_chiral_asymmetric, 1.0, p_max,
                    args=(xi, eps_fn1, eps_fn2, d),
                    limit=150, epsrel=1e-4)
        return xi ** 2 * integral_val

    xi_max = 10.0 * omega_uv
    raw, _ = quad(outer, 0.0, xi_max, limit=80, epsrel=1e-3, points=[omega_uv])

    prefactor = HBAR / (4.0 * np.pi ** 2 * C ** 2)
    # raw > 0 (four-fold product positive), delta_E_asym = +2 * prefactor * raw > 0
    return 2.0 * prefactor * raw


def casimir_energy_chiral_asymmetric(eps_static1: float, eps_static2: float,
                                      d: float, kappa: float = 0.0,
                                      omega_uv: float = OMEGA_UV) -> float:
    """
    Casimir energy with ASYMMETRIC chiral correction (plate 1 chiral only).

    Correct formula for the physical Te | vac | WTe₂ heterostructure where
    Te carries chirality κ and WTe₂ is a non-chiral anisotropic crystal (κ₂=0).

    E(d, κ) = E_Lifshitz(d) + κ² · δE_asym(d)

    where δE_asym is from the second-order scattering formula (Silveirinha 2010),
    NOT the Zhao 2009 symmetric formula used in casimir_energy_chiral().

    Physical consequence:
    - δE_asym << δE_sym at all separations (extra exp(−2d) suppression)
    - κ_crit_asym = sqrt(|E_Lifshitz| / δE_asym) ≈ 6.3, far outside physical range
    - κ_crit_sym reference values (Zhao formula — exact for symmetric Te|Te geometry):
        d=10 nm → 0.795;  d=84 nm → 0.775  (NOT ≈ 0.826; that figure is for the
        Zhao formula incorrectly applied to Te|WTe₂ at d=84.2 nm — see IEEE §V.B)
    - Repulsion requires κ_eff > κ_crit_asym; impossible for physical κ ≤ 1

    Args:
        eps_static1: Static dielectric of chiral plate (Te, ε_eff ≈ 164.27).
        eps_static2: Static dielectric of non-chiral plate (WTe₂, ε ≈ 6.16).
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
    Compute κ_crit and comparison ratio for the asymmetric Te|WTe₂ configuration.

    Reports:
      - δE_sym:   symmetric (Zhao 2009) correction coefficient [J/m²]
      - δE_asym:  asymmetric (Silveirinha 2010) correction coefficient [J/m²]
      - ratio:    δE_asym / δE_sym  (suppression factor due to asymmetry)
      - kappa_crit_sym:   sqrt(|E_std| / δE_sym)  [Zhao 2009]
      - kappa_crit_asym:  sqrt(|E_std| / δE_asym) [correct asymmetric]
      - E_std:    standard Lifshitz energy [J/m²]

    Args:
        eps_static1: Static dielectric of chiral plate (Te).
        eps_static2: Static dielectric of non-chiral plate (WTe₂).
        d:           Gap separation (m).
        omega_uv:    UV oscillator frequency (rad/s).

    Returns:
        Dict with keys: E_std, delta_E_sym, delta_E_asym, ratio,
                        kappa_crit_sym, kappa_crit_asym.
    """
    E_std      = casimir_energy(eps_static1, eps_static2, d, omega_uv)
    dE_sym     = _casimir_chiral_correction(eps_static1, eps_static2, d, omega_uv)
    dE_asym    = _casimir_chiral_correction_asymmetric(
                     eps_static1, eps_static2, d, omega_uv)
    kc_sym  = np.sqrt(abs(E_std) / dE_sym)  if dE_sym  > 0 else float("inf")
    kc_asym = np.sqrt(abs(E_std) / dE_asym) if dE_asym > 0 else float("inf")
    return {
        "E_std_Jm2":       E_std,
        "delta_E_sym_Jm2":  dE_sym,
        "delta_E_asym_Jm2": dE_asym,
        "ratio_asym_over_sym": dE_asym / dE_sym if dE_sym != 0 else float("nan"),
        "kappa_crit_sym":   kc_sym,
        "kappa_crit_asym":  kc_asym,
    }


def sweep_chiral(eps_static1: float, eps_static2: float,
                 d: float, kappa0_list: list[float],
                 n_theta: int = 60,
                 omega_uv: float = OMEGA_UV) -> tuple[np.ndarray, dict]:
    """
    Sweep Casimir energy vs theta for several kappa0 values at fixed d.

    Efficiently reuses E_std and delta_E (computed once) for all curves.

    E(theta, kappa0) = E_std + (kappa0 * sin(theta))^2 * delta_E

    Args:
        eps_static1: Static dielectric of material 1.
        eps_static2: Static dielectric of material 2.
        d:           Fixed gap separation (m).
        kappa0_list: List of intrinsic chirality amplitudes to sweep.
        n_theta:     Number of theta sample points in [0, pi/2].
        omega_uv:    UV oscillator frequency (rad/s).

    Returns:
        (theta_arr, results) where theta_arr is shape (n_theta,) and
        results is dict {kappa0: E_array (J/m^2)}.
    """
    print(f"  Computing E_std at d={d*1e9:.1f} nm...")
    E_std = casimir_energy(eps_static1, eps_static2, d, omega_uv)
    print(f"    E_std = {E_std:.4e} J/m^2")

    print("  Computing chiral correction integral (delta_E)...")
    delta_E = _casimir_chiral_correction(eps_static1, eps_static2, d, omega_uv)
    print(f"    delta_E = {delta_E:.4e} J/m^2  (kappa^2 coefficient)")

    theta = np.linspace(0.0, np.pi / 2.0, n_theta)
    results: dict = {}
    for k0 in kappa0_list:
        kappa_arr = k0 * np.sin(theta)
        results[k0] = E_std + kappa_arr ** 2 * delta_E

    return theta, results


# ─────────────────────────────────────────────────────────────────────────────
# Anisotropic (uniaxial) Lifshitz integration
# ─────────────────────────────────────────────────────────────────────────────

def load_eps_tensor(json_path: Path) -> tuple[float, float]:
    """
    Extract uniaxial dielectric components (eps_perp, eps_par) from JSON.

    For a uniaxial medium with the optic axis along z (interface normal):
      - eps_perp = epsilon_xx = epsilon_yy  (in-plane, ordinary axis)
      - eps_par  = epsilon_zz               (out-of-plane, extraordinary axis)

    Uses e_total_tensor diagonal if available; falls back to isotropic e_total.

    Args:
        json_path: Path to material JSON (saved by fetch_materials.py).

    Returns:
        (eps_perp, eps_par) as floats.  eps_perp is the in-plane value;
        eps_par is along the interface normal.
    """
    with open(json_path) as f:
        data = json.load(f)
    if "e_total_tensor" in data:
        t = np.array(data["e_total_tensor"])
        eps_perp = float((t[0, 0] + t[1, 1]) / 2.0)   # average xx, yy
        eps_par  = float(t[2, 2])                        # zz (along normal)
        return eps_perp, eps_par
    eps = float(data["e_total"])
    return eps, eps   # isotropic fallback


def _reflection_te_aniso(eps_perp: float, p: float) -> float:
    """
    TE Fresnel reflection for a uniaxial medium at imaginary frequency.

    TE polarisation (E in the interface plane) probes only the in-plane
    dielectric eps_perp (ordinary axis).  Form identical to isotropic r^TE
    but with eps_perp instead of the trace-average epsilon.

        q^TE = sqrt(eps_perp - 1 + p^2)
        r^TE = (p - q^TE) / (p + q^TE)

    Args:
        eps_perp: In-plane (ordinary) dielectric at imaginary frequency.
        p:        Normalised wavevector >= 1.

    Returns:
        r^TE; negative for eps_perp > 1.
    """
    q = np.sqrt(eps_perp - 1.0 + p ** 2)
    return (p - q) / (p + q)


def _reflection_tm_aniso(eps_perp: float, eps_par: float, p: float) -> float:
    """
    TM Fresnel reflection for a uniaxial medium at imaginary frequency.

    TM polarisation (E has a z-component) couples both eps_perp and eps_par.
    With the optic axis along z (interface normal), the extraordinary dispersion
    relation gives:

        q^TM = sqrt(eps_perp / eps_par * (eps_par - 1 + p^2))
        r^TM = (eps_perp * p - q^TM) / (eps_perp * p + q^TM)

    Reduces to the isotropic formula when eps_perp = eps_par.

    Reference: Parsegian, Van der Waals Forces (2006), App. 3.4;
               Bimonte et al., Phys. Rev. A (2009).

    Args:
        eps_perp: In-plane (ordinary) dielectric at imaginary frequency.
        eps_par:  Out-of-plane (extraordinary) dielectric at imaginary frequency.
        p:        Normalised wavevector >= 1.

    Returns:
        r^TM; positive for eps_perp > 1.
    """
    q_sq = (eps_perp / eps_par) * (eps_par - 1.0 + p ** 2)
    if q_sq < 0.0:
        warnings.warn(
            f"_reflection_tm_aniso: q²={q_sq:.3e} < 0 "
            f"(eps_perp={eps_perp:.2f}, eps_par={eps_par:.2f}, p={p:.2f}). "
            "Unphysical anisotropic region — returning 0.",
            RuntimeWarning, stacklevel=2,
        )
        return 0.0   # unphysical parameter region; suppress TM contribution
    q = np.sqrt(q_sq)
    return (eps_perp * p - q) / (eps_perp * p + q)


def _outer_integrand_aniso(xi: float,
                            eps_perp_fn1: Callable, eps_par_fn1: Callable,
                            eps_perp_fn2: Callable, eps_par_fn2: Callable,
                            d: float) -> float:
    """
    Outer (xi) integrand for anisotropic Lifshitz energy.

    Uses uniaxial TE and TM Fresnel coefficients.

    Args:
        xi:            Imaginary frequency (rad/s).
        eps_perp_fn1:  Callable eps_perp1(xi).
        eps_par_fn1:   Callable eps_par1(xi).
        eps_perp_fn2:  Callable eps_perp2(xi).
        eps_par_fn2:   Callable eps_par2(xi).
        d:             Gap separation (m).

    Returns:
        xi^2 * (I_TE + I_TM).
    """
    if xi == 0.0:
        return 0.0

    ep1 = eps_perp_fn1(xi);  ea1 = eps_par_fn1(xi)
    ep2 = eps_perp_fn2(xi);  ea2 = eps_par_fn2(xi)

    p_max = min(max(20.0, 5.0 * C / (xi * d)), 1.0e6)

    def inner_te(p: float) -> float:
        r1 = _reflection_te_aniso(ep1, p)
        r2 = _reflection_te_aniso(ep2, p)
        arg = r1 * r2 * np.exp(-2.0 * p * xi * d / C)
        if arg >= 1.0:
            return 0.0
        return p * np.log(1.0 - arg)

    def inner_tm(p: float) -> float:
        r1 = _reflection_tm_aniso(ep1, ea1, p)
        r2 = _reflection_tm_aniso(ep2, ea2, p)
        arg = r1 * r2 * np.exp(-2.0 * p * xi * d / C)
        if arg >= 1.0:
            return 0.0
        return p * np.log(1.0 - arg)

    I_te, _ = quad(inner_te, 1.0, p_max, limit=200, epsrel=1e-5)
    I_tm, _ = quad(inner_tm, 1.0, p_max, limit=200, epsrel=1e-5)

    return xi ** 2 * (I_te + I_tm)


def casimir_energy_aniso(eps_perp1: float, eps_par1: float,
                          eps_perp2: float, eps_par2: float,
                          d: float,
                          omega_uv: float = OMEGA_UV) -> float:
    """
    Lifshitz-Casimir energy for two uniaxial dielectric half-spaces.

    Uses anisotropic (uniaxial) Fresnel coefficients with the optic axis
    along z (perpendicular to the interface / along the Casimir force direction).

    For identical isotropic media (eps_perp = eps_par) the result matches
    casimir_energy() exactly.

    Args:
        eps_perp1:  In-plane static dielectric of material 1 (epsilon_xx).
        eps_par1:   Out-of-plane static dielectric of material 1 (epsilon_zz).
        eps_perp2:  In-plane static dielectric of material 2.
        eps_par2:   Out-of-plane static dielectric of material 2.
        d:          Gap separation (m).
        omega_uv:   UV oscillator frequency for Cauchy model (rad/s).

    Returns:
        Casimir energy per unit area (J/m^2).  Negative = attractive.
    """
    ep_fn1 = lambda xi: epsilon_imaginary(eps_perp1, xi, omega_uv)
    ea_fn1 = lambda xi: epsilon_imaginary(eps_par1,  xi, omega_uv)
    ep_fn2 = lambda xi: epsilon_imaginary(eps_perp2, xi, omega_uv)
    ea_fn2 = lambda xi: epsilon_imaginary(eps_par2,  xi, omega_uv)

    xi_max = 10.0 * omega_uv
    result, _ = quad(
        _outer_integrand_aniso, 0.0, xi_max,
        args=(ep_fn1, ea_fn1, ep_fn2, ea_fn2, d),
        limit=100, epsabs=1e-60, epsrel=1e-4, points=[omega_uv],
    )

    prefactor = HBAR / (4.0 * np.pi ** 2 * C ** 2)
    return prefactor * result


# ─────────────────────────────────────────────────────────────────────────────
# Finite-thickness slab: transfer-matrix (Airy) Lifshitz correction
# ─────────────────────────────────────────────────────────────────────────────

def _airy_reflection_te(eps_slab: float, eps_sub: float,
                         p: float, xi: float, h: float) -> float:
    """
    Effective TE reflection of a finite-thickness dielectric slab on a substrate,
    seen from vacuum, at imaginary frequency xi.

    Uses the Airy (Fabry-Perot) formula for coherent multiple reflections:

        r_eff^TE = (r01 + r12 * exp(-2*q_L*xi*h/c))
                 / (1 + r01 * r12 * exp(-2*q_L*xi*h/c))

    where:
        r01 = (p - q_L) / (p + q_L)          vacuum -> slab interface
        r12 = (q_L - q_sub) / (q_L + q_sub)  slab -> substrate interface
        q_L   = sqrt(eps_slab - 1 + p^2)      normalised z-wavevector in slab
        q_sub = sqrt(eps_sub  - 1 + p^2)      normalised z-wavevector in substrate
        h = slab thickness (m)

    At h -> inf:  r_eff -> r01  (semi-infinite slab, same as current code).
    At h -> 0:    r_eff -> 0    (vacuum, no slab).

    Args:
        eps_slab: Dielectric of the slab at imaginary frequency xi.
        eps_sub:  Dielectric of the substrate at imaginary frequency xi.
        p:        Normalised wavevector >= 1.
        xi:       Imaginary frequency (rad/s).
        h:        Slab thickness (m).

    Returns:
        Effective TE reflection coefficient (real).
    """
    q_L   = np.sqrt(eps_slab - 1.0 + p ** 2)
    q_sub = np.sqrt(eps_sub  - 1.0 + p ** 2)
    r01 = (p    - q_L  ) / (p    + q_L  )
    r12 = (q_L  - q_sub) / (q_L  + q_sub)
    phase = np.exp(-2.0 * q_L * xi * h / C)
    denom = 1.0 + r01 * r12 * phase
    if abs(denom) < 1e-30:
        return r01
    return (r01 + r12 * phase) / denom


def _airy_reflection_tm(eps_slab: float, eps_sub: float,
                         p: float, xi: float, h: float) -> float:
    """
    Effective TM reflection of a finite-thickness dielectric slab on a substrate.

    Uses the Airy formula with TM Fresnel coefficients:

        r01^TM = (eps_slab * p - q_L) / (eps_slab * p + q_L)  [vacuum -> slab]
        r12^TM = (eps_sub * q_L - eps_slab * q_sub)
               / (eps_sub * q_L + eps_slab * q_sub)            [slab -> substrate]

    Args:
        eps_slab: Dielectric of the slab at imaginary frequency xi.
        eps_sub:  Dielectric of the substrate at imaginary frequency xi.
        p:        Normalised wavevector >= 1.
        xi:       Imaginary frequency (rad/s).
        h:        Slab thickness (m).

    Returns:
        Effective TM reflection coefficient (real).
    """
    q_L   = np.sqrt(eps_slab - 1.0 + p ** 2)
    q_sub = np.sqrt(eps_sub  - 1.0 + p ** 2)
    r01 = (eps_slab * p - q_L) / (eps_slab * p + q_L)
    r12 = (eps_sub  * q_L - eps_slab * q_sub) / (eps_sub * q_L + eps_slab * q_sub)
    phase = np.exp(-2.0 * q_L * xi * h / C)
    denom = 1.0 + r01 * r12 * phase
    if abs(denom) < 1e-30:
        return r01
    return (r01 + r12 * phase) / denom


def casimir_energy_multilayer(eps_slab: float, h_slab: float,
                               eps_sub: float, d: float,
                               omega_uv: float = OMEGA_UV) -> float:
    """
    Lifshitz-Casimir energy for a finite-thickness dielectric slab on a substrate.

    Corrects the semi-infinite slab approximation by using the Airy (transfer-
    matrix) effective reflection coefficient for the slab+substrate system.

    Geometry (left to right):
        vacuum (semi-infinite) | gap d | slab (eps_slab, h_slab) | substrate (eps_sub)

    The slab is assumed to be backed by the substrate (not vacuum).  For the
    optimizer's 18-layer Te metamaterial on WTe2:
        eps_slab = eps_eff  (Maxwell-Garnett EMA)
        h_slab   = N_layers * LAYER_THICKNESS_NM * 1e-9
        eps_sub  = eps_WTe2

    For h_slab -> inf (semi-infinite limit) the result reduces to
    casimir_energy(eps_slab, eps_sub, d) — verifiable numerically.

    The semi-infinite approximation overestimates |E| by
    ~exp(-2*q_L*xi_c*h_slab/c) relative correction, where xi_c ~ c/d is the
    characteristic Matsubara frequency.  At h_slab = 90 nm and d = 83 nm this
    correction is O(10%), not O(100%), so the optimizer's designs remain
    qualitatively valid but quantitatively shifted.

    Args:
        eps_slab:  Static dielectric of the metamaterial slab (ε_eff from MG-EMA).
        h_slab:    Physical thickness of the slab (m).  h_slab = N * layer_nm * 1e-9.
        eps_sub:   Static dielectric of the substrate (WTe2).
        d:         Vacuum gap separation (m).
        omega_uv:  UV pole frequency for Cauchy dispersion model (rad/s).

    Returns:
        Casimir energy per unit area (J/m^2).  Negative = attractive.
    """
    eps_slab_fn = lambda xi: epsilon_imaginary(eps_slab, xi, omega_uv)
    eps_sub_fn  = lambda xi: epsilon_imaginary(eps_sub,  xi, omega_uv)

    def outer(xi: float) -> float:
        if xi == 0.0:
            return 0.0
        p_max = min(max(20.0, 5.0 * C / (xi * d)), 1.0e6)

        def inner_te(p: float) -> float:
            e_slab = eps_slab_fn(xi)
            e_sub  = eps_sub_fn(xi)
            # Left surface: vacuum (r1 = 0 for semi-infinite vacuum)
            # Actually left plate IS the slab — it reflects from the gap side.
            # r1 = standard slab TE reflection (from vacuum into slab)
            # r2 = 0 (right half-space is vacuum — but there IS no left plate here)
            # Correct geometry: one plate is the slab+substrate assembly.
            # The LEFT plate in the standard Lifshitz setup is the Te slab;
            # r1 = r_eff^TE (slab + substrate seen from vacuum gap).
            # No right plate; but Lifshitz for TWO half-spaces needs r2 too.
            # Here we model: Te_slab_on_substrate | gap | vacuum (no second plate).
            # The Casimir energy between two slabs: left = Te_slab+sub, right = vacuum.
            # r2 = reflection of vacuum = 0  -> ln(1-0) = 0.
            # This is not useful. The correct use case is:
            #   left PLATE = Te slab (finite thickness) on backing
            #   right PLATE = WTe2 substrate (semi-infinite)
            # But then r1 is the slab reflection FROM the gap, and
            # r2 is the WTe2 substrate reflection.  r2 = _reflection_te(e_sub, p).
            # However, the slab IS on the substrate — the substrate IS the backing.
            # So geometry: vacuum | gap d | [slab h_slab | substrate semi-inf]
            # The right assembly r_right = r_eff (Airy of slab+substrate).
            # The left is just vacuum (r_left = 0). This gives E=0 (wrong).
            #
            # CORRECT physical setup:
            #   Left:  vacuum semi-infinite (device backing, far away)
            #   |      Te slab (thickness h_slab)
            #   Gap d  (vacuum)
            #   |      WTe2 substrate (semi-infinite)
            #
            # So r1 = TE reflection of [vacuum | Te_slab] seen from gap
            #       = Airy(eps_slab, eps_vac=1, p, xi, h_slab) — slab on vacuum backing
            # r2 = _reflection_te(eps_sub, p)  — semi-infinite WTe2
            e_vac = 1.0   # vacuum backing behind the slab
            r1_corrected = _airy_reflection_te(e_slab, e_vac, p, xi, h_slab)
            r2 = _reflection_te(e_sub, p)
            arg = r1_corrected * r2 * np.exp(-2.0 * p * xi * d / C)
            if arg >= 1.0:
                return 0.0
            return p * np.log(1.0 - arg)

        def inner_tm(p: float) -> float:
            e_slab = eps_slab_fn(xi)
            e_sub  = eps_sub_fn(xi)
            e_vac  = 1.0
            r1 = _airy_reflection_tm(e_slab, e_vac, p, xi, h_slab)
            r2 = _reflection_tm(e_sub, p)
            arg = r1 * r2 * np.exp(-2.0 * p * xi * d / C)
            if arg >= 1.0:
                return 0.0
            return p * np.log(1.0 - arg)

        I_te, _ = quad(inner_te, 1.0, p_max, limit=200, epsrel=1e-5)
        I_tm, _ = quad(inner_tm, 1.0, p_max, limit=200, epsrel=1e-5)
        return xi ** 2 * (I_te + I_tm)

    xi_max = 10.0 * omega_uv
    result, _ = quad(outer, 0.0, xi_max, limit=100,
                     epsabs=1e-60, epsrel=1e-4, points=[omega_uv])
    prefactor = HBAR / (4.0 * np.pi ** 2 * C ** 2)
    return prefactor * result


def sweep_separation_aniso(eps_perp1: float, eps_par1: float,
                            eps_perp2: float, eps_par2: float,
                            d_min_nm: float = 1.0, d_max_nm: float = 100.0,
                            n_points: int = 40,
                            omega_uv: float = OMEGA_UV,
                            ) -> tuple[np.ndarray, np.ndarray]:
    """
    Compute anisotropic Casimir energy over a log-spaced separation range.

    Args:
        eps_perp1:  In-plane static dielectric of material 1.
        eps_par1:   Out-of-plane static dielectric of material 1.
        eps_perp2:  In-plane static dielectric of material 2.
        eps_par2:   Out-of-plane static dielectric of material 2.
        d_min_nm:   Minimum separation (nm).
        d_max_nm:   Maximum separation (nm).
        n_points:   Number of log-spaced sample points.
        omega_uv:   UV oscillator frequency (rad/s).

    Returns:
        (d_nm, E_Jm2) arrays.
    """
    d_nm = np.logspace(np.log10(d_min_nm), np.log10(d_max_nm), n_points)
    E = []
    for i, d in enumerate(d_nm):
        e = casimir_energy_aniso(eps_perp1, eps_par1,
                                  eps_perp2, eps_par2, d * 1e-9, omega_uv)
        E.append(e)
        if (i + 1) % 10 == 0:
            print(f"    {i+1}/{n_points}  d={d:.1f} nm  E={e:.4e} J/m^2")
    return d_nm, np.array(E)


# ─────────────────────────────────────────────────────────────────────────────
# Casimir force F = -dE/dd
# ─────────────────────────────────────────────────────────────────────────────

def _inner_force_te(p: float, xi: float,
                    eps_fn1: Callable, eps_fn2: Callable,
                    d: float) -> float:
    """
    Inner (p) integrand for the TE contribution to Casimir force.

    F = -dE/dd so each log integrand gains a factor (2*p*xi/c) / (1 - r1*r2*exp):

        integrand_F^TE = p * (2*p*xi/c) * r1^TE * r2^TE * exp(-2*p*xi*d/c)
                         / (1 - r1^TE * r2^TE * exp(-2*p*xi*d/c))

    Positive output -> attractive force (sign convention: F < 0 attractive).

    Args:
        p:       Normalised wavevector (>= 1).
        xi:      Imaginary frequency (rad/s).
        eps_fn1: Callable eps1(xi).
        eps_fn2: Callable eps2(xi).
        d:       Gap separation (m).

    Returns:
        Integrand value at (p, xi, d).
    """
    e1 = eps_fn1(xi)
    e2 = eps_fn2(xi)
    r1 = _reflection_te(e1, p)
    r2 = _reflection_te(e2, p)
    x = r1 * r2 * np.exp(-2.0 * p * xi * d / C)
    if x >= 1.0:
        return 0.0
    return p * (2.0 * p * xi / C) * x / (1.0 - x)


def _inner_force_tm(p: float, xi: float,
                    eps_fn1: Callable, eps_fn2: Callable,
                    d: float) -> float:
    """
    Inner (p) integrand for the TM contribution to Casimir force.

    Args:
        p:       Normalised wavevector (>= 1).
        xi:      Imaginary frequency (rad/s).
        eps_fn1: Callable eps1(xi).
        eps_fn2: Callable eps2(xi).
        d:       Gap separation (m).

    Returns:
        Integrand value at (p, xi, d).
    """
    e1 = eps_fn1(xi)
    e2 = eps_fn2(xi)
    r1 = _reflection_tm(e1, p)
    r2 = _reflection_tm(e2, p)
    x = r1 * r2 * np.exp(-2.0 * p * xi * d / C)
    if x >= 1.0:
        return 0.0
    return p * (2.0 * p * xi / C) * x / (1.0 - x)


def casimir_force(eps_static1: float, eps_static2: float, d: float,
                  omega_uv: float = OMEGA_UV) -> float:
    """
    Compute Lifshitz-Casimir force per unit area F(d) = -dE/dd in N/m^2.

    Analytically differentiated from the Lifshitz energy integral:

        F(d) = -(hbar / 4*pi^2 * c^2)
                 * int_0^xi_max xi^2 dxi
                 * int_1^p_max p dp
                 * sum_pol (2*p*xi/c) * r1^pol * r2^pol * exp(-2*p*xi*d/c)
                            / (1 - r1^pol * r2^pol * exp(-2*p*xi*d/c))

    The prefactor includes a minus sign so that:
      - F < 0  -> attractive (surfaces pull together)
      - F > 0  -> repulsive  (chiral repulsion)

    Args:
        eps_static1: Static dielectric of material 1.
        eps_static2: Static dielectric of material 2.
        d:           Gap separation (m); must be > 0.
        omega_uv:    UV oscillator frequency for Cauchy model (rad/s).

    Returns:
        Casimir force per unit area (N/m^2 = Pa).  Negative = attractive.
    """
    eps_fn1 = lambda xi: epsilon_imaginary(eps_static1, xi, omega_uv)
    eps_fn2 = lambda xi: epsilon_imaginary(eps_static2, xi, omega_uv)

    def outer(xi: float) -> float:
        if xi == 0.0:
            return 0.0
        p_max = min(max(20.0, 5.0 * C / (xi * d)), 1.0e6)
        I_te, _ = quad(_inner_force_te, 1.0, p_max,
                       args=(xi, eps_fn1, eps_fn2, d),
                       limit=200, epsrel=1e-5)
        I_tm, _ = quad(_inner_force_tm, 1.0, p_max,
                       args=(xi, eps_fn1, eps_fn2, d),
                       limit=200, epsrel=1e-5)
        return xi ** 2 * (I_te + I_tm)

    xi_max = 10.0 * omega_uv
    result, _ = quad(outer, 0.0, xi_max, limit=100,
                     epsabs=1e-60, epsrel=1e-4, points=[omega_uv])

    # Negative sign: F = -dE/dd; the inner integrands are positive for eps>1
    # so result > 0, and F = -prefactor * result < 0 (attractive).
    prefactor = HBAR / (4.0 * np.pi ** 2 * C ** 2)
    return -prefactor * result


def _casimir_chiral_force_correction(eps_static1: float, eps_static2: float,
                                      d: float,
                                      omega_uv: float = OMEGA_UV) -> float:
    """
    Compute the kappa^2 coefficient of the chiral Casimir force correction.

    delta_F = -d(delta_E)/dd
            = 2 * (hbar / 4*pi^2*c^2) * int xi^2 dxi int p dp
              * (r1^TM*r2^TE + r1^TE*r2^TM) * (2*p*xi/c) * exp(-2pxid/c)

    F_chiral(d, kappa) = F_std(d) + kappa^2 * delta_F(d)

    Args:
        eps_static1: Static dielectric of material 1.
        eps_static2: Static dielectric of material 2.
        d:           Gap separation (m).
        omega_uv:    UV oscillator frequency (rad/s).

    Returns:
        delta_F in N/m^2.  Positive = chiral correction reduces attraction.
    """
    eps_fn1 = lambda xi: epsilon_imaginary(eps_static1, xi, omega_uv)
    eps_fn2 = lambda xi: epsilon_imaginary(eps_static2, xi, omega_uv)

    def inner(p: float, xi: float) -> float:
        e1 = eps_fn1(xi)
        e2 = eps_fn2(xi)
        rTE1 = _reflection_te(e1, p)
        rTM1 = _reflection_tm(e1, p)
        rTE2 = _reflection_te(e2, p)
        rTM2 = _reflection_tm(e2, p)
        cross = rTM1 * rTE2 + rTE1 * rTM2
        return p * cross * (2.0 * p * xi / C) * np.exp(-2.0 * p * xi * d / C)

    def outer(xi: float) -> float:
        if xi == 0.0:
            return 0.0
        p_max = min(max(20.0, 5.0 * C / (xi * d)), 1.0e6)
        integral_val, _ = quad(inner, 1.0, p_max, args=(xi,), limit=150, epsrel=1e-4)
        return xi ** 2 * integral_val

    xi_max = 10.0 * omega_uv
    raw, _ = quad(outer, 0.0, xi_max, limit=80, epsrel=1e-3, points=[omega_uv])

    prefactor = HBAR / (4.0 * np.pi ** 2 * C ** 2)
    # delta_E = -2P * raw_energy  (raw_energy = integral without 2pxi/c factor)
    # d(delta_E)/dd = -2P * integral(xi^2 * integral(p * cross * (-2pxi/c) * exp))
    #               = +2P * raw   (raw already has (2pxi/c) factor)
    # delta_F = -d(delta_E)/dd = -2P * raw
    # For Te|Te: cross < 0, raw < 0, so delta_F = -2P*(negative) > 0 (reduces attraction)
    return -2.0 * prefactor * raw


def casimir_force_chiral(eps_static1: float, eps_static2: float,
                          d: float, kappa: float = 0.0,
                          omega_uv: float = OMEGA_UV) -> float:
    """
    Casimir force with chiral TE-TM correction (full Lifshitz + kappa^2 term).

    F(d, kappa) = F_std(d) + kappa^2 * delta_F(d)

    where delta_F = -d(delta_E)/dd > 0 (chiral correction reduces attraction).

    Args:
        eps_static1: Static dielectric of material 1.
        eps_static2: Static dielectric of material 2.
        d:           Gap separation (m).
        kappa:       Chirality parameter kappa = kappa0 * sin(theta).
        omega_uv:    UV oscillator frequency (rad/s).

    Returns:
        Casimir force per unit area (N/m^2).  Negative = attractive.
    """
    F_std = casimir_force(eps_static1, eps_static2, d, omega_uv)
    if kappa == 0.0:
        return F_std
    delta_F = _casimir_chiral_force_correction(eps_static1, eps_static2, d, omega_uv)
    return F_std + kappa ** 2 * delta_F


def sweep_force(eps_static1: float, eps_static2: float,
                d_min_nm: float = 1.0, d_max_nm: float = 100.0,
                n_points: int = 50,
                kappa: float = 0.0,
                omega_uv: float = OMEGA_UV) -> tuple[np.ndarray, np.ndarray]:
    """
    Compute Casimir force per unit area over a range of separations.

    Args:
        eps_static1: Static dielectric of material 1.
        eps_static2: Static dielectric of material 2.
        d_min_nm:    Minimum separation (nm).
        d_max_nm:    Maximum separation (nm).
        n_points:    Number of log-spaced sample points.
        kappa:       Chirality parameter (0 = standard Lifshitz).
        omega_uv:    UV oscillator frequency (rad/s).

    Returns:
        Tuple (d_nm, F) where F is in N/m^2.  Negative = attractive.
    """
    d_nm = np.logspace(np.log10(d_min_nm), np.log10(d_max_nm), n_points)
    F = []
    for i, d in enumerate(d_nm):
        if kappa == 0.0:
            f = casimir_force(eps_static1, eps_static2, d * 1e-9, omega_uv)
        else:
            f = casimir_force_chiral(eps_static1, eps_static2,
                                     d * 1e-9, kappa, omega_uv)
        F.append(f)
        if (i + 1) % 10 == 0:
            print(f"    {i+1}/{n_points}  d={d:.1f} nm  F={f:.4e} N/m^2")
    return d_nm, np.array(F)


# ─────────────────────────────────────────────────────────────────────────────
# Multi-oscillator Sellmeier dielectric model
# ─────────────────────────────────────────────────────────────────────────────

def epsilon_imaginary_2osc(C1: float, omega1: float,
                            C2: float, omega2: float,
                            xi: float) -> float:
    """
    Two-oscillator Sellmeier model for dielectric at imaginary frequency.

    Splits the dielectric response into an IR (ionic/phonon) oscillator and
    a UV (electronic) oscillator, each a single-pole Cauchy term:

        eps(i*xi) = 1 + C1 / (1 + (xi/omega1)^2)
                      + C2 / (1 + (xi/omega2)^2)

    At xi=0: eps(0) = 1 + C1 + C2.
    As xi -> inf: eps -> 1 (correct vacuum limit).

    Calibration for Tellurium (mp-19, eps_static=164.27, n=10.88):
        C1  = 45.77   omega1 = 3.0e13 rad/s  (IR phonon, ~160 cm⁻¹, Caldwell & Fan 1959)
        C2  = 117.50  omega2 = 4.5e15 rad/s  (UV electronic, ~3 eV, Stuke 1965)
        eps(0) = 1 + 45.77 + 117.50 = 164.27 ✓
        eps_electronic (xi>>omega1, xi<<omega2): 1 + 0 + 117.50 = 118.50  (≈ n² = 118.4 ✓)
        eps at xi>>omega2: 1 (vacuum)

    References for Te oscillator parameters:
        Caldwell & Fan, Phys. Rev. 114, 664 (1959)  — IR phonon at 160 cm⁻¹
        Stuke, J. Phys. Chem. Sol. 26, 1803 (1965)  — UV electronic resonance ~3 eV
        Palik, Handbook of Optical Constants of Solids (1985), Te entry

    Calibration for WTe2 (mp-1023926, eps_static=6.16, n=2.42):
        C1 = 0.30    omega1 = 5.0e13 rad/s  (far-IR, ionic)
        C2 = 4.86    omega2 = 6.0e15 rad/s  (interband ~4 eV, Ali et al. 2014)
        eps(0) = 1 + 0.30 + 4.86 = 6.16 ✓
        eps_electronic: 1 + 0 + 4.86 = 5.86  (≈ n² = 5.86 ✓)

    Args:
        C1, C2:       Oscillator strengths (dimensionless). C1+C2 = eps_static-1.
        omega1, omega2: Oscillator frequencies (rad/s). omega1 << omega2.
        xi:           Imaginary frequency (rad/s).

    Returns:
        Real-valued eps(i*xi) >= 1.
    """
    return (1.0
            + C1 / (1.0 + (xi / omega1) ** 2)
            + C2 / (1.0 + (xi / omega2) ** 2))


# Default 2-oscillator parameters for Te and WTe2 (P-6m2)
# Literature-grounded 2-oscillator parameters
# Te:   IR phonon ω1 from Caldwell & Fan (1959); UV pole ω2 from Stuke (1965)
# WTe2: interband transition ω2 from Ali et al., Nature 514, 205 (2014)
TE_2OSC   = dict(C1=45.77,  omega1=3.0e13, C2=117.50, omega2=4.5e15)
WTE2_2OSC = dict(C1=0.30,   omega1=5.0e13, C2=4.86,   omega2=6.0e15)

# Drude + Lorentz parameters for Td-WTe2 (type-II Weyl semimetal, Pmn2_1)
# Drude term: Weyl-pocket free carriers (Wu et al. PRB 2017, Soluyanov Nature 2015)
#   omega_p ~ 0.66 eV -> 1.0e15 rad/s; gamma from residual resistivity ~33 meV
# Lorentz term: interband (electronic) contribution only, eps_inf = 13.63
#   (from td_wte2_dft.json e_electronic = 13.63; excludes ionic eps_ionic=1.70)
# Use epsilon_imaginary_drude_lorentz() with these params for the "td" substrate.
WTE2_TD_DRUDE = dict(omega_p=1.0e15, gamma=5.0e13, eps_inf=13.63, omega_uv=OMEGA_UV)


def casimir_energy_2osc(C1_1: float, omega1_1: float, C2_1: float, omega2_1: float,
                         C1_2: float, omega1_2: float, C2_2: float, omega2_2: float,
                         d: float) -> float:
    """
    Lifshitz-Casimir energy using the 2-oscillator dielectric model.

    Replaces the single-oscillator Cauchy model with a 2-oscillator Sellmeier
    for both materials.  The IR oscillator captures phonon/ionic contributions;
    the UV oscillator captures electronic band contributions.  The full Lifshitz
    double integral is used (same integrator as casimir_energy).

    Args:
        C1_1, omega1_1, C2_1, omega2_1:  2-osc parameters for material 1.
        C1_2, omega1_2, C2_2, omega2_2:  2-osc parameters for material 2.
        d:  Gap separation (m).

    Returns:
        Casimir energy per unit area (J/m^2).  Negative = attractive.
    """
    eps_fn1 = lambda xi: epsilon_imaginary_2osc(C1_1, omega1_1, C2_1, omega2_1, xi)
    eps_fn2 = lambda xi: epsilon_imaginary_2osc(C1_2, omega1_2, C2_2, omega2_2, xi)

    # Upper limit: 5x the higher UV pole
    xi_max = 10.0 * max(omega2_1, omega2_2)

    result, _ = quad(
        _outer_integrand,
        0.0, xi_max,
        args=(eps_fn1, eps_fn2, d),
        limit=150,
        epsabs=1e-60,
        epsrel=1e-4,
        points=[omega1_1, omega2_1, omega1_2, omega2_2],
    )

    prefactor = HBAR / (4.0 * np.pi ** 2 * C ** 2)
    return prefactor * result


def sweep_separation_2osc(mat1_params: dict, mat2_params: dict,
                           d_min_nm: float = 1.0, d_max_nm: float = 100.0,
                           n_points: int = 40) -> tuple[np.ndarray, np.ndarray]:
    """
    Casimir energy sweep using the 2-oscillator dielectric model.

    Args:
        mat1_params: Dict with keys C1, omega1, C2, omega2 for material 1.
        mat2_params: Dict with keys C1, omega1, C2, omega2 for material 2.
        d_min_nm, d_max_nm: Separation range (nm).
        n_points:   Number of log-spaced points.

    Returns:
        Tuple (d_nm, E_Jm2).
    """
    d_arr = np.logspace(np.log10(d_min_nm), np.log10(d_max_nm), n_points)
    E = []
    for i, d_nm in enumerate(d_arr):
        e = casimir_energy_2osc(
            mat1_params["C1"], mat1_params["omega1"],
            mat1_params["C2"], mat1_params["omega2"],
            mat2_params["C1"], mat2_params["omega1"],
            mat2_params["C2"], mat2_params["omega2"],
            d_nm * 1e-9,
        )
        E.append(e)
        if (i + 1) % 10 == 0:
            print(f"    {i+1}/{n_points}  d={d_nm:.1f} nm  E={e:.4e} J/m^2")
    return d_arr, np.array(E)


# ─────────────────────────────────────────────────────────────────────────────
# General-purpose eps-callable interface (used by Drude benchmark)
# ─────────────────────────────────────────────────────────────────────────────

def casimir_force_from_eps_fns(eps_fn1: Callable, eps_fn2: Callable,
                                d: float,
                                omega_ref: float = OMEGA_UV) -> float:
    """
    Casimir pressure F(d) = -dE/dd using arbitrary callable dielectric functions.

    Identical integrator to casimir_force() but accepts pre-built eps(xi)
    callables — enabling Drude, multi-oscillator, or any other model.

    Primary use: Au/SiO₂ code validation benchmark, where the Au plate
    uses the Drude model (epsilon_imaginary_drude) instead of the Cauchy model.

    Args:
        eps_fn1:   Callable eps1(xi: float) -> float.
        eps_fn2:   Callable eps2(xi: float) -> float.
        d:         Gap separation (m); must be > 0.
        omega_ref: Reference frequency used to set xi_max = 10*omega_ref (rad/s).
                   Set to max(plasma_freq, UV_pole) of the two materials.

    Returns:
        Casimir pressure (N/m^2).  Negative = attractive.
    """
    def outer(xi: float) -> float:
        if xi == 0.0:
            return 0.0
        p_max = min(max(20.0, 5.0 * C / (xi * d)), 1.0e6)
        I_te, _ = quad(_inner_force_te, 1.0, p_max,
                       args=(xi, eps_fn1, eps_fn2, d),
                       limit=200, epsrel=1e-5)
        I_tm, _ = quad(_inner_force_tm, 1.0, p_max,
                       args=(xi, eps_fn1, eps_fn2, d),
                       limit=200, epsrel=1e-5)
        return xi ** 2 * (I_te + I_tm)

    xi_max = 10.0 * omega_ref
    result, _ = quad(outer, 0.0, xi_max, limit=150,
                     epsabs=1e-60, epsrel=1e-4, points=[omega_ref])
    prefactor = HBAR / (4.0 * np.pi ** 2 * C ** 2)
    return -prefactor * result


# ─────────────────────────────────────────────────────────────────────────────
# Finite-temperature Lifshitz (Matsubara summation)
# ─────────────────────────────────────────────────────────────────────────────

def casimir_energy_finite_T(eps_static1: float, eps_static2: float,
                             d: float, T: float = 300.0,
                             omega_uv: float = OMEGA_UV,
                             n_max: int = 800) -> float:
    """
    Finite-temperature Lifshitz-Casimir energy via Matsubara summation.

    Replaces the continuous imaginary-frequency integral with a discrete sum
    over Matsubara frequencies xi_n = n * xi_1, where xi_1 = 2*pi*k_B*T/hbar.

    The finite-temperature formula (Pitaevskii, 1960):

        E(d, T) = (k_B T / (2*pi)) * sum'_{n=0}^{N_max} int_1^{p_max} p dp
                  * [ln(1 - r1^TE r2^TE e^{-2p xi_n d/c})
                   + ln(1 - r1^TM r2^TM e^{-2p xi_n d/c})]

    where sum' means the n=0 term is counted with weight 1/2.

    The n=0 Matsubara term (xi=0) is the classical/thermal contribution:
      - r^TE(xi=0) = 0 for any finite dielectric -> TE mode is screened
      - r^TM(xi=0) = (eps-1)/(eps+1) evaluated at static eps

    Physics:
      - At d << thermal length l_T = hbar*c/(2*pi*k_B*T) ≈ 1.2 µm (300 K),
        the T=0 result is an excellent approximation.
      - Thermal corrections become significant at d ~ l_T and are dominant
        (classical limit) at d >> l_T.
      - The n=0 (classical) term alone gives E_cl = k_B*T/(16*pi*d^2) * beta1*beta2,
        where beta_i = (eps_i - 1)/(eps_i + 1).

    Args:
        eps_static1: Static dielectric of material 1.
        eps_static2: Static dielectric of material 2.
        d:           Gap separation (m); must be > 0.
        T:           Temperature (K).  Default 300 K.
        omega_uv:    UV oscillator pole frequency (rad/s).
        n_max:       Number of Matsubara terms (excluding n=0).
                     Convergence: n_max > c / (2*d*xi_1).  Default 800
                     is safe for d >= 1 nm at T=300 K.

    Returns:
        Casimir energy per unit area (J/m^2).  Negative = attractive.
        At T=0 (or T very small) this should match casimir_energy().
    """
    xi_1 = 2.0 * np.pi * KB * T / HBAR   # first Matsubara frequency (rad/s)

    eps_fn1 = lambda xi: epsilon_imaginary(eps_static1, xi, omega_uv)
    eps_fn2 = lambda xi: epsilon_imaginary(eps_static2, xi, omega_uv)

    # Prefactor kBT/(2π) is consistent with the corrected T=0 formula using
    # ħ/(4π²c²) (DLP 1961).  In the T→0 (d<<l_T) limit the Matsubara sum
    # reproduces casimir_energy() to within exponentially-small thermal corrections.
    # Reference: Bordag et al. (2009), Advances in the Casimir Effect, eq. 7.7.
    prefactor = KB * T / (2.0 * np.pi)

    total = 0.0

    # ── n=0 classical term ────────────────────────────────────────────────────
    # At xi=0 only TM survives (r^TE = 0 for any finite dielectric).
    # The p-space normalisation p = c*kappa/xi is degenerate at xi=0, so we
    # work directly in k_perp space (u = k_perp * d, dimensionless):
    #
    #   E_{n=0} = prefactor * (1/2) * (1/d^2)
    #             * integral_0^inf u * ln(1 - beta1*beta2 * exp(-2u)) du
    #
    # where beta_i = (eps_i(0) - 1)/(eps_i(0) + 1)  [static TM reflection].
    # Weight 1/2 from the Sigma' convention.
    # Reference: DLP (1961) Adv. Phys. 10, 165, eq. (3.16).
    beta1_s = (eps_static1 - 1.0) / (eps_static1 + 1.0)
    beta2_s = (eps_static2 - 1.0) / (eps_static2 + 1.0)
    beta_prod = beta1_s * beta2_s

    def _inner_n0_kperp(u: float) -> float:
        """u = k_perp * d; integrand for n=0 TM classical term."""
        arg = beta_prod * np.exp(-2.0 * u)
        if arg >= 1.0 or arg <= -1.0:
            return 0.0
        return u * np.log(1.0 - arg)

    I0_kperp, _ = quad(_inner_n0_kperp, 0.0, 50.0, limit=100, epsrel=1e-6)
    total += 0.5 * I0_kperp / d ** 2  # weight 1/2; 1/d^2 from u=k_perp*d

    # ── n >= 1 quantum Matsubara terms ────────────────────────────────────────
    # Correct formula (Bordag et al. 2009, eq. 7.13; DLP 1961):
    #
    #   E_T = prefactor * sum'_{n=0}^inf  (xi_n/c)^2
    #         * integral_1^p_max p dp [ln(1-r1^TE r2^TE e^{-2p xi_n d/c})
    #                                  + ln(1-r1^TM r2^TM e^{-2p xi_n d/c})]
    #
    # The (xi_n/c)^2 factor arises from the change of variables
    #   k_perp dk_perp = (xi_n/c)^2 p dp
    # when converting the transverse-wavevector integral to normalised p.
    # MISSING this factor causes a ~10^13 magnitude error at d=83 nm, T=300 K.
    for n in range(1, n_max + 1):
        xi_n  = n * xi_1
        xic_sq = (xi_n / C) ** 2          # (xi_n/c)^2 — the previously missing factor

        p_max = min(max(20.0, 5.0 * C / (xi_n * d)), 1.0e6)
        I_te, _ = quad(_inner_integrand_te, 1.0, p_max,
                       args=(xi_n, eps_fn1, eps_fn2, d),
                       limit=200, epsrel=1e-4)
        I_tm, _ = quad(_inner_integrand_tm, 1.0, p_max,
                       args=(xi_n, eps_fn1, eps_fn2, d),
                       limit=200, epsrel=1e-4)
        contrib = xic_sq * (I_te + I_tm)
        total  += contrib

        # Early termination once contribution is negligible
        if n > 10 and abs(contrib) < 1e-12 * abs(total):
            break

    return prefactor * total


def sweep_finite_T(eps_static1: float, eps_static2: float,
                   T: float = 300.0,
                   d_min_nm: float = 1.0, d_max_nm: float = 2000.0,
                   n_points: int = 40,
                   omega_uv: float = OMEGA_UV) -> tuple[np.ndarray, np.ndarray]:
    """
    Casimir energy sweep at finite temperature using Matsubara summation.

    Extended to d=2000 nm to capture the thermal regime (l_T ≈ 1.2 µm at 300 K).

    Args:
        eps_static1, eps_static2: Static dielectrics.
        T:          Temperature (K).
        d_min_nm, d_max_nm: Separation range (nm).
        n_points:   Log-spaced sample count.
        omega_uv:   UV pole frequency (rad/s).

    Returns:
        Tuple (d_nm, E_Jm2).
    """
    d_arr = np.logspace(np.log10(d_min_nm), np.log10(d_max_nm), n_points)
    E = []
    for i, d_nm in enumerate(d_arr):
        e = casimir_energy_finite_T(eps_static1, eps_static2,
                                     d_nm * 1e-9, T=T, omega_uv=omega_uv)
        E.append(e)
        if (i + 1) % 10 == 0:
            print(f"    {i+1}/{n_points}  d={d_nm:.1f} nm  E={e:.4e} J/m^2")
    return d_arr, np.array(E)


if __name__ == "__main__":
    data_dir = Path(__file__).parent.parent / "data"

    eps_te   = load_eps_static(data_dir / "tellurium.json")
    eps_wte2 = load_eps_static(data_dir / "wte2.json")

    print(f"eps_static (Te)   = {eps_te:.4f}")
    print(f"eps_static (WTe2) = {eps_wte2:.4f}")

    d_nm, E_te   = sweep_separation(eps_te,   1.0, n_points=5)
    d_nm, E_wte2 = sweep_separation(eps_wte2, 1.0, n_points=5)

    for d, e1, e2 in zip(d_nm, E_te, E_wte2):
        print(f"d={d:6.1f} nm  E_Te={e1:.4e}  E_WTe2={e2:.4e}  J/m^2")
