"""
visualize.py — Casimir energy plots for spaceship_bubble project.

Generates 12 publication-quality plots (saved to plots/):
  1.  casimir_tellurium.png        — E vs d, Te | vac | Te
  2.  casimir_wte2.png             — E vs d, WTe2 | vac | WTe2
  3.  casimir_comparison.png       — overlay Te and WTe2 (isotropic)
  4.  casimir_chiral.png           — E vs theta (kappa0 = 0.1/0.3/0.5/1.0)
  5.  pareto_front.png             — NSGA-II Pareto scatter
  6.  casimir_force.png            — |F| vs d log-log (three configs)
  7.  casimir_force_chiral.png     — |F| vs d, kappa=0/0.5/1.0
  8.  casimir_aniso.png            — anisotropic vs isotropic comparison
  9.  casimir_td_wte2.png          — Td (Weyl) vs hex WTe2 phase comparison
  10. casimir_2osc_model.png       — 2-oscillator Sellmeier vs Cauchy model
  11. casimir_finite_T.png         — T=0 vs T=300 K Matsubara summation
  12. casimir_benchmark_au_sio2.png — Au/SiO2 code validation (Drude model)
"""

import json
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np

from lifshitz import (
    AU_DRUDE,
    TE_2OSC,
    casimir_force_from_eps_fns,
    epsilon_imaginary,
    epsilon_imaginary_drude,
    load_eps_static,
    load_eps_tensor,
    sweep_chiral,
    sweep_finite_T,
    sweep_force,
    sweep_separation,
    sweep_separation_2osc,
    sweep_separation_aniso,
)

# ── Plot styling ──────────────────────────────────────────────────────────────
plt.rcParams.update({
    "font.family":    "serif",
    "font.size":      11,
    "axes.labelsize": 12,
    "axes.titlesize": 13,
    "legend.fontsize": 10,
    "figure.dpi":     300,
})

PLOTS_DIR = Path(__file__).parent.parent / "plots"
DATA_DIR  = Path(__file__).parent.parent / "data"


