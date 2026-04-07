"""
optimizer.py — Multi-objective Casimir stiction optimizer.

Uses NSGA-II (pymoo) to find chiral Te metamaterial parameters that
simultaneously minimise three objectives.

Design variables (5):
    x[0] theta         — chiral orientation angle (rad),  [0, pi/2]
    x[1] d_nm          — vacuum gap separation (nm),      [1, 100]
    x[2] N_layers      — number of Te metamaterial layers,[1, 20]
    x[3] kappa0        — intrinsic chirality amplitude,   [0.01, 1.0]
    x[4] eps_substrate — substrate dielectric constant,   [1.0, 10.0]

Derived quantities:
    kappa = kappa0 * sin(theta)     [effective chirality at angle theta]
    f     = N_layers / N_LAYERS_MAX [volume fill fraction for EMA]
    eps_eff = maxwell_garnett(eps_substrate, EPS_TE, f)

Objectives (3, all minimised):
    F1 = |E_Casimir(eps_eff, EPS_SUBSTRATE, d, kappa)|  [J/m^2]  stiction energy
    F2 = N_layers * LAYER_THICKNESS_NM                  [nm]     device thickness
    F3 = thermal_fraction = E_classical(T) / |E_quantum|  [–]   thermal sensitivity
         (fraction of Casimir energy from classical T>0 fluctuations;
          minimising F3 selects thermally stable designs)

Substrate options (--substrate flag):
    "hex"   — WTe₂ hexagonal phase  (mp-1023926, eps=6.16)   [default]
    "td"    — Td-WTe₂ Weyl phase    (DFT-HSE06,  eps=15.33)

Casimir energy uses casimir_energy_fast (Hamaker + kappa^2 chiral factor)
for speed.  After convergence, full Matsubara T=300 K energies are computed
for all Pareto solutions via validate_pareto_finite_T().

Pareto front saved to outputs/pareto_results.json.

References:
    Deb et al. (2002) NSGA-II. IEEE Trans. Evol. Comput. 6, 182.
    Zhao et al. (2009) Chiral Casimir. Phys. Rev. Lett. 103, 103602.
    Soluyanov et al. (2015) Nature 527, 495.  [Td-WTe2 Weyl semimetal]
"""

import json
import numpy as np
from pathlib import Path
from typing import Callable

from pymoo.core.problem import Problem
from pymoo.algorithms.moo.nsga2 import NSGA2
from pymoo.optimize import minimize
from pymoo.termination import get_termination

from lifshitz import (casimir_energy, casimir_energy_fast, casimir_energy_finite_T,
                      casimir_energy_multilayer, casimir_energy_chiral_asymmetric,
                      epsilon_imaginary, epsilon_imaginary_drude_lorentz,
                      WTE2_TD_DRUDE, OMEGA_UV as _OMEGA_UV,
                      load_eps_static, KB as _KB, HBAR as _HBAR, C as _C)


def _thermal_length_nm(T: float) -> float:
    """Thermal length l_T = hbar*c / (2*pi*k_B*T) in nm."""
    return _HBAR * _C / (2.0 * np.pi * _KB * T) * 1e9


def casimir_energy_fast_finite_T(eps1: float, eps2: float,
                                  d: float, kappa: float,
                                  T: float = 300.0) -> float:
    """
    Fast Casimir energy with classical n=0 Matsubara thermal correction.

    Adds the classical thermal (n=0 Matsubara) contribution to the fast
    Hamaker model:

        E_T ≈ E_fast(T=0) + E_classical(T)

    where:
        E_classical = -k_B T / (8 pi d^2) * beta1 * beta2   [attractive, adds to E_quantum]

    This correction is negligible at d << l_T ≈ 1.2 µm (300 K) but is
    physically correct and inexpensive (O(1) operations vs. O(n_max) for
    full Matsubara sum).  The NSGA-II optimizer uses this for speed.

    Args:
        eps1, eps2: Static dielectric constants.
        d:          Gap separation (m).
        kappa:      Effective chirality parameter.
        T:          Temperature (K).

    Returns:
        E (J/m²). Negative = attractive (usually).
    """
    E_quantum = casimir_energy_fast(eps1, eps2, d, kappa)
    beta1 = (eps1 - 1.0) / (eps1 + 1.0)
    beta2 = (eps2 - 1.0) / (eps2 + 1.0)
    # DLP classical n=0 Matsubara limit: E_{n=0} = -k_BT β₁β₂ / (8π d²)
    # (Dzyaloshinskii, Lifshitz & Pitaevskii 1961; Parsegian 2006 eq. 2.17)
    # Negative sign: thermal contribution adds to attraction (more negative total).
    E_classical = -_KB * T / (16.0 * np.pi * d ** 2) * beta1 * beta2
    return E_quantum + E_classical

