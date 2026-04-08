from pathlib import Path
import json

root = Path(__file__).parent
with open(root / 'outputs' / 'pareto_results.json', 'r') as f:
    data = json.load(f)

variables = data['variables']
objectives = data['objectives']
n = len(variables)

repulsive = [i for i in range(n) if objectives[i].get('is_repulsive', False)]
energies = [
    objectives[i].get('E_Casimir_chiral_asymm_mJm2') or objectives[i].get('E_Casimir_mJm2', 0)
    for i in range(n)
]
closest_zero_idx = min(range(n), key=lambda i: abs(energies[i]))

print(f'Total solutions: {n}')
print(f'Repulsive solutions: {len(repulsive)}')
print(f'\nBest (lowest |E|):')
v, o = variables[closest_zero_idx], objectives[closest_zero_idx]
print(f'  idx={closest_zero_idx}, E={energies[closest_zero_idx]:.4e} mJ/m², '
      f'd={v["d_nm"]:.2f} nm, kappa_eff={v["kappa_eff"]:.4f}, N={v["N_layers"]}, '
      f'f_T={o.get("thermal_fraction", "N/A")}')

print(f'\nTop 5 by |E| (closest to zero):')
top5 = sorted(range(n), key=lambda i: abs(energies[i]))[:5]
for i in top5:
    v, o = variables[i], objectives[i]
    ft = o.get('thermal_fraction')
    ft_str = f'{ft:.4f}' if ft is not None else 'N/A'
    print(f'  idx={i}: E={energies[i]:.4e}, d={v["d_nm"]:.2f} nm, '
          f'kappa_eff={v["kappa_eff"]:.4f}, N={v["N_layers"]}, f_T={ft_str}')
