# Verification Report
Generated: 2026-04-18
Pipeline: spaceship_bubble (casimir-tools v0.1.7)
Verifier: Physics verification run — autonomous, no assumptions trusted

---

## Overall Verdict

**NEEDS FIXES ⚠️**

Core physics engine is sound and correctly implements Lifshitz theory.
Several claimed results in the README are numerically wrong. Three critical
discrepancies must be corrected before publication.

---

## Benchmark Results — Au/SiO₂ vs Lambrecht & Reynaud (2000)

**IMPORTANT NOTE:** The verification prompt's expected value of
"-1.3 × 10⁻⁵ N/m² at d=100nm" is incorrect. The true Casimir
pressure between Au plates at d=100nm is ~5-6 N/m². The ideal
perfect-conductor value is 13 N/m²; Drude-model Au gives ~0.43×
that. This is a wrong expectation in the prompt, NOT a code error.

**Actual benchmark: η = F_Au / F_ideal compared to Lambrecht & Reynaud 2000:**

| d (nm) | F_ideal (N/m²) | F_Au code (N/m²) | η_code | η_literature |
|--------|----------------|------------------|--------|-------------|
| 50     | 208.0          | -58.8            | 0.283  | ~0.28       |
| 100    | 13.00          | -5.68            | **0.437** | **~0.43** |
| 200    | 0.813          | -0.494           | 0.607  | ~0.60       |

**η at d=100nm: code=0.437, Lambrecht & Reynaud=0.43 → deviation: ~1.6%**

**Status: VERIFIED ✅ — deviates < 5% from literature across all separations.**

The Au Drude parameters (ω_p=1.37×10¹⁶ rad/s, γ=5.32×10¹³ rad/s) are
correct per Lambrecht & Reynaud (2000) Table 1.

---

## Physics Implementation

| Check | Status | Notes |
|-------|--------|-------|
| Lifshitz integral (TE+TM) | ✅ | Correct prefactor HBAR/(4π²c²); p-limits adaptive |
| Chiral correction (Zhao 2009) | ✅ | δE = −2·prefactor·∫ ξ²dξ ∫p dp (r^TM·r^TE cross term) |
| Asymmetric chiral (Silveirinha 2010) | ✅ | exp(−4d) two-round-trip correctly implemented |
| Matsubara summation (n=0 term) | ✅ | k_⊥ space with weight 1/2; matches DLP analytic |
| Matsubara convergence | ✅ | n_max=800 >> required ~61 at d=10nm, T=300K |
| Physical constants (HBAR,KB,C) | ✅ | HBAR 16 ppb off CODATA; negligible at any physics scale |
| Materials data (Te, WTe₂) | ✅ | Trace-average eps_static correct; tensor loaded correctly |
| Anisotropic Lifshitz (uniaxial) | ✅ | eps_perp/eps_par correctly split for TE vs TM |
| Two-oscillator Sellmeier | ✅ | C1+C2=eps_static−1 self-consistent; eps(0)=164.27 ✓ |
| Force = −dE/dd | ✅ | Analytic derivative; sign convention correct (F<0 = attractive) |
| Sign of Casimir energy | ✅ | Te|Te at kappa=0 gives E<0 (attractive) ✓ |
| Large-d behavior | ✅ | E→0 as d→∞ ✓ |
| Optimizer objectives | ✅ | F1,F2,F3 all minimized; constraint d_nm ≤ N×5nm correct |
| NSGA-II via pymoo | ✅ | Standard library; non-dominated sort + crowding distance ✓ |
| Hamaker fast model (optimizer inner loop) | ⚠️ | Overestimates |E| by 2x at d=10nm, 14x at d=100nm vs full Lifshitz |
| Publication results use fast model | ✅ | NO — final outputs use casimir_energy_chiral_asymmetric() |

---

## Claimed Results Verification

| Claim | Status | Actual Value | Notes |
|-------|--------|-------------|-------|
| 40% reduction at κ_eff=0.5 (Te\|Te, d=10nm) | ✅ | **39.5%** | Within 1% of claim |
| κ_crit = 0.795 (Te\|Te, d=10nm) | ✅ | **0.7955** | Matches to 0.1% |
| κ_crit ≈ 0.775 (Te\|Te, d=84nm) | ✅ | **0.7750** | Matches exactly |
| N=20, d=99.9nm optimal design, E=−1.44×10⁻⁴ mJ/m² | ✅ | **−1.44×10⁻⁴ mJ/m²** | E_chiral_asymm (Silveirinha), confirmed at idx=11 |
| κ_eff=0.937 design in Pareto front | ✅ | **idx=11 has κ_eff=0.9370** | Confirmed |
| κ_crit_asym (Te\|WTe₂) ≈ 6.3 | ⚠️ | **6.65** | 5.5% off; repulsion still impossible at κ≤1 |
| WTe₂ anisotropy → 14% TM-mode reduction | ❌ | **9.7% at d=10nm, 5.1% at d=100nm** | Overstated by 4–9 pp |
| Td-WTe₂ / hex-WTe₂ ratio = 2.01 at d=1nm | ❌ | **1.639** | Off by 18% |
| Td-WTe₂ / hex-WTe₂ ratio = 1.45 at d=53nm | ❌ | **1.357** | Off by 6.4% |
| Thermal fraction range 0.003–173 | ✅ | **0.0028–173.21** | Matches |
| l_T = 1215 nm at T=300K | ✅ | **1214.8 nm** | ħc/(2πk_BT) correct |
| Quantum-classical crossover at d~193nm | ✅ | l_T/(2π)=193.3 nm | Correct |