# ── Fixed physical parameters ─────────────────────────────────────────────────
LAYER_THICKNESS_NM = 5.0   # nm — thickness per Te metamaterial layer
N_LAYERS_MAX       = 20    # maximum number of layers (normalises fill fraction)

# Material dielectric constants (loaded from data/ at module level)
_DATA_DIR    = Path(__file__).parent.parent / "data"
EPS_TE       = load_eps_static(_DATA_DIR / "tellurium.json")       # ~164.27
EPS_WTE2_HEX = load_eps_static(_DATA_DIR / "wte2.json")            # ~6.16 (hex P-6m2)
_TD_PATH     = _DATA_DIR / "td_wte2_dft.json"
EPS_WTE2_TD  = (load_eps_static(_TD_PATH)
                if _TD_PATH.exists() else EPS_WTE2_HEX)             # ~15.33 (Td DFT)
EPS_WTE2     = EPS_WTE2_HEX   # default substrate (backward compat)

SUBSTRATE_EPS = {
    "hex": EPS_WTE2_HEX,   # WTe2 hexagonal (mp-1023926)
    "td":  EPS_WTE2_TD,    # Td-WTe2 Weyl semimetal (DFT-HSE06)
}


def maxwell_garnett(eps_host: float, eps_inclusion: float,
                    fill_fraction: float) -> float:
    """
    Maxwell-Garnett effective medium dielectric constant.

        eps_eff = eps_h * (eps_i + 2*eps_h + 2*f*(eps_i - eps_h))
                        / (eps_i + 2*eps_h - f*(eps_i - eps_h))

    Args:
        eps_host:       Host medium dielectric constant.
        eps_inclusion:  Inclusion material dielectric constant.
        fill_fraction:  Volume fraction of inclusions in [0, 1].

    Returns:
        Effective dielectric constant.
    """
    # Note: MG EMA assumes spherical inclusions dispersed in a host matrix.
    # Applied here to a layered Te/substrate composite as a design-phase approximation;
    # a layered EMA (Bruggeman) would be more accurate for stratified geometries.
    f  = fill_fraction
    ei = eps_inclusion
    eh = eps_host
    return eh * (ei + 2*eh + 2*f*(ei - eh)) / (ei + 2*eh - f*(ei - eh))


