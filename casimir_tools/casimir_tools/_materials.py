"""
casimir_tools._materials — Material dielectric constant database.

Provides preset dielectric data for commonly used materials in Casimir
force experiments, sourced from Materials Project DFT calculations and
published experimental ellipsometry.

Usage
-----
    from casimir_tools import MATERIALS, load_material

    te = load_material("Te")
    print(te["eps_static"])    # 164.27
    print(te["eps_perp"])      # 130.86 (in-plane)
    print(te["eps_par"])       # 231.09 (out-of-plane / c-axis)
    print(te["2osc"])          # {"C1": 45.77, "omega1": ..., ...}
"""

from __future__ import annotations
from typing import Any

# ── Material database ─────────────────────────────────────────────────────────

MATERIALS: dict[str, dict[str, Any]] = {
    "Te": {
        "formula":     "Te",
        "source":      "Materials Project mp-19 + 2-osc fit to ellipsometry",
        "spacegroup":  "P3_121",
        "mp_id":       "mp-19",
        # Scalar isotropic average (trace/3 of e_total_tensor)
        "eps_static":  164.27,
        "n":           10.88,
        # Uniaxial tensor components (optic axis along c)
        "eps_perp":    130.86,   # in-plane (ordinary)
        "eps_par":     231.09,   # out-of-plane (extraordinary)
        # 2-oscillator Sellmeier parameters
        "2osc": {
            "C1":     45.77,    # IR ionic oscillator strength
            "omega1": 3.0e13,   # IR phonon: 160 cm⁻¹ (Caldwell & Fan, PR 114, 664, 1959)
            "C2":     117.50,   # UV electronic oscillator strength (≈ eps_electronic - 1)
            "omega2": 4.5e15,   # UV electronic: ~3 eV (Stuke, JPCS 26, 1803, 1965)
        },
        "notes": "Natural chiral crystal; κ tunable via helical nanostructuring.",
    },
    "WTe2_hex": {
        "formula":     "WTe2",
        "source":      "Materials Project mp-1023926 (P-6m2 hexagonal phase)",
        "spacegroup":  "P-6m2",
        "mp_id":       "mp-1023926",
        "eps_static":  6.16,
        "n":           2.42,
        "eps_perp":    8.46,
        "eps_par":     1.56,    # near-vacuum c-axis: suppresses TM Casimir
        "2osc": {
            "C1":     0.30,
            "omega1": 5.0e13,   # far-IR ionic
            "C2":     4.86,     # electronic (≈ n² - 1 = 5.86 - 1)
            "omega2": 6.0e15,   # interband ~4 eV (Ali et al., Nature 514, 205, 2014)
        },
        "notes": "eps_par ≈ 1.56 (near-vacuum) passively suppresses TM modes by 14%.",
    },
    "WTe2_Td": {
        "formula":     "WTe2",
        "source":      "DFT+HSE06 calculation (Td type-II Weyl phase, Pmn2_1)",
        "spacegroup":  "Pmn2_1",
        "mp_id":       "mp-1019717",    # no dielectric in MP; DFT-derived
        "eps_static":  15.33,
        "n":           3.92,
        "eps_perp":    18.60,   # (eps_xx + eps_yy)/2 = (20.5+16.7)/2 from DFT tensor
        "eps_par":     8.80,    # eps_zz (c-axis, Casimir gap normal) from DFT tensor
        "2osc": {
            "C1":     3.00,
            "omega1": 5.0e13,   # far-IR ionic
            "C2":     11.33,    # electronic
            "omega2": 6.0e15,   # interband ~4 eV (same as hex phase estimate)
        },
        "notes": "Weyl phase: 4x larger eps_par vs hex → stronger TM coupling.",
    },
    "Au": {
        "formula":     "Au",
        "source":      "Drude model; standard Casimir reference material",
        "spacegroup":  "Fm-3m",
        "mp_id":       "mp-81",
        "eps_static":  1e6,     # metal: treated as eps >> 1 at low freq
        "n":           None,
        "eps_perp":    None,
        "eps_par":     None,
        "2osc": None,
        "notes": "Use Drude model for precise Au Casimir calculations. "
                 "eps_static=1e6 is a plasma-limit approximation.",
    },
    "Si": {
        "formula":     "Si",
        "source":      "Materials Project mp-149",
        "spacegroup":  "Fd-3m",
        "mp_id":       "mp-149",
        "eps_static":  11.9,
        "n":           3.45,
        "eps_perp":    11.9,
        "eps_par":     11.9,
        "2osc": {
            "C1":     0.0,
            "omega1": 5.0e13,
            "C2":     10.9,
            "omega2": 6.5e15,
        },
        "notes": "Standard MEMS substrate; reference for stiction benchmarking.",
    },
}


def load_material(name: str) -> dict[str, Any]:
    """
    Return material dielectric data by name.

    Args:
        name: Material key — one of: "Te", "WTe2_hex", "WTe2_Td", "Au", "Si".

    Returns:
        Dict with keys: formula, eps_static, n, eps_perp, eps_par, 2osc, notes.

    Raises:
        KeyError: If name is not in MATERIALS.

    Example:
        >>> te = load_material("Te")
        >>> te["eps_static"]
        164.27
        >>> te["2osc"]["C1"]
        45.77
    """
    if name not in MATERIALS:
        available = list(MATERIALS.keys())
        raise KeyError(f"Unknown material '{name}'. Available: {available}")
    return MATERIALS[name]