---

## Errors Found

### ERROR 1 — README: WTe₂ anisotropy suppression overstated ❌ WRONG
**File:** `README.md`, Key Results table  
**Claimed:** "14% TM-mode reduction"  
**Actual computed:** 9.7% at d=10nm, 5.4% at d=50nm, 5.1% at d=100nm  
**Severity:** HIGH — publishable claim is quantitatively wrong  
**Root cause:** The 14% figure does not match live `casimir_energy_aniso()` output.
This function correctly implements uniaxial Fresnel coefficients. The real anisotropy
suppression is separation-dependent, not a single number.

### ERROR 2 — README: Td-WTe₂ / hex-WTe₂ ratio wrong ❌ WRONG
**File:** `README.md`, Key Results table  
**Claimed:** "ratio 2.01 at d=1nm, 1.45 at d=53nm"  
**Actual computed:**
- d=1nm: eps_hex=6.16 → E_hex=−2.183×10⁻² mJ/m²; eps_td=15.33 → E_td=−3.578×10⁻², ratio=**1.639**
- d=53nm: ratio=**1.357**  
**Severity:** HIGH — claimed 2× coupling enhancement is actually 1.64×  
**Root cause:** The ratio depends on whether the full isotropic Td eps (15.33 trace-avg)
or the anisotropic tensor (eps_perp=18.60, eps_par=8.80) is used. The code uses
`eps_td=15.33` (scalar trace-avg from load_eps_static). At d=1nm the 2.01 figure
requires eps_td~25, which no consistent reading of td_wte2_dft.json produces.

### ERROR 3 — README: κ_crit_asym slightly imprecise ⚠️ WARNING
**File:** `README.md`, Key Results table  
**Claimed:** "κ_crit_asym ≈ 6.3"  
**Actual computed:** 6.65 at d=10nm, 6.84 at d=84nm  
**Severity:** LOW — qualitative conclusion (repulsion impossible for κ≤1) is correct.
The exact number used in the draft should be updated.

### ISSUE 4 — Hamaker fast model / Lifshitz mismatch ⚠️ WARNING
**File:** `src/optimizer.py` (CasimirOptimizationProblem._evaluate)  
**Issue:** The fast Hamaker model overestimates |E_Casimir| vs full Lifshitz by:
- d=10nm: **2.06×**
- d=20nm: **3.34×**
- d=50nm: **7.41×**
- d=100nm: **14.5×**

This means the optimizer's inner-loop objective F1 is a wildly inaccurate proxy for
true stiction energy. The NSGA-II does not optimize the actual Casimir energy — it
optimizes the Hamaker approximation, which diverges from reality with distance.

**Mitigation (already in code):** The post-optimization validation step uses
`casimir_energy_chiral_asymmetric()` (Silveirinha 2010), and the final Pareto results
reported in the README use E_chiral_asymm, not E_fast. The optimizer ranking (which
design has less stiction) is directionally correct, but the convergence landscape is
wrong.

**Impact on publication:** If IEEE reviewers look at the optimizer objective function,
this is a clear weakness. It should be disclosed as a "speed approximation" and the
paper should state explicitly that reported energies come from the post-hoc full
Lifshitz calculation, not the optimization objective.

### ISSUE 5 — WTe₂ c-axis dielectric eps_par=1.56 is physically extreme ⚠️ WARNING
**File:** `data/wte2.json`  
**Issue:** The hexagonal WTe₂ (P-6m2) DFT dielectric tensor gives eps_par=1.56 (along c-axis).
This is nearly vacuum-like and implies almost no dielectric response perpendicular to the layers.
While anisotropy in layered TMDs is real, a ratio of 8.46/1.56 = 5.4× is at the extreme end
and may reflect a DFT artifact (LDA/GGA underestimates of interlayer coupling). This
affects casimir_energy_aniso() results but not the main casimir_energy() results (which use trace-avg).

### ISSUE 6 — 2-oscillator IR phonon frequency (minor) ⚠️ WARNING
**File:** `src/lifshitz.py`, line 1584  
**Code:** `TE_2OSC = dict(C1=45.77, omega1=3.0e13, ...)`  
**omega1 = 3.0×10¹³ rad/s = 4.77 THz** (angular → linear: 4.77 THz)  
**Caldwell & Fan (1959) Te main TO phonon:** 160 cm⁻¹ = 4.80 THz  
This matches well. The prompt's claim of "~3.6 THz" appears to be a different mode;
the code value of 4.77 THz is actually the correct main phonon. **Code is correct.**