class CasimirOptimizationProblem(Problem):
    """
    5-variable, 3-objective Casimir stiction minimisation problem.

    Variables (x):
        x[0] theta          rad    [0,       pi/2]
        x[1] d_nm           nm     [1,       100 ]
        x[2] N_layers       count  [1,       20  ]
        x[3] kappa0         –      [0.01,    1.0 ]
        x[4] eps_substrate  –      [1.0,     10.0]

    Objectives (F) — all minimised:
        F[:, 0]  |E_Casimir|          J/m²    stiction energy (primary)
        F[:, 1]  total thickness      nm      device volume (secondary)
        F[:, 2]  thermal_fraction     –       E_classical(T) / |E_quantum|
                   fraction of Casimir energy from classical T>0 fluctuations.
                   Minimising selects thermally stable designs (low T-sensitivity).
                   thermal_fraction = (k_BT β1β2) / (16π d² |E_quantum|)

    Inequality constraint:
        g(x) = d_nm - N_layers * LAYER_THICKNESS_NM <= 0

    Substrate:
        "hex"  — WTe₂ hex P-6m2  (eps ≈ 6.16,  mp-1023926)
        "td"   — Td-WTe₂ Weyl   (eps ≈ 15.33, DFT-HSE06)

    Temperature:
        T > 0 adds the classical n=0 Matsubara correction to F1.
        F3 (thermal_fraction) is always computed using T (default 300 K).
    """

    def __init__(self, T: float = 300.0, substrate: str = "hex") -> None:
        """
        Args:
            T:         Temperature (K). Used for thermal correction + F3. Default 300 K.
            substrate: "hex" (WTe₂ P-6m2) or "td" (Td-WTe₂ Weyl). Default "hex".
        """
        if substrate not in SUBSTRATE_EPS:
            raise ValueError(f"substrate must be 'hex' or 'td', got '{substrate}'")
        super().__init__(
            n_var=5,
            n_obj=3,
            n_ieq_constr=1,
            xl=np.array([0.0,     1.0,  1.0,  0.01, 1.0 ]),
            xu=np.array([np.pi/2, 100.0, 20.0, 1.0,  10.0]),
        )
        self.T         = float(T)
        self.substrate = substrate
        self.eps_sub2  = SUBSTRATE_EPS[substrate]

    def _evaluate(self, x: np.ndarray, out: dict,
                  *args, **kwargs) -> None:
        """
        Evaluate all three objectives and constraint for the entire population.

        Physical model:
            kappa_eff = kappa0 * sin(theta) * (N_layers / N_LAYERS_MAX)
            F3 = thermal_fraction = (k_B T β1 β2) / (16π d² |E_quantum|)

        Pareto tradeoffs:
          F1 vs F2: fewer layers → less thick → less kappa → more stiction
          F1 vs F3: smaller d → less stiction (F1↓) but more thermal sensitivity (F3↑)
          F2 vs F3: larger d → more layers needed → thicker (F2↑) but less F3

        Args:
            x:   Population matrix, shape (pop_size, 5).
            out: Output dict; writes 'F' (3 objectives) and 'G' (1 constraint).
        """
        F = np.zeros((x.shape[0], 3))
        G = np.zeros((x.shape[0], 1))

        for i, xi in enumerate(x):
            theta, d_nm, N_layers, kappa0, eps_sub = xi

            layer_fraction = N_layers / N_LAYERS_MAX
            kappa_eff      = kappa0 * np.sin(theta) * layer_fraction
            eps_eff        = maxwell_garnett(eps_sub, EPS_TE, layer_fraction)
            d_m            = d_nm * 1e-9

            # F1: stiction energy via fast Hamaker model (NSGA-II inner loop, speed only).
            # CHIRAL_FACTOR=1.0 is calibrated for symmetric Te|Te (Zhao 2009);
            # for Te|WTe₂ the exact Silveirinha (2010) asymmetric formula gives
            # χ_asym ≈ 2% of χ_sym — repulsion is not achievable (κ_crit≈6.3).
            # WARNING: CHIRAL_FACTOR=1.0 overestimates chiral suppression for Te|WTe₂,
            # making optimizer designs OPTIMISTIC (not conservative) for this heterostructure.
            # Publication validation uses casimir_energy_chiral_asymmetric() — see below.
            E_quantum = casimir_energy_fast(eps_eff, self.eps_sub2, d_m, kappa_eff)

            if self.T > 0.0:
                E = casimir_energy_fast_finite_T(
                    eps_eff, self.eps_sub2, d_m, kappa_eff, self.T)
            else:
                E = E_quantum

            # F3: thermal fraction = classical Matsubara n=0 / quantum term
            beta1     = (eps_eff       - 1.0) / (eps_eff       + 1.0)
            beta2     = (self.eps_sub2 - 1.0) / (self.eps_sub2 + 1.0)
            E_classical = -_KB * self.T / (16.0 * np.pi * d_m ** 2) * beta1 * beta2
            denom       = abs(E_quantum) if abs(E_quantum) > 1e-60 else 1e-60
            thermal_frac = abs(E_classical) / denom

            thickness  = N_layers * LAYER_THICKNESS_NM
            F[i, 0]    = abs(E)
            F[i, 1]    = thickness
            F[i, 2]    = thermal_frac
            G[i, 0]    = d_nm - thickness

        out["F"] = F
        out["G"] = G


