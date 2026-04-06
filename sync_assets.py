"""
sync_assets.py — Sync plots and data to dashboard/public/ for the React dev server.

Run after generating plots and running the optimizer:
    uv run python sync_assets.py
"""

import shutil
from pathlib import Path

# Anchor to project root regardless of invocation directory
_ROOT = Path(__file__).parent

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


def sync() -> None:
    dashboard = _ROOT / "dashboard"
    public    = dashboard / "public"

    plots_dest  = public / "plots"
    data_dest   = public / "data"
    plots_dest.mkdir(parents=True, exist_ok=True)
    data_dest.mkdir(parents=True, exist_ok=True)

    plots_src   = _ROOT / "plots"
    outputs_src = _ROOT / "outputs"

    # ── Copy plots ────────────────────────────────────────────────────────────
    synced_plots: list[str] = []
    if plots_src.exists():
        for f in plots_src.glob("*.png"):
            shutil.copy2(f, plots_dest / f.name)
            print(f"  Synced {f.name}")
            synced_plots.append(f.name)
    else:
        print(f"  [WARN] plots/ directory not found at {plots_src}")

    missing = [p for p in _EXPECTED_PLOTS if p not in synced_plots]
    if missing:
        print(f"  [WARN] {len(missing)} expected plot(s) not found and not synced:")
        for m in missing:
            print(f"         - {m}")
    else:
        print(f"  All {len(_EXPECTED_PLOTS)} expected plots synced.")

    # ── Copy Pareto results JSON ──────────────────────────────────────────────
    pareto_src = outputs_src / "pareto_results.json"
    if pareto_src.exists():
        shutil.copy2(pareto_src, data_dest / "pareto_results.json")
        print("  Synced pareto_results.json")
    else:
        print(f"  [WARN] pareto_results.json not found at {pareto_src}. "
              "Run main.py --optimize first.")

    print("\nSync complete. Dashboard public/ is up to date.")


if __name__ == "__main__":
    sync()
