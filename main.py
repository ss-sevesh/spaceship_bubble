"""
main.py — Spaceship Bubble Research Pipeline Orchestrator.

AI-driven Casimir Stiction-Suppressing Chiral Tellurium Metamaterials.
Lead: Sevesh SS, KEC 2026.
Goals: IEEE publication + SERB funding.

Usage:
    uv run python main.py [--fetch] [--lifshitz] [--optimize] [--plot] [--all]

Steps (execution order):
    1. --fetch     Fetch dielectric tensor + structure from Materials Project
    2. --lifshitz  Quick Lifshitz-Casimir sanity check at several separations
    3. --optimize  Run NSGA-II Pareto optimisation, save outputs/pareto_results.json
    4. --plot      Generate all plots (requires pareto_results.json from step 3)
    --all          Run all four steps in sequence
"""

import argparse
import sys
from pathlib import Path

# Anchor all paths to project root regardless of invocation directory
_ROOT = Path(__file__).parent
sys.path.insert(0, str(_ROOT / "src"))

_EXPECTED_PLOTS = [
    "casimir_tellurium.png",
    "casimir_wte2.png",
    "casimir_comparison.png",
    "casimir_chiral.png",
    "pareto_front.png",
    "casimir_force.png",
    "casimir_force_chiral.png",
    "casimir_aniso.png",
    "casimir_td_wte2.png",
    "casimir_2osc_model.png",
    "casimir_finite_T.png",
    "casimir_benchmark_au_sio2.png",
]


def run_fetch() -> bool:
    """Fetch Te (mp-19) and WTe2 (mp-1023926) data from Materials Project."""
    print("\n[Step 1/4] Fetching Materials Project data...")
    try:
        from fetch_materials import main as fetch_main
        fetch_main()
        return True
    except Exception as exc:
        print(f"  [ERROR] --fetch failed: {exc}")
        return False


def run_lifshitz_check() -> bool:
    """Quick Lifshitz-Casimir energy and force check at selected separations."""
    print("\n[Step 2/4] Lifshitz-Casimir sanity check...")
    try:
        from lifshitz import (casimir_energy, casimir_energy_chiral,
                              casimir_energy_aniso, casimir_force,
                              casimir_energy_2osc, casimir_energy_finite_T,
                              load_eps_static, load_eps_tensor,
                              TE_2OSC, WTE2_2OSC)

        data_dir = _ROOT / "data"
        eps_te   = load_eps_static(data_dir / "tellurium.json")
        eps_wte2 = load_eps_static(data_dir / "wte2.json")

        te_perp,   te_par   = load_eps_tensor(data_dir / "tellurium.json")
        wte2_perp, wte2_par = load_eps_tensor(data_dir / "wte2.json")
        print(f"  eps_static  Te   = {eps_te:.4f}  "
              f"(tensor: perp={te_perp:.2f}, par={te_par:.2f})")
        print(f"  eps_static WTe2  = {eps_wte2:.4f}  "
              f"(tensor: perp={wte2_perp:.2f}, par={wte2_par:.2f})")

        hdr = (f"  {'d (nm)':>8}  {'E_iso':>12}  {'E_aniso':>12}  "
               f"{'E_chiral k=0.5':>15}  {'E_2osc':>12}  "
               f"{'E_T300K':>12}  {'F_std':>12}")
        print(f"\n{hdr}   [all mJ/m^2 except F in mN/m^2]")
        print("  " + "-" * 96)
        for d_nm in [5.0, 10.0, 20.0, 50.0, 100.0]:
            d_m      = d_nm * 1e-9
            E_iso    = casimir_energy(eps_te, eps_wte2, d_m)
            E_aniso  = casimir_energy_aniso(te_perp, te_par, wte2_perp, wte2_par, d_m)
            E_chiral = casimir_energy_chiral(eps_te, eps_wte2, d_m, kappa=0.5)
            E_2osc   = casimir_energy_2osc(
                TE_2OSC["C1"], TE_2OSC["omega1"], TE_2OSC["C2"], TE_2OSC["omega2"],
                WTE2_2OSC["C1"], WTE2_2OSC["omega1"], WTE2_2OSC["C2"], WTE2_2OSC["omega2"],
                d_m)
            E_T300   = casimir_energy_finite_T(eps_te, eps_wte2, d_m, T=300.0)
            F_std    = casimir_force(eps_te, eps_wte2, d_m)
            print(f"  {d_nm:>8.1f}  {E_iso*1e3:>12.4e}  {E_aniso*1e3:>12.4e}  "
                  f"{E_chiral*1e3:>15.4e}  {E_2osc*1e3:>12.4e}  "
                  f"{E_T300*1e3:>12.4e}  {F_std*1e3:>12.4e}")
        return True
    except Exception as exc:
        print(f"  [ERROR] --lifshitz failed: {exc}")
        return False


def run_optimize() -> bool:
    """Run NSGA-II multi-objective optimisation."""
    print("\n[Step 3/4] Running NSGA-II optimisation...")
    try:
        from optimizer import main as opt_main
        opt_main()
        # Auto-sync results to dashboard/public/
        import sys as _sys
        _sys.path.insert(0, str(_ROOT))
        from sync_assets import sync
        sync()
        return True
    except Exception as exc:
        print(f"  [ERROR] --optimize failed: {exc}")
        return False


def run_plots() -> bool:
    """Generate all Casimir energy plots including chiral sweep."""
    print("\n[Step 4/4] Generating plots...")
    try:
        from visualize import main as viz_main
        viz_main()

        # Verify expected plot files were produced
        plots_dir = _ROOT / "plots"
        missing = [p for p in _EXPECTED_PLOTS if not (plots_dir / p).exists()]
        if missing:
            print(f"  [WARN] {len(missing)} expected plot(s) not generated: "
                  + ", ".join(missing))
        else:
            print(f"  All {len(_EXPECTED_PLOTS)} plots confirmed.")
        return True
    except Exception as exc:
        print(f"  [ERROR] --plot failed: {exc}")
        return False


def main() -> None:
    """Parse arguments and run requested pipeline steps."""
    parser = argparse.ArgumentParser(
        description="Spaceship Bubble: Casimir stiction research pipeline."
    )
    parser.add_argument("--fetch",    action="store_true", help="Fetch MP data")
    parser.add_argument("--lifshitz", action="store_true", help="Lifshitz check")
    parser.add_argument("--optimize", action="store_true", help="NSGA-II optimisation")
    parser.add_argument("--plot",     action="store_true", help="Generate all plots")
    parser.add_argument("--all",      action="store_true", help="Run all steps")
    args = parser.parse_args()

    run_all = args.all or not any([args.fetch, args.lifshitz,
                                   args.plot, args.optimize])

    print("=" * 60)
    print("  Spaceship Bubble Research Pipeline")
    print("  AI-driven Casimir Stiction Suppression")
    print("  Lead: Sevesh SS | KEC 2026")
    print("=" * 60)

    results: dict[str, bool] = {}

    if run_all or args.fetch:
        results["fetch"] = run_fetch()

    if run_all or args.lifshitz:
        results["lifshitz"] = run_lifshitz_check()

    if run_all or args.optimize:
        results["optimize"] = run_optimize()

    if run_all or args.plot:
        results["plot"] = run_plots()

    # Summary
    failed = [k for k, v in results.items() if not v]
    if failed:
        print(f"\n[WARN] Steps that failed: {', '.join(failed)}")
        print("Pipeline finished with errors. Check output above.")
    else:
        print("\nPipeline complete.  Check data/, plots/, outputs/ for results.")


if __name__ == "__main__":
    main()