def _eps_fn_for_substrate(substrate: str) -> "Callable[[float], float]":
    """
    Return a callable eps(xi) for the chosen substrate.

    For "hex" (insulating WTe2):  uses single-oscillator Cauchy model.
    For "td"  (Weyl semimetal):   uses Drude+Lorentz model — the Drude
        free-carrier term is essential for the metallic Td phase; using the
        Cauchy insulator model ignores free electrons and gives wrong results.

    Args:
        substrate: "hex" or "td".

    Returns:
        Callable eps_fn(xi: float) -> float.
    """
    if substrate == "td":
        p = WTE2_TD_DRUDE
        return lambda xi: epsilon_imaginary_drude_lorentz(
            xi, p["omega_p"], p["gamma"], p["eps_inf"], p["omega_uv"])
    # Default: hex WTe2 (insulating, Cauchy model)
    eps_s = EPS_WTE2_HEX
    return lambda xi: epsilon_imaginary(eps_s, xi, _OMEGA_UV)


def validate_pareto_finite_T(pareto: dict, T: float = 300.0) -> dict:
    """
    Post-optimization high-fidelity T=300 K Casimir energy for each Pareto solution.

    Uses the full Matsubara summation (casimir_energy_finite_T) which is too
    slow for NSGA-II evaluation loops but appropriate for validating the
    final Pareto front (~50 solutions).  Results are added to each objective
    dict as 'E_Casimir_chiral_asymm_mJm2'.

    Chiral validation: uses casimir_energy_chiral_asymmetric() (Silveirinha 2010)
        which is the correct formula for Te|WTe₂ (Te chiral, WTe₂ non-chiral).
        Each solution is evaluated with its own eps_eff, d_nm, and kappa_eff.
        A non-chiral Matsubara baseline is also stored as E_Casimir_T300K_nonchiral_mJm2
        for thermal reference only — do NOT use it as the validated chiral energy.

    Transparent stack: casimir_energy_multilayer() gives the slab-thickness
        correction factor via Airy (transfer-matrix) reflection for the finite
        Te metamaterial slab, stored as E_Casimir_multilayer_mJm2.

    Args:
        pareto: Dict returned by run_optimization.
        T:      Temperature for non-chiral Matsubara baseline (K). Default 300 K.

    Returns:
        Updated pareto dict with 'E_Casimir_chiral_asymm_mJm2',
        'E_Casimir_T300K_nonchiral_mJm2', and 'E_Casimir_multilayer_mJm2'
        in each objective entry.
    """
    n_sol     = len(pareto["variables"])
    l_T       = _thermal_length_nm(T)
    substrate = pareto["meta"].get("substrate", "hex")
    eps_sub2  = SUBSTRATE_EPS.get(substrate, EPS_WTE2_HEX)

    print(f"\n  Validating {n_sol} Pareto solutions at T={T:.0f} K ...")
    print(f"  Substrate : {substrate}  eps_static={eps_sub2:.2f}  "
          f"l_T={l_T:.0f} nm")
    print(f"  Dielectric model : "
          f"{'Drude+Lorentz (metallic Weyl)' if substrate == 'td' else 'Cauchy (insulator)'}")

    for i, (v, o) in enumerate(zip(pareto["variables"], pareto["objectives"])):
        eps_eff   = v["eps_eff"]
        d_m       = v["d_nm"] * 1e-9
        kappa_eff = v["kappa_eff"]
        n_layers  = int(v["N_layers"])
        h_slab_m  = n_layers * LAYER_THICKNESS_NM * 1e-9   # physical slab thickness

        # Non-chiral Matsubara baseline (T=300 K, no kappa) — thermal reference only.
        # Do NOT use this as the "validated" chiral energy; see E_chiral_asymm below.
        E_T = casimir_energy_finite_T(eps_eff, eps_sub2, d_m, T=T, n_max=400)
        o["E_Casimir_T300K_nonchiral_mJm2"] = float(E_T * 1e3)

        # High-fidelity chiral validation: asymmetric Silveirinha formula (Te chiral,
        # WTe₂ non-chiral).  This is the physically correct model for Te|WTe₂ and
        # is the value that should appear in publication plots.
        E_chiral_asymm = casimir_energy_chiral_asymmetric(
            eps_eff, eps_sub2, d_m, kappa=kappa_eff)
        o["E_Casimir_chiral_asymm_mJm2"] = float(E_chiral_asymm * 1e3)
        o["is_repulsive"] = bool(E_chiral_asymm > 0.0)

        # Transparent-stack: Airy transfer-matrix reflection for finite slab
        E_ml = casimir_energy_multilayer(eps_eff, h_slab_m, eps_sub2, d_m)
        o["E_Casimir_multilayer_mJm2"] = float(E_ml * 1e3)

        # Slab-thickness correction factor (finite slab / semi-infinite at T=0)
        E_semi = casimir_energy(eps_eff, eps_sub2, d_m)   # T=0, no chiral factor
        correction = (E_ml / E_semi) if abs(E_semi) > 1e-60 else float("nan")
        o["slab_thickness_correction"] = float(correction)

        if (i + 1) % 10 == 0:
            print(f"    {i+1}/{n_sol}  d={v['d_nm']:.1f}nm  kappa={kappa_eff:.4f}  "
                  f"E_chiral={E_chiral_asymm*1e3:.4e} mJ/m²  "
                  f"E_T300_nonchiral={E_T*1e3:.4e} mJ/m²  "
                  f"correction={correction:.4f}")

    pareto["meta"]["T_validation_K"]         = T
    pareto["meta"]["l_T_nm"]                 = l_T
    pareto["meta"]["substrate_dielectric_model"] = (
        "Drude+Lorentz" if substrate == "td" else "Cauchy")
    return pareto