### NON-ISSUE: Physical constants HBAR value
**HBAR = 1.0545718e-34 vs CODATA 1.054571817e-34**  
Relative error: 1.61×10⁻⁸ (16 ppb). This is 7 significant digits vs 9.
Impact on any computed energy or force: < 0.000002%. **Not a publication concern.**

### NON-ISSUE: Te dielectric tensor "expected" values in prompt
The prompt expects "εxx ≈ εyy ≈ 23, εzz ≈ 33" for Te. These values are wrong.
Te (mp-19) DFT gives εxx=εyy≈130.9, εzz≈231.1, trace-avg=164.3. Te has
exceptionally large dielectric constant due to strong phonon-electron coupling.
The code's Materials Project values are correct.

---

## Fixes Applied

### Fix 1 — Update README WTe₂ anisotropy claim
The "14% TM-mode reduction" figure is wrong. Correcting to reflect actual computed values.

### Fix 2 — Update README Td-WTe₂ ratio claims
The "ratio 2.01 at d=1nm, 1.45 at d=53nm" are wrong. Correcting to 1.64 and 1.36.

### Fix 3 — Update README κ_crit_asym value
Change "~6.3" to "~6.65" for consistency with live calculation.

All three fixes applied to `README.md` directly.

---

## What You Can Claim Confidently

These numbers were computed live from the running code and match literature:

- "We implement the full Lifshitz TE+TM double integral with Drude-model gold,
  achieving η=0.437 vs the theoretical prediction η≈0.43 (Lambrecht & Reynaud 2000)
  at d=100nm — a 1.6% deviation confirming benchmark validity."

- "For symmetric Te|Te chiral plates, the critical chirality κ_crit = 0.7955 at
  d=10nm (Zhao et al. 2009 leading-order formula), where the Casimir force passes
  through zero. At κ_eff=0.5, we compute 39.5% stiction reduction."

- "The physical Te|WTe₂ heterostructure (chiral plate only, κ₂=0) requires
  κ_crit_asym ≈ 6.65 (Silveirinha 2010 two-round-trip formula), confirming that
  Casimir repulsion is unachievable for any physically realizable chirality κ≤1."

- "NSGA-II (Deb 2002) identifies N=20 layers, d=99.9nm, κ_eff=0.937 as the
  Pareto-optimal minimum-stiction design, with E_Casimir=−1.44×10⁻⁴ mJ/m²
  (Silveirinha asymmetric formula, T=300K Matsubara, n_max=400)."

- "WTe₂ anisotropy (εxx/εzz ≈ 5.4) produces a separation-dependent TM-mode
  suppression of approximately 10% at d=10nm and 5% at d≥50nm."

- "Thermal fraction f_T spans 0.003–173 across the Pareto front (T=300K,
  l_T=1215nm). The quantum-classical crossover occurs at d≈193nm."

---

## What Needs More Work

1. **Td-WTe₂ ratio**: The "~2×" and "2.01 at d=1nm" claims are wrong (actual: 1.64).
   Update the IEEE draft table (Section V.B) before submission.

2. **WTe₂ anisotropy**: The "14% TM-mode reduction" is wrong. The actual figure is
   separation-dependent (~10% at 10nm, ~5% at 100nm). Update IEEE Section IV.C.

3. **Hamaker fast model disclosure**: The NSGA-II optimizer uses E_fast which
   overestimates |E| by 2-15× vs full Lifshitz at MEMS-relevant separations.
   Add a paragraph in the Methods section stating: "For computational efficiency,
   the NSGA-II inner loop uses the non-retarded Hamaker approximation. All energies
   reported in results use the full Lifshitz integral (casimir_energy_chiral_asymmetric)."

4. **WTe₂ c-axis dielectric**: eps_par=1.56 (nearly vacuum-like) should be flagged
   as a potential DFT artifact and compared against experimental optical data.

---

## Suggested Post Text (LinkedIn/Twitter)

Using ONLY verified results:

"Preprint: Casimir Stiction Suppression with Chiral Te Metamaterials

We ran a full Lifshitz TE+TM physics pipeline, benchmarked against Au/SiO₂
(1.6% deviation from Lambrecht & Reynaud 2000), and found:

• κ_crit = 0.796 (Te|Te symmetric) — zero Casimir force confirmed numerically
• 39.5% stiction reduction at κ_eff = 0.5
• NSGA-II Pareto: N=20 layers, d=99.9nm, E=−1.44×10⁻⁴ mJ/m²
• Matsubara summation (T=300K) converges at n>61; thermal crossover at d≈193nm
• For Te|WTe₂ heterostructure: κ_crit_asym ≈ 6.65 — repulsion needs new design strategies

Code: github.com/... | Package: pip install casimir-tools"

Remove any mention of "14% TM reduction", "2× stronger Td-WTe₂", or "ratio 2.01"
from all public-facing text until the draft is corrected.
