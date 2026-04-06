"""
fetch_materials.py — Materials Project data fetcher.

Fetches dielectric tensor + crystal structure for:
  - Tellurium (mp-19)
  - WTe2 (mp-1019717)

Saves results to data/tellurium.json and data/wte2.json.
"""

import os
import json
from pathlib import Path

from dotenv import load_dotenv
from mp_api.client import MPRester


def fetch_material(material_id: str, api_key: str) -> dict:
    """
    Fetch dielectric tensor and structure data from Materials Project.

    Args:
        material_id: MP material ID string (e.g. "mp-19").
        api_key: Materials Project API key.

    Returns:
        dict with keys: material_id, formula, e_electronic, e_total,
        n (refractive index), lattice (a, b, c, alpha, beta, gamma),
        spacegroup.
    """
    with MPRester(api_key) as mpr:
        # Dielectric properties
        diel = mpr.materials.dielectric.search(
            material_ids=[material_id],
            fields=["material_id", "e_total", "e_electronic", "n",
                    "total", "electronic", "ionic"],
        )

        # Structure / summary
        summary = mpr.materials.summary.search(
            material_ids=[material_id],
            fields=["material_id", "formula_pretty", "symmetry", "structure"],
        )

    if not diel or not summary:
        raise ValueError(f"No data returned for {material_id}")

    d = diel[0]
    s = summary[0]

    lattice = s.structure.lattice

    def tensor_to_list(t) -> list:
        """Convert tuple-of-tuples or 2D array to nested Python list."""
        return [list(row) for row in t]

    result = {
        "material_id": material_id,
        "formula": s.formula_pretty,
        "spacegroup": s.symmetry.symbol if s.symmetry else None,
        # Full 3×3 dielectric tensors (from `total`, `electronic`, `ionic` fields)
        "e_electronic_tensor": tensor_to_list(d.electronic),
        "e_ionic_tensor":      tensor_to_list(d.ionic),
        "e_total_tensor":      tensor_to_list(d.total),
        # Scalar averages (trace/3) as reported by MP
        "e_electronic": float(d.e_electronic),
        "e_total":       float(d.e_total),
        "n": float(d.n),
        "lattice": {
            "a": lattice.a,
            "b": lattice.b,
            "c": lattice.c,
            "alpha": lattice.alpha,
            "beta":  lattice.beta,
            "gamma": lattice.gamma,
        },
    }
    return result


def save_json(data: dict, path: Path) -> None:
    """
    Serialize dict to a JSON file with pretty printing.

    Args:
        data: Dictionary to serialize.
        path: Destination file path (created if missing).
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=2)
    print(f"  Saved -> {path}")


def main() -> None:
    """Fetch Te and WTe2 data and save to data/."""
    load_dotenv()
    api_key = os.getenv("MP_API_KEY")
    if not api_key:
        raise EnvironmentError("MP_API_KEY not set in .env")

    data_dir = Path(__file__).parent.parent / "data"

    targets = [
        ("mp-19", data_dir / "tellurium.json"),
        # mp-1019717 (Td-WTe2, Weyl phase) has no dielectric data in MP.
        # Using mp-1023926 (WTe2, P-6m2) which has computed dielectric data.
        ("mp-1023926", data_dir / "wte2.json"),
    ]

    for mid, out_path in targets:
        print(f"\nFetching {mid}...")
        data = fetch_material(mid, api_key)
        print(f"  Formula  : {data['formula']}")
        print(f"  Spacegroup: {data['spacegroup']}")
        print(f"  n (refractive index): {data['n']:.4f}")
        save_json(data, out_path)

    print("\nAll materials fetched successfully.")


if __name__ == "__main__":
    main()