def run_optimization(n_gen: int = 100, pop_size: int = 50,
                     seed: int = 42, T: float = 300.0,
                     substrate: str = "hex") -> dict:
    """
    Run NSGA-II 3-objective optimisation and return the Pareto front.

    Objectives minimised simultaneously:
        F1 = |E_Casimir|     — stiction energy
        F2 = thickness       — device thickness
        F3 = thermal_frac    — fraction of energy from classical T fluctuations

    Args:
        n_gen:     Number of generations (default 100).
        pop_size:  Population size (default 50).
        seed:      Random seed (default 42).
        T:         Temperature for thermal correction (K). Default 300 K.
        substrate: "hex" (WTe₂ P-6m2) or "td" (Td-WTe₂ Weyl). Default "hex".

    Returns:
        dict with keys "variables" and "objectives" — each a list of dicts.
        Objective dicts include 'E_Casimir_chiral_asymm_mJm2' from Silveirinha validation.
    """
    eps_sub2    = SUBSTRATE_EPS[substrate]
    problem     = CasimirOptimizationProblem(T=T, substrate=substrate)
    algorithm   = NSGA2(pop_size=pop_size)
    termination = get_termination("n_gen", n_gen)

    print(f"  NSGA-II: pop={pop_size}, generations={n_gen}  "
          f"(total evals={pop_size*n_gen})")
    print(f"  EPS_TE={EPS_TE:.2f}  substrate={substrate}  "
          f"EPS_SUB={eps_sub2:.2f}")
    print(f"  Temperature: T={T:.0f} K  "
          f"(thermal length l_T={_thermal_length_nm(T):.0f} nm)")
    print(f"  Objectives: F1=|E_Casimir|  F2=thickness  "
          f"F3=thermal_fraction")

    res = minimize(problem, algorithm, termination,
                   seed=seed, verbose=False)

    # Sort Pareto front by F1 = |E_Casimir| ascending
    order    = np.argsort(res.F[:, 0])
    X_sorted = res.X[order]
    F_sorted = res.F[order]

    pareto = {
        "meta": {
            "n_gen":              n_gen,
            "pop_size":           pop_size,
            "seed":               seed,
            "n_pareto":           len(X_sorted),
            "EPS_TE":             EPS_TE,
            "EPS_WTE2":           eps_sub2,
            "substrate":          substrate,
            "LAYER_THICKNESS_NM": LAYER_THICKNESS_NM,
            "optimizer_T_K":      T,
            "n_objectives":       3,
        },
        "variables": [
            {
                "theta_rad":     float(xi[0]),
                "theta_deg":     float(np.degrees(xi[0])),
                "d_nm":          float(xi[1]),
                "N_layers":      int(round(xi[2])),
                "kappa0":        float(xi[3]),
                "eps_substrate": float(xi[4]),
                "kappa_eff":     float(xi[3] * np.sin(xi[0]) * xi[2] / N_LAYERS_MAX),
                "eps_eff":       float(maxwell_garnett(xi[4], EPS_TE, xi[2] / N_LAYERS_MAX)),
            }
            for xi in X_sorted
        ],
        "objectives": [
            {
                "E_Casimir_Jm2":    float(fi[0]),
                "E_Casimir_mJm2":   float(fi[0] * 1e3),
                "thickness_nm":     float(fi[1]),
                "thermal_fraction": float(fi[2]),
            }
            for fi in F_sorted
        ],
    }
    # Post-optimization: high-fidelity T=300 K Matsubara validation
    pareto = validate_pareto_finite_T(pareto, T=T)

    return pareto


