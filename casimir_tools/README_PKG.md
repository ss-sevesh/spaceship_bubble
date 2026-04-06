# casimir-tools

**Open-source Python toolkit for Lifshitz-Casimir force engineering in anisotropic and chiral dielectric heterostructures.**

Developed as part of the *AI-driven Casimir Stiction Suppression* project (KEC 2026, SERB CRG).

## Installation

```bash
pip install casimir-tools
```

## Quick Start

```python
from casimir_tools import casimir_energy, casimir_energy_chiral, MATERIALS

# Standard Lifshitz energy: Te | vacuum | WTe2 at 10 nm
te   = MATERIALS["Te"]
wte2 = MATERIALS["WTe2_hex"]

E = casimir_energy(te["eps_static"], wte2["eps_static"], d=10e-9)
print(f"E = {E*1e3:.4f} mJ/m²")   # ~ -0.20 mJ/m²

# With chiral correction κ = 0.7 → near-zero Casimir
E_chiral = casimir_energy_chiral(te["eps_static"], wte2["eps_static"],
                                  d=10e-9, kappa=0.7)
print(f"E_chiral = {E_chiral*1e3:.4f} mJ/m²")

# Finite temperature (T = 300 K, Matsubara summation)
from casimir_tools import casimir_energy_finite_T
E_300K = casimir_energy_finite_T(te["eps_static"], wte2["eps_static"],
                                  d=10e-9, T=300.0)

# Anisotropic uniaxial Lifshitz (Te crystal tensor)
from casimir_tools import casimir_energy_aniso
E_aniso = casimir_energy_aniso(te["eps_perp"], te["eps_par"],
                                wte2["eps_perp"], wte2["eps_par"],
                                d=10e-9)

# 2-oscillator Sellmeier model
from casimir_tools import casimir_energy_2osc, TE_2OSC, WTE2_2OSC
E_2osc = casimir_energy_2osc(**TE_2OSC, **{f"{k}_2": v for k, v in WTE2_2OSC.items()},
                               d=10e-9)
```

## Physics

The library implements the **Lifshitz (1956)** formula for Casimir energy between two planar dielectric half-spaces:

```
E(d) = (ħ/2π²c²) ∫₀^∞ ξ² dξ ∫₁^∞ p dp
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
  url     = {https://github.com/seveshss/casimir-tools},
  version = {0.1.0},
}
```

## License

MIT © Sevesh SS, KEC 2026
