# Changelog

All notable changes to **casimir-tools** are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

---

## [0.1.7] — 2026-04-11

### Added
- `casimir_energy_chiral_asymmetric` — asymmetric chiral correction (Silveirinha 2010) for Te|WTe₂ heterostructures
- `epsilon_imaginary_drude_lorentz` — Drude-Lorentz dielectric model for metallic substrates
- `compute_asymmetric_kappa_crit` — critical chirality parameter for the asymmetric case
- `sweep_force` — convenience wrapper to sweep Casimir force vs separation

### Changed
- `MATERIALS` dict updated with Td-WTe₂ DFT-HSE06 tensor (ε_⊥=18.60, ε_∥=8.80)

---

## [0.1.6] — 2026-04-08

### Added
- `casimir_energy_finite_T` — finite-temperature Lifshitz via Matsubara summation (T=300 K default)
- `casimir_energy_2osc` — two-oscillator Sellmeier model (IR phonon + UV electronic)
- `sweep_finite_T` — energy vs separation at finite T
- `TE_2OSC`, `WTE2_2OSC` — fitted 2-oscillator presets for Tellurium and WTe₂

---

## [0.1.5] — 2026-04-06

### Added
- `casimir_energy_aniso` — uniaxial anisotropic Lifshitz tensor model
- `sweep_separation_aniso` — anisotropic energy sweep
- `load_material` — load DFT dielectric tensors from JSON

---

## [0.1.4] — 2026-04-05

### Added
- `casimir_energy_chiral` — T=0 Lifshitz with κ² chiral correction term
- `casimir_force_chiral` — chiral Casimir force
- `casimir_energy_fast` — Hamaker approximation for fast sweeps

---

## [0.1.3] — 2026-04-04

### Added
- `casimir_energy` — T=0 isotropic Lifshitz double integral (TE + TM modes)
- `casimir_force` — F = −dE/dd analytical force
- `sweep_separation` — energy vs separation sweep utility
- `epsilon_imaginary`, `epsilon_imaginary_2osc` — Cauchy and Sellmeier dielectric models
- `MATERIALS` — preset dielectric constants for Te, WTe₂, SiO₂

### Notes
- First public release on PyPI