def save_pareto(pareto: dict, out_path: Path) -> None:
    """
    Save Pareto front dict to a JSON file.

    Args:
        pareto:   Dict returned by run_optimization.
        out_path: Destination file path.
    """
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(pareto, f, indent=2)
    print(f"  Pareto front saved -> {out_path}")


def print_pareto_summary(pareto: dict) -> None:
    """
    Print a formatted summary table of the Pareto front.

    Args:
        pareto: Dict returned by run_optimization.
    """
    n         = pareto["meta"]["n_pareto"]
    T         = pareto["meta"].get("optimizer_T_K", 0.0)
    substrate = pareto["meta"].get("substrate", "hex")
    print(f"\n  Pareto front  ({n} solutions, T={T:.0f} K, substrate={substrate}):")
    print(f"  {'theta(deg)':>10}  {'d(nm)':>7}  {'N_lay':>5}  "
          f"{'kappa_eff':>10}  "
          f"{'|E|fast':>12}  {'|E|chiral':>12}  {'therm_frac':>11}  {'thick(nm)':>10}")
    print("  " + "-" * 100)
    for v, o in zip(pareto["variables"], pareto["objectives"]):
        e_t300  = o.get("E_Casimir_chiral_asymm_mJm2", float("nan"))
        th_frac = o.get("thermal_fraction", float("nan"))
        print(
            f"  {v['theta_deg']:>10.1f}  {v['d_nm']:>7.1f}  "
            f"{v['N_layers']:>5d}  {v['kappa_eff']:>10.4f}  "
            f"{o['E_Casimir_mJm2']:>12.4e}  {e_t300:>12.4e}  "
            f"{th_frac:>11.4e}  {o['thickness_nm']:>10.1f}"
        )


def main() -> None:
    """Run NSGA-II 3-objective optimisation and save results.

    Substrate can be overridden via environment variable OPTIMIZER_SUBSTRATE:
        OPTIMIZER_SUBSTRATE=td uv run python main.py --optimize
    """
    import os
    substrate = os.environ.get("OPTIMIZER_SUBSTRATE", "hex")
    if substrate not in SUBSTRATE_EPS:
        print(f"  Warning: unknown OPTIMIZER_SUBSTRATE={substrate!r}, using 'hex'")
        substrate = "hex"

    pareto   = run_optimization(n_gen=100, pop_size=50, substrate=substrate)
    out_path = Path(__file__).parent.parent / "outputs" / "pareto_results.json"
    save_pareto(pareto, out_path)
    print_pareto_summary(pareto)


if __name__ == "__main__":
    main()