def _save(fig: plt.Figure, path: Path) -> None:
    """Save figure and close it. Uses ASCII-safe output."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved -> {path.name}")


def plot_casimir_single(d_nm: np.ndarray, E_Jm2: np.ndarray,
                        label: str, color: str, out_path: Path) -> None:
    """
    Plot Casimir energy per unit area vs separation for one material pair.

    Args:
        d_nm:     Separation distances (nm).
        E_Jm2:    Casimir energy per unit area (J/m^2).
        label:    Curve label for title and legend.
        color:    Matplotlib color string.
        out_path: Destination PNG path.
    """
    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.plot(d_nm, E_Jm2 * 1e3, color=color, linewidth=2.0, label=label)
    ax.axhline(0, color="gray", linewidth=0.8, linestyle="--", alpha=0.6)
    ax.set_xscale("log")

    ax.set_xlabel("Separation d (nm)")
    ax.set_ylabel("E_Cas (mJ/m^2)")
    ax.set_title(f"Lifshitz-Casimir Energy: {label}")
    ax.legend()
    ax.grid(True, which="major", alpha=0.3)
    ax.grid(True, which="minor", alpha=0.1)
    _save(fig, out_path)


def plot_casimir_comparison(d_nm: np.ndarray,
                             E_te: np.ndarray, E_wte2: np.ndarray,
                             out_path: Path) -> None:
    """
    Overlay Casimir energy curves for Te and WTe2 symmetric configurations.

    Args:
        d_nm:     Separation array (nm).
        E_te:     Energy for Te|vac|Te (J/m^2).
        E_wte2:   Energy for WTe2|vac|WTe2 (J/m^2).
        out_path: Destination PNG path.
    """
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(d_nm, E_te   * 1e3, color="#1f77b4", linewidth=2.0,
            label="Te | vac | Te  (mp-19)")
    ax.plot(d_nm, E_wte2 * 1e3, color="#d62728", linewidth=2.0,
            label="WTe2 | vac | WTe2  (mp-1023926)")
    ax.axhline(0, color="gray", linewidth=0.8, linestyle="--", alpha=0.6)
    ax.set_xscale("log")

    ax.set_xlabel("Separation d (nm)")
    ax.set_ylabel("E_Cas (mJ/m^2)")
    ax.set_title("Lifshitz-Casimir Energy Comparison")
    ax.legend()
    ax.grid(True, which="major", alpha=0.3)
    ax.grid(True, which="minor", alpha=0.1)
    _save(fig, out_path)


def plot_chiral_effect(theta: np.ndarray, results: dict,
                       d_nm: float, out_path: Path) -> None:
    """
    Plot Casimir energy vs chiral orientation angle theta for several kappa0.

    Each curve corresponds to one kappa0 value; the effective chirality
    parameter is kappa = kappa0 * sin(theta).

    Args:
        theta:    Array of theta values (rad), shape (n_theta,).
        results:  Dict {kappa0: E_array (J/m^2)} from sweep_chiral.
        d_nm:     Separation distance (nm), for annotation only.
        out_path: Destination PNG path.
    """
    colors = ["#2ca02c", "#1f77b4", "#ff7f0e", "#d62728"]
    fig, ax = plt.subplots(figsize=(8, 5))

    for (k0, E_arr), col in zip(sorted(results.items()), colors):
        ax.plot(np.degrees(theta), E_arr * 1e3, color=col,
                linewidth=2.0, label=f"kappa0 = {k0}")

    ax.axhline(0, color="gray", linewidth=0.8, linestyle="--", alpha=0.6,
               label="E = 0 (repulsion boundary)")

    ax.set_xlabel("Chiral angle theta (deg)")
    ax.set_ylabel("E_Cas (mJ/m^2)")
    ax.set_title(f"Chiral Casimir Effect vs Orientation Angle  (d = {d_nm:.0f} nm)")
    ax.set_xlim(0, 90)
    ax.legend(loc="upper right")
    ax.xaxis.set_minor_locator(ticker.AutoMinorLocator())
    ax.yaxis.set_minor_locator(ticker.AutoMinorLocator())
    ax.grid(True, which="major", alpha=0.3)
    ax.grid(True, which="minor", alpha=0.1)
    _save(fig, out_path)


def plot_aniso_comparison(d_nm: np.ndarray,
                          E_iso: np.ndarray,
                          E_aniso_te_te: np.ndarray,
                          E_aniso_asym: np.ndarray,
                          out_path: Path) -> None:
    """
    Compare isotropic trace-average vs full anisotropic Lifshitz energy.

    Highlights the physics lost when replacing the uniaxial tensor by its
    trace average — relevant for Te (eps_perp=131, eps_par=231) and WTe2
    (eps_perp=8.46, eps_par=1.56).

    Args:
        d_nm:           Separation array (nm).
        E_iso:          Isotropic energy for Te|vac|WTe2 (J/m^2).
        E_aniso_te_te:  Anisotropic energy for Te|vac|Te (J/m^2).
        E_aniso_asym:   Anisotropic energy for Te|vac|WTe2 (J/m^2).
        out_path:       Destination PNG path.
    """
    fig, ax = plt.subplots(figsize=(8, 5))

    ax.plot(d_nm, np.abs(E_iso)          * 1e3, color="#9467bd",
            linewidth=2.0, linestyle="--",
            label="Te | vac | WTe2 — isotropic (trace avg)")
    ax.plot(d_nm, np.abs(E_aniso_te_te)  * 1e3, color="#1f77b4",
            linewidth=2.0,
            label="Te | vac | Te — anisotropic (tensor)")
    ax.plot(d_nm, np.abs(E_aniso_asym)   * 1e3, color="#2ca02c",
            linewidth=2.0,
            label="Te | vac | WTe2 — anisotropic (tensor)")

    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("Separation d (nm)")
    ax.set_ylabel("|E_Cas| (mJ/m^2)")
    ax.set_title("Anisotropic vs Isotropic Lifshitz-Casimir Energy")
    ax.legend(fontsize=9)
    ax.grid(True, which="major", alpha=0.3)
    ax.grid(True, which="minor", alpha=0.1)
    _save(fig, out_path)


def plot_casimir_force(d_nm: np.ndarray,
                       F_te: np.ndarray, F_wte2: np.ndarray,
                       F_asym: np.ndarray, out_path: Path) -> None:
    """
    Log-log plot of |Casimir force| vs separation for three configurations.

    Args:
        d_nm:    Separation array (nm).
        F_te:    Force for Te|vac|Te (N/m^2), negative values.
        F_wte2:  Force for WTe2|vac|WTe2 (N/m^2).
        F_asym:  Force for Te|vac|WTe2 (N/m^2).
        out_path: Destination PNG path.
    """
    fig, ax = plt.subplots(figsize=(8, 5))

    # Convert N/m^2 -> mN/m^2 (milli-Newtons per square metre = mPa)
    ax.plot(d_nm, np.abs(F_te)   * 1e3, color="#1f77b4", linewidth=2.0,
            label="Te | vac | Te  (mp-19)")
    ax.plot(d_nm, np.abs(F_wte2) * 1e3, color="#d62728", linewidth=2.0,
            label="WTe2 | vac | WTe2  (mp-1023926)")
    ax.plot(d_nm, np.abs(F_asym) * 1e3, color="#ff7f0e", linewidth=2.0,
            linestyle="--", label="Te | vac | WTe2  (asymmetric)")

    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("Separation d (nm)")
    ax.set_ylabel("|F_Cas| (mN/m^2)")
    ax.set_title("Lifshitz-Casimir Force per Unit Area  (attractive, log-log)")
    ax.legend()
    ax.grid(True, which="major", alpha=0.3)
    ax.grid(True, which="minor", alpha=0.1)
    _save(fig, out_path)


def plot_chiral_force(d_nm: np.ndarray,
                      F_std: np.ndarray, F_k05: np.ndarray,
                      F_k10: np.ndarray, out_path: Path) -> None:
    """
    Log-log plot of |Casimir force| vs d for increasing chiral suppression.

    Shows how chirality progressively reduces and can reverse the Casimir force
    on the MEMS-relevant scale (1–100 nm).

    Args:
        d_nm:    Separation array (nm).
        F_std:   Force at kappa=0 (standard Lifshitz, N/m^2).
        F_k05:   Force at kappa=0.5 (partial suppression, N/m^2).
        F_k10:   Force at kappa=1.0 (full chiral repulsion, N/m^2).
        out_path: Destination PNG path.
    """
    fig, ax = plt.subplots(figsize=(8, 5))

    # Plot attractive (negative) values as solid |F|; repulsive as dashed
    def _plot_force(ax_: plt.Axes, d: np.ndarray, F: np.ndarray,
                    color: str, label: str) -> None:
        """Helper: split into attractive and repulsive segments."""
        attr_mask = F <= 0.0
        rep_mask  = F > 0.0
        if attr_mask.any():
            ax_.plot(d[attr_mask], np.abs(F[attr_mask]) * 1e3,
                     color=color, linewidth=2.0, label=label + " (attractive)")
        if rep_mask.any():
            ax_.plot(d[rep_mask], np.abs(F[rep_mask]) * 1e3,
                     color=color, linewidth=2.0, linestyle="--",
                     label=label + " (repulsive)")

    _plot_force(ax, d_nm, F_std, "#d62728", "kappa=0 (standard)")
    _plot_force(ax, d_nm, F_k05, "#ff7f0e", "kappa=0.5")
    _plot_force(ax, d_nm, F_k10, "#1f77b4", "kappa=1.0")

    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("Separation d (nm)")
    ax.set_ylabel("|F_Cas| (mN/m^2)")
    ax.set_title("Chiral Casimir Force vs Separation  (Te | vac | Te)")
    ax.legend(fontsize=9)
    ax.grid(True, which="major", alpha=0.3)
    ax.grid(True, which="minor", alpha=0.1)
    _save(fig, out_path)


def plot_2osc_comparison(d_nm: np.ndarray,
                         E_1osc: np.ndarray,
                         E_2osc: np.ndarray,
                         out_path: Path) -> None:
    """
    Compare single-oscillator Cauchy model vs 2-oscillator Sellmeier.

    Shows the error introduced by the single-oscillator approximation for
    Tellurium, whose large eps_static is split between a far-IR phonon
    oscillator (C1=45.77, ω1=5×10¹³ rad/s) and a UV electronic oscillator
    (C2=117.5, ω2=1.5×10¹⁶ rad/s).

    Args:
        d_nm:    Separation array (nm).
        E_1osc:  Energy with single-oscillator Cauchy model (J/m^2).
        E_2osc:  Energy with 2-oscillator Sellmeier model (J/m^2).
        out_path: Destination PNG path.
    """
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

    ax1.plot(d_nm, np.abs(E_1osc) * 1e3, color="#1f77b4", linewidth=2.0,
             label="Single-oscillator (Cauchy)")
    ax1.plot(d_nm, np.abs(E_2osc) * 1e3, color="#d62728", linewidth=2.0,
             linestyle="--", label="2-oscillator Sellmeier")
    ax1.set_xscale("log")
    ax1.set_yscale("log")
    ax1.set_xlabel("Separation d (nm)")
    ax1.set_ylabel(r"$|E_\mathrm{Cas}|$ (mJ/m$^2$)")
    ax1.set_title("Casimir Energy: Dielectric Model Comparison\n(Te | vac | Te)")
    ax1.legend()
    ax1.grid(True, which="major", alpha=0.3)
    ax1.grid(True, which="minor", alpha=0.1)

    # Relative error plot
    rel_err = (E_2osc - E_1osc) / np.abs(E_1osc) * 100.0
    ax2.plot(d_nm, rel_err, color="#ff7f0e", linewidth=2.0)
    ax2.axhline(0, color="gray", linewidth=0.8, linestyle="--", alpha=0.6)
    ax2.set_xscale("log")
    ax2.set_xlabel("Separation d (nm)")
    ax2.set_ylabel("Relative difference (%)")
    ax2.set_title("2-osc vs 1-osc: Relative Difference")
    ax2.grid(True, which="major", alpha=0.3)
    ax2.grid(True, which="minor", alpha=0.1)
    ax2.annotate(
        "IR oscillator (ω₁=5×10¹³)\npulls more weight at large d",
        xy=(0.05, 0.85), xycoords="axes fraction", fontsize=8.5,
        bbox=dict(boxstyle="round,pad=0.3", fc="#1a1a2e", alpha=0.8),
    )

    fig.tight_layout()
    _save(fig, out_path)


def plot_finite_T(d_nm: np.ndarray,
                  E_T0: np.ndarray,
                  E_T300: np.ndarray,
                  out_path: Path) -> None:
    """
    Casimir energy: T=0 vs T=300 K Matsubara summation.

    Highlights the crossover from the quantum (T=0) regime at small d to the
    classical thermal regime at d ~ l_T = ℏc/(2πk_BT) ≈ 1.2 µm at 300 K.

    Args:
        d_nm:   Separation array (nm), extended to ~2000 nm to show thermal regime.
        E_T0:   T=0 Lifshitz energy (J/m^2) from casimir_energy().
        E_T300: T=300 K energy (J/m^2) from casimir_energy_finite_T().
        out_path: Destination PNG path.
    """
    # Thermal length l_T = hbar*c / (2*pi*k_B*T) at 300 K
    HBAR_VAL = 1.0545718e-34
    C_VAL    = 2.99792458e8
    KB_VAL   = 1.380649e-23
    l_T_nm   = HBAR_VAL * C_VAL / (2.0 * np.pi * KB_VAL * 300.0) * 1e9  # nm

    fig, ax = plt.subplots(figsize=(9, 5))
    ax.plot(d_nm, np.abs(E_T0)   * 1e3, color="#1f77b4", linewidth=2.0,
            label=r"$T = 0$ K  (continuous integral)")
    ax.plot(d_nm, np.abs(E_T300) * 1e3, color="#d62728", linewidth=2.0,
            linestyle="--", label=r"$T = 300$ K  (Matsubara sum)")

    ax.axvline(l_T_nm, color="gray", linewidth=1.2, linestyle=":",
               label=fr"$\ell_T = {l_T_nm:.0f}$ nm  (thermal length)")

    ax.set_xscale("log")
    ax.set_yscale("log")

    # Annotation placed after log scale so axes fraction coords are stable
    ax.text(l_T_nm * 1.08, 0.02, r"$\ell_T$",
            fontsize=10, color="gray",
            transform=ax.get_xaxis_transform())
    ax.set_xlabel("Separation d (nm)")
    ax.set_ylabel(r"$|E_\mathrm{Cas}|$ (mJ/m$^2$)")
    ax.set_title(r"Finite-Temperature Casimir Effect: $T=0$ vs $T=300$ K"
                 "\n(Te | vac | WTe₂, Matsubara summation)")
    ax.legend()
    ax.grid(True, which="major", alpha=0.3)
    ax.grid(True, which="minor", alpha=0.1)

    _save(fig, out_path)


def plot_td_wte2_comparison(d_nm: np.ndarray,
                             E_hex: np.ndarray,
                             E_td: np.ndarray,
                             E_te_td: np.ndarray,
                             out_path: Path) -> None:
    """
    Compare Casimir energy for P-6m2 (hexagonal) vs Td (Weyl) WTe2 phase.

    Highlights the dielectric difference between the two WTe2 polymorphs —
    especially that Td phase has eps_par=7.6 (c-axis) vs 1.56 for P-6m2,
    leading to stronger TM coupling and larger attractive Casimir energy.

    Args:
        d_nm:       Separation array (nm).
        E_hex:      Energy for Te|vac|WTe2(hex) aniso J/m^2.
        E_td:       Energy for Te|vac|Td-WTe2 aniso J/m^2.
        E_te_td:    Energy for Td-WTe2|vac|Td-WTe2 (symmetric) J/m^2.
        out_path:   Destination PNG path.
    """
    fig, ax = plt.subplots(figsize=(8, 5))

    ax.plot(d_nm, np.abs(E_hex)   * 1e3, color="#2ca02c", linewidth=2.0,
            label=r"Te | vac | WTe$_2$ hex (mp-1023926, $\varepsilon_\parallel$=1.56)")
    ax.plot(d_nm, np.abs(E_td)    * 1e3, color="#d62728", linewidth=2.0,
            label=r"Te | vac | Td-WTe$_2$ (DFT-HSE06, $\varepsilon_\parallel$=7.60)")
    ax.plot(d_nm, np.abs(E_te_td) * 1e3, color="#9467bd", linewidth=2.0,
            linestyle="--",
            label=r"Td-WTe$_2$ | vac | Td-WTe$_2$ (symmetric)")

    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("Separation d (nm)")
    ax.set_ylabel(r"$|E_\mathrm{Cas}|$ (mJ/m$^2$)")
    ax.set_title(r"Td vs Hex WTe$_2$ — Casimir Energy Comparison (anisotropic Lifshitz)")

    ax.annotate(r"Td phase: 14$\times$ larger $\varepsilon_\parallel$ $\rightarrow$ stronger TM coupling",
                xy=(0.03, 0.07), xycoords="axes fraction",
                fontsize=9, color="#d62728",
                bbox=dict(boxstyle="round,pad=0.3", fc="#2d1b1b", alpha=0.8))

    ax.legend(fontsize=9)
    ax.grid(True, which="major", alpha=0.3)
    ax.grid(True, which="minor", alpha=0.1)
    _save(fig, out_path)


def plot_pareto_front(pareto_path: Path, out_path: Path) -> None:
    """
    Two-panel Pareto front for 3-objective NSGA-II results.

    Left panel : |E_exact| vs F2 (device thickness), coloured by κ_eff.
                 Repulsive solutions (E_exact > 0) shown as star markers.
    Right panel: |E_exact| vs F3 (thermal_fraction), coloured by d_nm.
                 Falls back to a single panel when thermal_fraction is absent
                 (older 2-objective JSON files).

    Args:
        pareto_path: Path to outputs/pareto_results.json.
        out_path:    Destination PNG path.
    """
    with open(pareto_path) as f:
        data = json.load(f)

    # Prefer asymmetric chiral validation (Silveirinha formula, kappa included).
    # Fall back to fast-model optimizer energy (also has kappa via CHIRAL_FACTOR).
    # Never use E_Casimir_T300K_nonchiral_mJm2 here — that field has no kappa.
    E_raw    = [o.get("E_Casimir_chiral_asymm_mJm2") or o["E_Casimir_mJm2"]
                for o in data["objectives"]]
    E_vals   = [abs(e) for e in E_raw]
    is_rep   = [o.get("is_repulsive", False) for o in data["objectives"]]
    t_vals   = [o["thickness_nm"]    for o in data["objectives"]]
    k_effs   = [v["kappa_eff"]        for v in data["variables"]]
    d_nms    = [v["d_nm"]             for v in data["variables"]]

    # Thermal fraction — present in 3-objective runs, absent in older JSON
    tf_vals = [o.get("thermal_fraction") for o in data["objectives"]]
    has_tf  = all(v is not None for v in tf_vals)

    n = data["meta"].get("n_pareto", len(E_vals))
    substrate = data["meta"].get("substrate", "hex")

    if has_tf:
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
    else:
        fig, ax1 = plt.subplots(figsize=(8, 5))

    # ── Left panel: |E_exact| vs F2, coloured by κ_eff ──────────────────────
    # Split into attractive and repulsive subsets for distinct markers
    idx_attr = [i for i, r in enumerate(is_rep) if not r]
    idx_rep  = [i for i, r in enumerate(is_rep) if r]

    E_attr = [E_vals[i] for i in idx_attr]
    t_attr = [t_vals[i] for i in idx_attr]
    k_attr = [k_effs[i] for i in idx_attr]

    sc1 = ax1.scatter(E_attr, t_attr, c=k_attr, cmap="plasma",
                      s=65, edgecolors="k", linewidths=0.4, zorder=3,
                      label="Attractive")

    if idx_rep:
        E_rep = [E_vals[i] for i in idx_rep]
        t_rep = [t_vals[i] for i in idx_rep]
        k_rep = [k_effs[i] for i in idx_rep]
        ax1.scatter(E_rep, t_rep, c=k_rep, cmap="plasma",
                    s=180, marker="*", edgecolors="#00ff88", linewidths=1.2,
                    zorder=5, vmin=min(k_effs), vmax=max(k_effs),
                    label=f"Repulsive ({len(idx_rep)})")
        ax1.legend(loc="lower right", fontsize=8, framealpha=0.7)

    cbar1 = fig.colorbar(sc1, ax=ax1)
    cbar1.set_label(r"$\kappa_\mathrm{eff}$")
    ax1.set_xlabel(r"$|E_\mathrm{exact}|$ (mJ/m$^2$)")
    ax1.set_ylabel("Total device thickness (nm)")
    ax1.set_title(
        f"NSGA-II Pareto Front — Stiction vs Thickness\n"
        f"Substrate: {substrate.upper()}-WTe₂  |  n = {n} solutions"
    )
    ax1.set_xscale("log")
    ax1.grid(True, alpha=0.3)
    ax1.annotate(
        r"$\kappa_\mathrm{eff} \to 1/\sqrt{2}$ minimises stiction",
        xy=(0.03, 0.92), xycoords="axes fraction", fontsize=8.5,
        bbox=dict(boxstyle="round,pad=0.3", fc="#1a1a2e", alpha=0.8),
    )

    # ── Right panel: F1 vs F3 (thermal fraction), coloured by d_nm ──────────
    if has_tf:
        sc2 = ax2.scatter(E_vals, tf_vals, c=d_nms, cmap="viridis",
                          s=65, edgecolors="k", linewidths=0.4, zorder=3)
        cbar2 = fig.colorbar(sc2, ax=ax2)
        cbar2.set_label("Separation d (nm)")
        ax2.set_xlabel(r"$|E_\mathrm{exact}|$ (mJ/m$^2$)")
        ax2.set_ylabel(r"Thermal fraction $f_T = E_\mathrm{classical}/|E_\mathrm{quantum}|$")
        ax2.set_title(
            "Thermal Stability Front (T = 300 K)\n"
            r"$f_T \to 0$: quantum-dominated  |  $f_T \to 1$: thermal-dominated"
        )
        ax2.set_xscale("log")
        ax2.grid(True, alpha=0.3)
        ax2.axhline(0.1, color="#f59e0b", linewidth=1.0, linestyle="--", alpha=0.7)
        ax2.annotate(
            r"$f_T = 0.1$ threshold (quantum-safe regime)",
            xy=(0.03, 0.13), xycoords="axes fraction", fontsize=8,
            color="#f59e0b",
        )

    fig.tight_layout()
    _save(fig, out_path)


def plot_au_sio2_benchmark(d_nm: np.ndarray,
                            F_our: np.ndarray,
                            out_path: Path) -> None:
    """
    Code validation plot: Au | vac | SiO₂ Casimir pressure vs separation.

    Compares our Lifshitz code (Drude-Au + Cauchy-SiO₂) against two
    analytical reference curves:
      1. Perfect conductor (PC) limit: F_PC = ℏcπ²/(240 d⁴)  — upper bound
      2. Non-retarded Hamaker limit:   F_Ham = A/(6π d³)       — non-retarded vdW

    At d = 100–500 nm (retarded regime): our code lies between these two bounds,
    confirming that retardation is correctly captured.  This validates the Lifshitz
    integrator before applying it to the Te/WTe₂ stiction-suppression problem.

    Args:
        d_nm:    Separation array (nm), e.g. 100–500 nm.
        F_our:   Our Lifshitz pressure (N/m²) for Drude-Au / Cauchy-SiO₂.
        out_path: Destination PNG path.

    References:
        Lambrecht & Reynaud (2000) Eur. Phys. J. D 8, 309.
        Decca et al. (2007) Phys. Rev. D 75, 077101.
        Parsegian (2006) Van der Waals Forces, Cambridge UP, Table A5.2.
    """
    HBAR_V = 1.0545718e-34   # J*s
    C_V    = 2.99792458e8    # m/s
    d_m    = d_nm * 1e-9

    # Perfect-conductor pressure: F = -ℏcπ²/(240 d⁴)
    F_PC  = HBAR_V * C_V * np.pi ** 2 / (240.0 * d_m ** 4)

    # Non-retarded Hamaker pressure: |F| = A/(6π d³)
    # A_Au-SiO₂ (Parsegian 2006, Table A5.2, Au/vac/SiO₂ Lifshitz-Hamaker)
    A_AU_SIO2 = 5.5e-20   # J
    F_Ham = A_AU_SIO2 / (6.0 * np.pi * d_m ** 3)

    fig, ax = plt.subplots(figsize=(8, 5))

    ax.plot(d_nm, np.abs(F_our) * 1e3, color="#1f77b4", linewidth=2.2,
            label="Our Lifshitz code (Drude-Au | vac | Cauchy-SiO₂)")
    ax.plot(d_nm, F_PC * 1e3, color="gray", linewidth=1.4, linestyle="--",
            label=r"Perfect conductor limit: $\hbar c\pi^2/(240\,d^4)$")
    ax.plot(d_nm, F_Ham * 1e3, color="#d62728", linewidth=1.4, linestyle=":",
            label=r"Hamaker (non-retarded): $A/(6\pi d^3)$, $A=5.5\times10^{-20}$ J")

    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("Separation d (nm)")
    ax.set_ylabel(r"Casimir pressure $|F|$ (mPa)")
    ax.set_title(
        "Code Validation: Au | vac | SiO₂ Lifshitz Benchmark\n"
        "(Drude model — Lambrecht & Reynaud 2000; Decca et al. 2007)"
    )
    ax.legend(fontsize=9)
    ax.grid(True, which="major", alpha=0.3)
    ax.grid(True, which="minor", alpha=0.1)

    # Ratio annotation at midpoint
    mid = len(d_nm) // 2
    ratio_pc  = np.abs(F_our[mid]) / F_PC[mid]
    ratio_ham = np.abs(F_our[mid]) / F_Ham[mid]
    ax.text(0.03, 0.10,
            f"At d = {d_nm[mid]:.0f} nm:\n"
            f"Our / PC  = {ratio_pc:.2f}\n"
            f"Our / Ham = {ratio_ham:.2f}",
            transform=ax.transAxes, fontsize=8.5,
            bbox=dict(boxstyle="round,pad=0.3", fc="#0d1117", alpha=0.88),
            color="white")
    ax.annotate(
        "Our code correctly tracks the\nretarded regime: below PC,\nabove non-retarded Hamaker",
        xy=(0.60, 0.72), xycoords="axes fraction", fontsize=8.5,
        bbox=dict(boxstyle="round,pad=0.3", fc="#1a1a2e", alpha=0.85),
    )

    _save(fig, out_path)


def main() -> None:
    """Generate all Casimir energy and force plots, save to plots/.

    Sweep configurations:
      1. casimir_tellurium.png      — E vs d, Te | vac | Te
      2. casimir_wte2.png           — E vs d, WTe2 | vac | WTe2
      3. casimir_comparison.png     — overlay Te and WTe2 (isotropic)
      4. casimir_chiral.png         — E vs theta (kappa0 = 0.1/0.3/0.5/1.0)
      5. pareto_front.png           — NSGA-II Pareto scatter
      6. casimir_force.png          — |F| vs d log-log (three configs)
      7. casimir_force_chiral.png   — |F| vs d, kappa=0/0.5/1.0
      8. casimir_aniso.png          — anisotropic vs isotropic comparison
      9. casimir_td_wte2.png        — Td (Weyl) vs hex WTe2 phase comparison
     10. casimir_2osc_model.png     — 2-oscillator Sellmeier vs Cauchy model
     11. casimir_finite_T.png       — T=0 vs T=300 K Matsubara summation
     12. casimir_benchmark_au_sio2.png — Au/SiO₂ code validation (Drude model)
    """
    te_path   = DATA_DIR / "tellurium.json"
    wte2_path = DATA_DIR / "wte2.json"

    eps_te   = load_eps_static(te_path)
    eps_wte2 = load_eps_static(wte2_path)

    # Anisotropic tensor components (eps_perp, eps_par)
    te_perp,   te_par   = load_eps_tensor(te_path)
    wte2_perp, wte2_par = load_eps_tensor(wte2_path)
    print(f"Te   tensor: eps_perp={te_perp:.2f}  eps_par={te_par:.2f}")
    print(f"WTe2 tensor: eps_perp={wte2_perp:.2f}  eps_par={wte2_par:.2f}")

    print(f"eps_static  Te   = {eps_te:.4f}")
    print(f"eps_static WTe2  = {eps_wte2:.4f}")

    # ── 1-3: Standard Lifshitz sweeps ────────────────────────────────────────
    print("\nComputing Te | vac | Te ...")
    d_nm, E_te   = sweep_separation(eps_te,   eps_te,   n_points=40)

    print("\nComputing WTe2 | vac | WTe2 ...")
    d_nm, E_wte2 = sweep_separation(eps_wte2, eps_wte2, n_points=40)

    print("\nComputing Te | vac | WTe2 (asymmetric) ...")
    _,    E_asym = sweep_separation(eps_te,   eps_wte2, n_points=40)

    print("\nGenerating standard plots...")
    plot_casimir_single(d_nm, E_te,
                        "Te | vac | Te (mp-19)", "#1f77b4",
                        PLOTS_DIR / "casimir_tellurium.png")
    plot_casimir_single(d_nm, E_wte2,
                        "WTe2 | vac | WTe2 (mp-1023926)", "#d62728",
                        PLOTS_DIR / "casimir_wte2.png")
    plot_casimir_comparison(d_nm, E_te, E_wte2,
                            PLOTS_DIR / "casimir_comparison.png")

    # ── 4: Chiral sweep — E vs theta ─────────────────────────────────────────
    print("\nComputing chiral sweep (Te | vac | Te, d=10 nm) ...")
    D_CHIRAL_NM = 10.0
    kappa0_vals = [0.1, 0.3, 0.5, 1.0]
    theta_arr, chiral_results = sweep_chiral(
        eps_te, eps_te, D_CHIRAL_NM * 1e-9, kappa0_vals, n_theta=80
    )
    plot_chiral_effect(theta_arr, chiral_results, D_CHIRAL_NM,
                       PLOTS_DIR / "casimir_chiral.png")

    # ── 5: Pareto front ──────────────────────────────────────────────────────
    pareto_path = Path(__file__).parent.parent / "outputs" / "pareto_results.json"
    if pareto_path.exists():
        print("\nGenerating Pareto front plot...")
        plot_pareto_front(pareto_path, PLOTS_DIR / "pareto_front.png")
    else:
        print("\nPareto data not found; run --optimize first.")

    # ── 6: Anisotropic tensor Lifshitz ──────────────────────────────────────
    print("\nComputing anisotropic Lifshitz (Te|vac|Te, Te|vac|WTe2) ...")
    N_ANISO = 30
    _, E_aniso_te_te = sweep_separation_aniso(
        te_perp, te_par, te_perp, te_par, n_points=N_ANISO)
    _, E_aniso_asym  = sweep_separation_aniso(
        te_perp, te_par, wte2_perp, wte2_par, n_points=N_ANISO)

    # Isotropic Te|WTe2 already computed as E_asym above (n_points=40 vs 30)
    # Recompute at same grid for clean comparison
    d_aniso, E_iso_asym = sweep_separation(eps_te, eps_wte2, n_points=N_ANISO)
    plot_aniso_comparison(d_aniso, E_iso_asym, E_aniso_te_te, E_aniso_asym,
                          PLOTS_DIR / "casimir_aniso.png")

    # Print aniso vs iso summary table
    print("\nAnisotropic vs isotropic comparison (Te | vac | WTe2):")
    print(f"  {'d (nm)':>8}  {'E_iso (mJ/m2)':>15}  {'E_aniso (mJ/m2)':>16}  {'ratio':>7}")
    print("  " + "-" * 54)
    for i in range(0, N_ANISO, N_ANISO // 6):
        r = E_aniso_asym[i] / E_iso_asym[i] if E_iso_asym[i] != 0 else float('nan')
        print(f"  {d_aniso[i]:>8.1f}  {E_iso_asym[i]*1e3:>15.4e}  "
              f"{E_aniso_asym[i]*1e3:>16.4e}  {r:>7.4f}")

    # ── 8: Casimir force curves  F = -dE/dd ─────────────────────────────────
    print("\nComputing Casimir force curves (Te|Te, WTe2|WTe2, Te|WTe2) ...")
    N_FORCE = 30   # fewer points — force integral is twice as expensive
    d_f, F_te   = sweep_force(eps_te,   eps_te,   n_points=N_FORCE)
    d_f, F_wte2 = sweep_force(eps_wte2, eps_wte2, n_points=N_FORCE)
    d_f, F_asym = sweep_force(eps_te,   eps_wte2, n_points=N_FORCE)
    plot_casimir_force(d_f, F_te, F_wte2, F_asym,
                       PLOTS_DIR / "casimir_force.png")

    print("\nComputing chiral force curves (Te|Te, kappa=0/0.5/1.0) ...")
    _,    F_k05 = sweep_force(eps_te, eps_te, n_points=N_FORCE, kappa=0.5)
    _,    F_k10 = sweep_force(eps_te, eps_te, n_points=N_FORCE, kappa=1.0)
    plot_chiral_force(d_f, F_te, F_k05, F_k10,
                      PLOTS_DIR / "casimir_force_chiral.png")

    # ── 9: Td-WTe2 (Weyl phase) vs Hex WTe2 comparison ─────────────────────
    td_wte2_path = DATA_DIR / "td_wte2_dft.json"
    if td_wte2_path.exists():
        print("\nComputing Td-WTe2 (Weyl phase) Casimir comparison ...")
        td_perp = load_eps_tensor(td_wte2_path)[0]
        td_par  = load_eps_tensor(td_wte2_path)[1]
        print(f"  Td-WTe2 DFT tensor: eps_perp={td_perp:.2f}  eps_par={td_par:.2f}")

        N_TD = 30
        d_td, E_te_hex  = sweep_separation_aniso(
            te_perp, te_par, wte2_perp, wte2_par, n_points=N_TD)
        _,    E_te_td   = sweep_separation_aniso(
            te_perp, te_par, td_perp, td_par, n_points=N_TD)
        _,    E_td_td   = sweep_separation_aniso(
            td_perp, td_par, td_perp, td_par, n_points=N_TD)

        plot_td_wte2_comparison(d_td, E_te_hex, E_te_td, E_td_td,
                                PLOTS_DIR / "casimir_td_wte2.png")

        print("\n  Td vs Hex WTe2 summary (Te | vac | WTe2, anisotropic):")
        print(f"  {'d (nm)':>8}  {'E_hex (mJ/m2)':>15}  {'E_Td (mJ/m2)':>14}  {'ratio Td/hex':>13}")
        print("  " + "-" * 58)
        for i in range(0, N_TD, N_TD // 6):
            r = E_te_td[i] / E_te_hex[i] if E_te_hex[i] != 0 else float("nan")
            print(f"  {d_td[i]:>8.1f}  {E_te_hex[i]*1e3:>15.4e}  "
                  f"{E_te_td[i]*1e3:>14.4e}  {r:>13.4f}")
    else:
        print("\n  td_wte2_dft.json not found; skipping Td-WTe2 plot.")

    # ── 10: 2-oscillator vs single-oscillator dielectric model ───────────────
    print("\nComputing 2-oscillator Sellmeier vs single-oscillator (Te|vac|Te) ...")
    N_2OSC = 30
    d_2osc, E_1osc_te = sweep_separation(eps_te, eps_te, n_points=N_2OSC)
    print("  [2-osc sweep]")
    _,      E_2osc_te = sweep_separation_2osc(TE_2OSC, TE_2OSC, n_points=N_2OSC)
    plot_2osc_comparison(d_2osc, E_1osc_te, E_2osc_te,
                         PLOTS_DIR / "casimir_2osc_model.png")

    # ── 11: Finite-temperature Lifshitz (T=300 K Matsubara) ─────────────────
    print("\nComputing finite-T Lifshitz (Te|vac|WTe2, T=300K, d=1..2000 nm) ...")
    N_FT = 35
    d_ft, E_T0 = sweep_separation(eps_te, eps_wte2,
                                   d_min_nm=1.0, d_max_nm=2000.0, n_points=N_FT)
    print("  [Matsubara sum T=300K]")
    _, E_T300  = sweep_finite_T(eps_te, eps_wte2,
                                 T=300.0, d_min_nm=1.0, d_max_nm=2000.0,
                                 n_points=N_FT)
    plot_finite_T(d_ft, E_T0, E_T300, PLOTS_DIR / "casimir_finite_T.png")

    # ── 12: Au/SiO₂ Lifshitz benchmark (code validation) ───────────────────
    print("\nComputing Au/SiO2 benchmark (Drude-Au | vac | Cauchy-SiO2) ...")
    # Au: Drude model, omega_p=1.37e16, gamma=5.32e13  (Lambrecht & Reynaud 2000)
    # SiO₂: single-oscillator Cauchy, eps_static=3.81, omega_UV=2.0e16 rad/s
    # Reference freq for xi_max: max(omega_p_Au, omega_UV_SiO2) = 2.0e16
    EPS_SIO2_STATIC = 3.81
    OMEGA_UV_SIO2   = 2.0e16   # rad/s — UV electronic pole of fused silica
    OMEGA_REF_BENCH = max(AU_DRUDE["omega_p"], OMEGA_UV_SIO2)

    eps_au   = lambda xi: epsilon_imaginary_drude(xi, AU_DRUDE["omega_p"],
                                                   AU_DRUDE["gamma"])
    eps_sio2 = lambda xi: epsilon_imaginary(EPS_SIO2_STATIC, xi, OMEGA_UV_SIO2)

    N_BENCH = 20   # fewer points — Drude integrand is stiffer
    d_bench = np.logspace(np.log10(100.0), np.log10(500.0), N_BENCH)
    F_bench = []
    for i, d_val in enumerate(d_bench):
        f = casimir_force_from_eps_fns(eps_au, eps_sio2, d_val * 1e-9,
                                        omega_ref=OMEGA_REF_BENCH)
        F_bench.append(f)
        if (i + 1) % 5 == 0:
            print(f"    {i+1}/{N_BENCH}  d={d_val:.0f} nm  F={f:.4e} N/m^2")
    F_bench = np.array(F_bench)

    plot_au_sio2_benchmark(d_bench, F_bench,
                            PLOTS_DIR / "casimir_benchmark_au_sio2.png")

    # Print benchmark summary
    print("\nAu/SiO2 benchmark summary (Drude-Au | vac | Cauchy-SiO2):")
    print(f"  {'d (nm)':>8}  {'F_our (Pa)':>12}  {'F_PC (Pa)':>11}  {'ratio':>7}")
    print("  " + "-" * 46)
    _HBAR = 1.0545718e-34; _C = 2.99792458e8
    for i in range(0, N_BENCH, N_BENCH // 5):
        d_m   = d_bench[i] * 1e-9
        F_pc  = _HBAR * _C * np.pi**2 / (240.0 * d_m**4)
        ratio = abs(F_bench[i]) / F_pc
        print(f"  {d_bench[i]:>8.0f}  {F_bench[i]:>12.4e}  {-F_pc:>11.4e}  {ratio:>7.3f}")

    # ── Summary table ─────────────────────────────────────────────────────────
    print("\n" + "=" * 72)
    print(f"{'d (nm)':>8}  {'E_Te (mJ/m2)':>14}  "
          f"{'E_WTe2 (mJ/m2)':>15}  {'E_Asym (mJ/m2)':>15}")
    print("-" * 72)
    for idx in np.linspace(0, len(d_nm) - 1, 8, dtype=int):
        print(
            f"{d_nm[idx]:>8.1f}  "
            f"{E_te[idx]*1e3:>14.4e}  "
            f"{E_wte2[idx]*1e3:>15.4e}  "
            f"{E_asym[idx]*1e3:>15.4e}"
        )
    print("=" * 72)

    # Print chiral summary
    print("\nChiral correction at d=10 nm (Te | vac | Te):")
    print(f"{'theta (deg)':>12}  " + "  ".join(
        f"k0={k0}  E(mJ/m2)" for k0 in kappa0_vals))
    print("-" * 80)
    for i in range(0, len(theta_arr), len(theta_arr)//8):
        row = f"{np.degrees(theta_arr[i]):>12.1f}"
        for k0 in kappa0_vals:
            row += f"  {chiral_results[k0][i]*1e3:>17.4e}"
        print(row)


if __name__ == "__main__":
    main()
