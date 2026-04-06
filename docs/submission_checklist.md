# IEEE Transactions on Nanotechnology — Submission Checklist

**Manuscript**: AI-Driven Design of Chiral Tellurium Metamaterials for Casimir Stiction Suppression  
**Target**: IEEE Transactions on Nanotechnology (Regular Paper)  
**Submission portal**: https://mc.manuscriptcentral.com/tnano

---

## ✅ DONE — Physics & Code

- [x] Lifshitz double integral (isotropic, T=0) — correct prefactor `ħ/(4π²c²)`
- [x] Uniaxial Fresnel coefficients (TE + TM anisotropic)
- [x] Chiral Casimir correction — symmetric Zhao 2009 formula (Te|Te)
- [x] Chiral Casimir correction — asymmetric Silveirinha 2010 formula (Te|WTe₂, κ₂=0)
- [x] Finite-temperature Matsubara summation — n=0 classical term + `(ξ_n/c)²` spectral weight
- [x] Two-oscillator Sellmeier model — anchored to Caldwell & Fan (1959), Stuke (1965)
- [x] Drude model (Au/SiO₂ benchmark validated, Our/PC ≈ 0.35–0.55)
- [x] Drude-Lorentz model (Td-WTe₂ Weyl semimetal)
- [x] Airy/transfer-matrix finite-slab correction (1.2% for QNT-26-100)
- [x] NSGA-II 3-objective optimizer (F1=|E|, F2=thickness, F3=thermal fraction)
- [x] p_max clamped to 1e6 in all outer-integrand functions — no more IntegrationWarnings
- [x] `casimir_energy_2osc` breakpoints sorted — scipy.quad correctness
- [x] 82 tests passing (pytest) across casimir_tools + src

---

## ✅ DONE — Paper Draft

- [x] Abstract ≤ 150 words (143 words ✓)
- [x] Abstract uses asymmetric Silveirinha formula result (κ_crit_asym ≈ 5.8)
- [x] Section I.E: 5-section list II–VI (no phantom Section III)
- [x] Section II.F: Asymmetric chiral formula derived and presented
- [x] Section II.A: Correct prefactor `ħ/(4π²c²)` in formula display
- [x] Section III.B: Matsubara `ξ_n²/c²` spectral weight factor explicit
- [x] Section III.D: χ table has separate symmetric/asymmetric columns
- [x] Section IV.C: κ_crit = 0.806 for Te|Te (not 0.831 from wrong formula)
- [x] Section IV.E: 0/50 Pareto solutions repulsive for Te|WTe₂
- [x] Section IV.H: Td/hex ratio ~2× (not ~4×); chirality NOT achievable for Td either
- [x] Section V.C: Reference [16] (Antezza 2008) in place of `[refs needed]`
- [x] Section V.C: Finite-slab correction 1.2% mentioned
- [x] Table II: Correct values at d=84.2nm; asymmetric formula rows clearly labelled
- [x] Figure 9 caption: "~2×" (not "~4×")
- [x] References [1]–[25] in citation order
- [x] Acknowledgments section present (SERB CRG, KEC HPC, Materials Project)
- [x] All sections in full prose (not bullet points)

---

## ⬜ TODO — **YOU MUST DO THESE** before submitting

### Personal / Administrative
- [ ] **Fill in your real full name** in `docs/cover_letter.md` and `docs/ieee_draft_outline.md` author line
- [ ] **Add email address** (correspondence author)
- [x] **ORCID** — 0009-0007-5498-8076 (registered)
- [x] **Full institution name** — "Dept. of Artificial Intelligence and Machine Learning, Kongu Engineering College, Perundurai, Erode 638060, Tamil Nadu, India"
- [ ] **Faculty advisor/PI** — consider adding as co-author for credibility (IEEE allows UG solo papers but faculty co-author helps)
- [ ] **SERB grant number** — replace `[Grant No. TBD]` in Acknowledgments once assigned

### Technical
- [ ] **Re-run pipeline** after any new optimizer run: `uv run python main.py --lifshitz --plot && uv run python sync_assets.py`
- [x] **PyPI publish**: `casimir-tools v0.1.5` live at pypi.org/project/casimir-tools/
- [x] **GitHub repository** — public at github.com/ss-sevesh/spaceship_bubble, add README link in cover letter
- [ ] **Verify all 12 figures are 300 dpi** — run `python -c "from PIL import Image; img=Image.open('plots/casimir_tellurium.png'); print(img.info.get('dpi'))"`

### Cover Letter
- [ ] Add GitHub repo link in cover letter
- [ ] Choose 2–3 reviewers from the suggested list that you have not cited (to avoid conflict of interest flags)
- [ ] Sign the cover letter (typed full name is fine for online submission)

### Submission Portal (IEEE ScholarOne)
- [ ] Create account at https://mc.manuscriptcentral.com/tnano
- [ ] Upload manuscript as PDF (convert from markdown to LaTeX or Word first)
- [ ] Upload figures separately as 300 dpi EPS/TIFF/PDF (not PNG — IEEE prefers vector)
- [ ] Complete copyright transfer form (IEEE eCP)
- [ ] Select "Regular Paper" as manuscript type
- [ ] Add keywords from the paper (Casimir effect, stiction, Lifshitz theory, chiral metamaterial, tellurium, WTe₂, MEMS, NSGA-II)

---

## ⚠️ Known Caveats to Mention in Response to Reviewers

1. **Td-WTe₂ dielectric tensor** is a model estimate (HSE06-level), not from a published ab initio run. ±10% uncertainty assigned. Experimental ellipsometry would replace it.
2. **Finite-slab correction** is 1.2% for the primary design — negligible; stated in V.C.
3. **κ_eff ∝ N scaling** is a first-order model; inter-layer coupling corrections are O(κ₀²d/λ) and negligible for d ≪ λ_UV.
4. **Au/SiO₂ benchmark**: Our/PC ≈ 0.21 at d=100nm is physically correct (not a bug).

---

## Estimated Time to Submission

| Task | Effort |
|------|--------|
| Fill personal details in cover letter + draft | 15 min |
| Register ORCID | 5 min |
| Convert draft to LaTeX/PDF | 2–4 hrs |
| Upload to ScholarOne + complete forms | 30 min |
| **Total** | **~1 day** |

---

*Checklist last updated: 2026-04-06 (Session 28)*
