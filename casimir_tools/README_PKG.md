# casimir-tools

**Open-source Python toolkit for Lifshitz-Casimir force engineering in anisotropic and chiral dielectric heterostructures.**

Developed as part of the *AI-driven Casimir Stiction Suppression* project (Kongu Engineering College 2026, SERB CRG).

## Installation

```bash
# Core (numpy + scipy only)
pip install casimir-tools

# With plotting support (matplotlib)
pip install "casimir-tools[plot]"

# Full dev install
pip install "casimir-tools[plot,dev]"
```

## Quick Start

```python
import casimir_tools as ct

# ── Material presets ──────────────────────────────────────────────────────────
te   = ct.MATERIALS["Te"]        # eps_static, eps_perp, eps_par
wte2 = ct.MATERIALS["WTe2_hex"]

# ── Standard Lifshitz energy (T = 0) ─────────────────────────────────────────
# Keyword args: eps_static1, eps_static2, d
E = ct.casimir_energy(eps_static1=te["eps_static"],
                      eps_static2=wte2["eps_static"],
                      d=10e-9)
print(f"E = {E*1e3:.4f} mJ/m²")   # ~ -0.20 mJ/m²

# ── Chiral correction (κ² term) ───────────────────────────────────────────────
# kappa=0.7 drives Casimir energy toward zero / repulsive regime
E_chiral = ct.casimir_energy_chiral(eps_static1=te["eps_static"],
                                     eps_static2=wte2["eps_static"],
                                     d=10e-9, kappa=0.7)
print(f"E_chiral = {E_chiral*1e3:.4f} mJ/m²")

# ── Finite temperature (T = 300 K, Matsubara summation) ──────────────────────
E_300K = ct.casimir_energy_finite_T(eps_static1=te["eps_static"],
                                     eps_static2=wte2["eps_static"],
                                     d=10e-9, T=300.0)

# ── Anisotropic uniaxial Lifshitz (Te crystal tensor) ────────────────────────
E_aniso = ct.casimir_energy_aniso(eps_perp1=te["eps_perp"], eps_par1=te["eps_par"],
                                   eps_perp2=wte2["eps_perp"], eps_par2=wte2["eps_par"],
                                   d=10e-9)

# ── 2-oscillator Sellmeier model ──────────────────────────────────────────────
E_2osc = ct.casimir_energy_2osc(
    **{f"{k}_1": v for k, v in ct.TE_2OSC.items()},
    **{f"{k}_2": v for k, v in ct.WTE2_2OSC.items()},
    d=10e-9
)
```

## Force Sweep & Plotting

`sweep_force` returns a **tuple** `(d_nm, forces)` — d values are already in nm.

```python
import casimir_tools as ct
import numpy as np
import matplotlib.pyplot as plt   # requires: pip install "casimir-tools[plot]"

EPS_TE = 164.27

# Returns (d_nm_array, force_array) — do NOT pass a pre-built d array
d_nm, forces = ct.sweep_force(eps1=EPS_TE, eps2=EPS_TE,
                               d_min_nm=5.0, d_max_nm=100.0, n_points=100)

plt.figure(figsize=(10, 6))
plt.plot(d_nm, np.abs(forces), color='#007acc', linewidth=2.5)
# d_nm is already in nm — no * 1e9 conversion needed
plt.yscale('log')
plt.xlabel("Separation Distance (nm)")
plt.ylabel("|F| (N/m²)")
plt.title("casimir-tools: Te Quantum Force Profile")
plt.grid(True, which="both", alpha=0.3)
plt.show()
```

## Physics

The library implements the **Lifshitz (1956)** formula for Casimir energy between two planar dielectric half-spaces:

```
E(d) = (ħ/4π²c²) ∫₀^∞ ξ² dξ ∫₁^∞ p dp
         × Σ_pol ln(1 − r₁^pol r₂^pol e^{−2pξd/c})
```

Extensions:
- **Chiral correction** (Zhao et al. 2009): `E = E_Lifshitz + κ² × δE`
- **Uniaxial anisotropy** (Bimonte et al. 2009): separate ε_⊥, ε_∥ Fresnel coefficients
- **Finite temperature** (Lifshitz/Pitaevskii): Matsubara sum at arbitrary T
- **2-oscillator Sellmeier**: resolves IR phonon + UV electronic contributions

## Citation

```bibtex
@software{sevesh2026casimir,
  author  = {Sevesh SS},
  title   = {casimir-tools: Lifshitz-Casimir Force Engineering Toolkit},
  year    = {2026},
  url     = {https://github.com/ss-sevesh/spaceship_bubble/tree/master/casimir_tools},
  version = {0.1.6},
}
```

## License

MIT © Sevesh SS, Kongu Engineering College 2026
