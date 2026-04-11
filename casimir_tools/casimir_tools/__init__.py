"""
casimir_tools — Open-source Casimir force engineering toolkit.

A self-contained Python library for computing Lifshitz-Casimir interactions
in anisotropic, chiral dielectric heterostructures. Developed as part of the
AI-driven Casimir Stiction Suppression project (KEC 2028, SERB CRG).

Public API
----------
Dielectric models:
    epsilon_imaginary       — single-oscillator Cauchy model
    epsilon_imaginary_2osc  — two-oscillator Sellmeier model

Energy calculations:
    casimir_energy          — T=0 isotropic Lifshitz (full double integral)
    casimir_energy_chiral   — T=0 with κ² chiral correction
    casimir_energy_aniso    — T=0 uniaxial anisotropic Lifshitz
    casimir_energy_2osc     — T=0 with 2-oscillator dielectric
    casimir_energy_finite_T — T>0 Matsubara summation

Force calculations:
    casimir_force           — F = -dE/dd (isotropic)
    casimir_force_chiral    — chiral Casimir force

Sweep utilities:
    sweep_separation        — energy vs d (isotropic)
    sweep_separation_aniso  — energy vs d (uniaxial)
    sweep_separation_2osc   — energy vs d (2-oscillator)
    sweep_finite_T          — energy vs d at finite T

Material presets:
    TE_2OSC    — Tellurium 2-oscillator parameters
    WTE2_2OSC  — WTe₂ (P-6m2) 2-oscillator parameters
    MATERIALS  — dict of preset material dielectric constants

Physical constants (SI):
    HBAR, KB, C, OMEGA_UV

References
----------
1. Lifshitz, E.M. (1956) Sov. Phys. JETP 2, 73.
2. Dzyaloshinskii, Lifshitz, Pitaevskii (1961) Adv. Phys. 10, 165.
3. Zhao, R. et al. (2009) Phys. Rev. Lett. 103, 103602.
4. Bimonte, G. et al. (2009) Phys. Rev. A 79, 042906.
5. Parsegian, V.A. (2006) Van der Waals Forces. Cambridge UP.
"""

__version__ = "0.1.6"
__author__  = "Sevesh SS"
__email__   = "seveshss.24aim@kongu.edu"
__license__ = "MIT"

from casimir_tools._core import (
    # Physical constants
    HBAR,
    KB,
    C,
    OMEGA_UV,
    # Dielectric models
    epsilon_imaginary,
    epsilon_imaginary_2osc,
    epsilon_imaginary_drude,
    # Isotropic Lifshitz
    casimir_energy,
    casimir_energy_chiral,
    casimir_energy_chiral_asymmetric,
    casimir_energy_fast,
    casimir_energy_finite_T,
    # Anisotropic Lifshitz
    casimir_energy_aniso,
    # 2-oscillator
    casimir_energy_2osc,
    # Force
    casimir_force,
    casimir_force_chiral,
    # Asymmetric chiral diagnostics
    compute_asymmetric_kappa_crit,
    # Sweeps
    sweep_separation,
    sweep_separation_aniso,
    sweep_separation_2osc,
    sweep_finite_T,
    sweep_force,
    # Material presets
    TE_2OSC,
    WTE2_2OSC,
)

from casimir_tools._materials import MATERIALS, load_material

__all__ = [
    "HBAR", "KB", "C", "OMEGA_UV",
    "epsilon_imaginary", "epsilon_imaginary_2osc", "epsilon_imaginary_drude",
    "casimir_energy", "casimir_energy_chiral", "casimir_energy_chiral_asymmetric",
    "casimir_energy_fast", "casimir_energy_aniso", "casimir_energy_2osc",
    "casimir_energy_finite_T", "casimir_force", "casimir_force_chiral",
    "compute_asymmetric_kappa_crit",
    "sweep_separation", "sweep_separation_aniso", "sweep_separation_2osc",
    "sweep_finite_T", "sweep_force",
    "TE_2OSC", "WTE2_2OSC",
    "MATERIALS", "load_material",
]
