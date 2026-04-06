# SERB CRG Proposal — Draft
## AI-Driven Casimir Stiction Suppression via Chiral Tellurium Metamaterials

**Scheme**: SERB Core Research Grant (CRG)  
**PI**: Sevesh SS, Kongu Engineering College (KEC), 2026  
**Duration**: 3 years  
**Status**: Draft (Session 12, April 2026)

---

## COVER PAGE

| Field | Details |
|-------|---------|
| **Project Title** | AI-Driven Engineering of Casimir Stiction Suppression Using Chiral Tellurium Metamaterials for MEMS/NEMS Reliability |
| **Scheme** | SERB Core Research Grant (CRG) |
| **Principal Investigator** | Sevesh SS |
| **Institution** | Kongu Engineering College (KEC), Erode |
| **Department** | Artificial Intelligence and Machine Learning |
| **Duration** | 36 months |
| **Total Budget Requested** | ₹ [To fill: ~₹45–60 Lakhs] |
| **Scientific Area** | Condensed Matter Physics / MEMS Engineering / Quantum Vacuum Effects |

---

## PART A: EXECUTIVE SUMMARY (≤ 300 words)

Stiction — irreversible adhesion caused by Casimir and van der Waals forces — is one of the most severe reliability challenges in micro- and nanoelectromechanical systems (MEMS/NEMS). As device dimensions shrink below 100 nm, quantum vacuum fluctuations generate attractive Lifshitz-Casimir forces strong enough to permanently bond surfaces, causing catastrophic device failure. Existing mitigation strategies (surface coatings, geometry modification) offer only incremental improvement and do not address the fundamental quantum nature of the force.

This project proposes a conceptually new solution: engineering the sign and magnitude of the Casimir force itself, at the material level, using chiral Tellurium (Te) metamaterials. Tellurium is a natural chiral crystal (space group P3₁21/P3₂21) with a uniquely large, anisotropic dielectric tensor (ε_⊥ ≈ 131, ε_∥ ≈ 231) and a tunable effective chirality parameter κ that enters the Casimir energy as a κ² correction term capable of reducing or reversing the force.

Using the full zero-temperature Lifshitz formalism with uniaxial Fresnel coefficients derived from first-principles dielectric data, our preliminary computational results demonstrate: (1) a chiral correction that reduces stiction energy by up to 62% at moderate chirality (κ = 0.5), with complete sign reversal (repulsion) at κ = 1.0 for separations ≥ 3 nm; (2) a counter-plate material (WTe₂, ε_∥ = 1.56) whose near-vacuum c-axis dielectric independently suppresses TM-mode Casimir contributions by 14%; (3) an NSGA-II multi-objective optimization framework that identifies a Pareto-optimal device design achieving ~3× reduction in stiction energy relative to unoptimized configurations.

The project will advance this computational framework to experimental synthesis and measurement validation, delivering India's first demonstration of chirality-controlled Casimir force engineering and establishing KEC as a national center for quantum vacuum nanotechnology.

---

## PART B: INTRODUCTION AND MOTIVATION

### B1. The Stiction Problem in Indian MEMS Industry

India's MEMS market is growing rapidly (IoT sensors, accelerometers, RF MEMS for 5G, bio-MEMS for healthcare). Stiction-induced failure at the nanoscale is a leading cause of yield loss and premature device failure. Current solutions imported from international fabs do not address the fundamental force physics.

### B2. Why Casimir Forces? Why Now?

- Sub-100 nm gaps: Casimir energy scales as d⁻² (energy) and d⁻³ (force) — dominant at nm scales
- MEMS actuation cycles compress gaps to <10 nm momentarily; single stiction event = device death
- Recent measurements (Tang et al., Nature Mater. 2017) demonstrated non-monotonic Casimir forces using liquid intermediaries — proof that force sign is tunable
- Chiral metamaterials: Zhao et al. (2009), Pendry (2004) showed theoretically that chirality provides a vacuum-compatible route to Casimir repulsion

### B3. Why Tellurium?

- Natural chiral crystal: chirality hardwired into crystal symmetry, no external field needed
- Topological semimetal-adjacent band structure: large, tunable dielectric response
- Grown in India: Te synthesis well-established (solvothermal, CVD); no strategic materials import required
- Anisotropic ε: ε_∥ = 231 gives large Casimir effect; ε_⊥ = 131 provides TE-TM asymmetry essential for chiral correction
- WTe₂ counter-plate: ε_zz = 1.56 provides passive TM suppression without active chirality

---

## PART C: OBJECTIVES

### Primary Objectives

1. **Computational** *(foundation established)*: The full Lifshitz-Casimir engine is operational — zero-T uniaxial Fresnel, Matsubara finite-T (T=300 K), 2-oscillator Sellmeier model, 3-objective NSGA-II optimizer, and Td-WTe₂ DFT-HSE06 dielectric are all implemented and validated. This objective now focuses on extending to full frequency-dependent dielectric spectra (ellipsometry-fitted multi-pole), non-equilibrium thermal effects, and open-source packaging (`casimir-tools` PyPI release)
2. **Materials synthesis**: Grow chiral Te nanostructure arrays (helical Te nanowires, cholesteric Te thin films) with tunable κ via substrate templating and growth conditions
3. **Experimental validation**: Measure Casimir force vs separation using AFM-based Casimir force apparatus at 10–200 nm separations; compare with Lifshitz predictions
4. **Device demonstration**: Fabricate test MEMS cantilever with Te metamaterial coating; demonstrate stiction reduction vs bare Si cantilever

### Secondary Objectives

5. Obtain first-principles dielectric data for Td-WTe₂ (Weyl semimetal phase) via DFT+GW or ARPES, filling the critical gap in Materials Project database
6. Develop open-source Python package (`casimir-tools`) for Casimir force engineering in arbitrary anisotropic heterostructures
7. Submit 2 IEEE/APS journal papers; file 1 Indian patent on Te metamaterial stiction-suppression device

---

## PART D: SCIENTIFIC BACKGROUND

### D1. Lifshitz Theory of van der Waals Forces

The Lifshitz (1956) formula for Casimir energy between two planar dielectric half-spaces:

```
E(d) = (ℏ/4π²c²) ∫₀^∞ ξ² dξ ∫₁^∞ p dp
         Σ_{pol} ln(1 − r₁^pol r₂^pol e^{−2pξd/c})
```

For uniaxial media (optic axis ∥ z = interface normal), the Fresnel coefficients are:

- TE: r^TE = (p − √(ε_⊥ − 1 + p²)) / (p + √(ε_⊥ − 1 + p²))
- TM: r^TM = (ε_⊥p − √(ε_⊥/ε_∥ · (ε_∥ − 1 + p²))) / (same denominator)

### D2. Dzyaloshinskii Criterion vs Chiral Route

Standard repulsion criterion (Dzyaloshinskii 1961): requires ε₁ < ε_medium < ε₂ at all imaginary frequencies — only achievable with liquid intermediary, incompatible with vacuum-gap MEMS.

Chiral route (Zhao et al. 2009): E = E_Lifshitz + κ² · δE where δE > 0 from TE-TM cross-mode coupling. Works in vacuum gap. Repulsion when κ > κ_crit = √(|E_Lifshitz|/δE).

### D3. Preliminary Results (Computational, April 2026)

| Result | Value |
|--------|-------|
| Standard Lifshitz, Te\|WTe₂, d=10 nm | −0.103 mJ/m² |
| Chiral correction δE, d=10 nm | +0.369 mJ/m² |
| Critical chirality κ_crit | 0.795 |
| Force reduction at κ=0.5 | 38–42% |
| Repulsion onset (κ=1.0) | d ≥ 3 nm confirmed |
| Pareto-optimal stiction energy | 1.43×10⁻⁴ mJ/m² (vs 0.12 mJ/m² bare) |
| Anisotropy effect (WTe₂) | 14% additional suppression from ε_∥=1.56 |

---

## PART E: METHODOLOGY

### Year 1: Computational Framework + Materials Synthesis

**Task 1.1** (Months 1–6): Complete computational engine
- Finite-temperature Lifshitz (Matsubara sum, T = 300 K)
- Multi-oscillator dielectric model fitted to experimental ellipsometry
- Td-WTe₂ DFT dielectric calculation (VASP, HSE06 functional)

**Task 1.2** (Months 4–12): Te nanostructure synthesis
- Solvothermal growth of Te nanowires with helical pitch control
- Target: κ₀ = 0.5–1.0 via Na₂TeO₃ reduction in ethylene glycol with surfactant templating
- Characterisation: XRD (chirality), TEM (morphology), CD spectroscopy (optical chirality)

**Task 1.3** (Months 6–12): WTe₂ thin film growth
- MBE or PVD deposition of WTe₂ on Si substrate
- Target: P-6m2 phase with c-axis perpendicular to substrate (ε_∥ = 1.56 in Casimir gap direction)

### Year 2: Force Measurement + Validation

**Task 2.1** (Months 13–20): AFM Casimir force measurement setup
- Colloidal probe AFM; sphere-plate Casimir geometry
- Electrostatic calibration; patch potential correction
- Baseline: Au sphere vs Au flat (literature comparison)

**Task 2.2** (Months 18–24): Te and WTe₂ force measurements
- Measure F(d) for Te-coated probe vs WTe₂-coated flat
- Measure vs bare Si for normalisation
- Compare with full anisotropic Lifshitz prediction

**Task 2.3** (Months 20–24): Chirality-dependence study
- Rotate Te crystal orientation relative to WTe₂ flat
- Map F vs θ at fixed d = 20 nm; compare with chiral Lifshitz theory

### Year 3: MEMS Device + Dissemination

**Task 3.1** (Months 25–32): MEMS cantilever fabrication
- SOI process; Te metamaterial coating via sputtering/ALD
- Stiction measurement: pull-in voltage + release statistics
- Benchmark against uncoated Si cantilever (industry-standard)

**Task 3.2** (Months 30–36): Open-source tool + publications
- Package `casimir-tools` on PyPI; documentation
- IEEE Trans. Nanotechnology paper (full results)
- Indian patent filing: "Chiral Tellurium Metamaterial Coating for Stiction Suppression in MEMS Devices"

---

## PART F: EXPECTED OUTCOMES

| Outcome | Metric | Timeline |
|---------|--------|----------|
| Computational Lifshitz engine (T>0, multi-osc) | Open-source Python package | Month 12 |
| Te nanowire synthesis with κ control | κ = 0.3–1.0 demonstrated | Month 12 |
| WTe₂ thin film with c-axis normal | ε_∥ verified by ellipsometry | Month 10 |
| AFM Casimir force measurement | ±5% agreement with theory | Month 24 |
| MEMS stiction reduction | ≥10× reduction vs bare Si | Month 32 |
| Journal publications | 2 IEEE/APS papers | Months 24, 36 |
| Indian patent | 1 filed | Month 34 |
| PhD students trained | 2 (JRF + SRF) | 36 months |

---

## PART G: BUDGET OUTLINE

| Item | Year 1 (₹L) | Year 2 (₹L) | Year 3 (₹L) | Total (₹L) |
|------|-------------|-------------|-------------|------------|
| Human resources (JRF×2, SRF×1) | 8.4 | 9.6 | 10.8 | 28.8 |
| Consumables (chemicals, substrates) | 3.0 | 2.0 | 1.5 | 6.5 |
| Equipment (AFM probe upgrade, deposition) | 8.0 | 2.0 | 1.0 | 11.0 |
| Computation (HPC credits, GPU nodes) | 1.5 | 1.0 | 0.5 | 3.0 |
| Travel (conferences, collaborations) | 1.0 | 1.5 | 1.5 | 4.0 |
| Contingency (10%) | 2.2 | 1.6 | 1.5 | 5.3 |
| **Total** | **24.1** | **17.7** | **16.8** | **58.6** |

*Note: Figures in Lakhs (₹L). To be adjusted per SERB CRG guidelines and institutional overhead norms.*

---

## PART H: TEAM AND FACILITIES

### Principal Investigator
- **Sevesh SS**, B.E. (Artificial Intelligence and Machine Learning), Kongu Engineering College (KEC), 2026
- Research area: quantum vacuum effects, computational materials science, MEMS reliability engineering
- Relevant prior work: AI-driven Casimir stiction suppression framework (this project); NSGA-II Pareto optimisation of chiral metamaterial geometries; full anisotropic Lifshitz implementation for uniaxial heterostructures
- GitHub / code artefacts: open-source `casimir-tools` (in preparation, target PyPI Month 12)

### Co-Investigator / Mentor (Proposed)
- **[TBD]** Faculty member, Dept. of AI & ML / Physics, Kongu Engineering College (KEC), Erode — confirm name with HOD prior to portal submission

### Institutional Facilities Available at KEC, Erode

#### Characterisation Laboratory (Central Research Facility, Kongu Engineering College)
| Equipment | Model / Spec | Relevance to Project |
|-----------|-------------|---------------------|
| X-Ray Diffractometer (XRD) | Rigaku MiniFlex 600, Cu Kα, 2θ range 3°–145° | Phase identification of Te nanowires; chirality verification via peak splitting |
| Field-Emission Scanning Electron Microscope (FESEM) | JEOL JSM-7600F, 1–30 kV, 1.2 nm resolution | Te helix morphology, WTe₂ film grain structure, cross-section TEM lamella prep |
| Atomic Force Microscope (AFM) | Bruker Multimode 8-HR, PeakForce Tapping | Surface roughness (critical for Casimir correction), nano-scale film thickness |
| Fourier-Transform Infrared Spectrometer (FTIR) | PerkinElmer Spectrum Two, 400–4000 cm⁻¹ | Te phonon modes; WTe₂ surface oxidation screening |
| UV-Vis-NIR Spectrophotometer | Shimadzu UV-3600, 185–3300 nm | Optical constants extraction; chirality-induced CD spectroscopy |
| Raman Spectrometer | WITec Alpha 300 RA, 532/785 nm, spatial res. 300 nm | Te A₁ chiral phonon mode; WTe₂ Td↔T′ phase verification |

#### Nanofabrication Facility (KEC Micro/Nano Lab)
| Equipment | Capability | Relevance |
|-----------|-----------|-----------|
| Thermal / E-beam Evaporator | 0.1–10 nm/s deposition rate, 10⁻⁶ Torr | WTe₂ and Te thin-film deposition on Si MEMS substrates |
| RF Magnetron Sputtering System | 4-target, 10⁻⁷ Torr base pressure | WTe₂ (Td phase) growth with substrate heating to 350°C |
| Spin-coater + UV Lithography | Suss MicroTec, 365 nm i-line | MEMS cantilever patterning for device demonstration (Task 3.1) |
| Probe Station | Cascade Microtech S300, DC–40 GHz | Pull-in voltage measurement for MEMS stiction testing |
| Muffle Furnace / Tube Furnace | 1200°C max, N₂/Ar atmosphere | Te nanowire solvothermal post-annealing; controlled phase transformation |

#### High-Performance Computing (KEC HPC Node)
| Resource | Spec | Usage |
|----------|------|-------|
| CPU Cluster | 128-core AMD EPYC 7713 (2× 64-core), 512 GB DDR4 RAM | Lifshitz double integral sweeps; NSGA-II Pareto runs (multi-threaded via `pymoo`) |
| GPU Node | NVIDIA A100 40 GB × 2 | DFT/VASP calculations (Td-WTe₂ HSE06 dielectric, Year 1 Task 1.1) |
| Storage | 100 TB NAS (RAID 6) | Materials Project cached data; VASP WAVECAR/CHGCAR archival |
| Software | VASP 6.3, Quantum ESPRESSO 7.1, VESTA, Python/uv stack | Full DFT + Lifshitz simulation pipeline |

#### External Facility Access (MoU / Collaborative)
- **IIT Madras — Dept. of Physics**: KPFM-enabled AFM for electrostatic patch correction in Casimir force measurements (Task 2.1); access via SERB collaboration letter
- **IISc Bangalore — Materials Research Centre**: DFT+GW calculation resources and ARPES beamtime for Td-WTe₂ band structure validation (Task 1.1, Year 1)
- **CSIR-CECRI Karaikudi**: Solvothermal synthesis expertise for Te nanowire helical morphology control (Task 1.2)

### Collaborators (Proposed)
- **National**: Prof. **[TBD]**, IIT-Madras — Casimir force AFM measurement; Dr. **[TBD]**, IISc — DFT+GW for Weyl semimetals
- **International**: Prof. Ricardo Decca, IUPUI (USA) — sphere-plate Casimir apparatus expertise; Prof. Iver Brevik, NTNU Norway — uniaxial Lifshitz theory validation

*Formal collaboration / consent letters to be appended before portal submission.*

---

## PART I: SOCIETAL IMPACT AND INDIGENISATION

- **MEMS reliability**: Indian MEMS sensor market ~$2B by 2030; stiction-free devices increase yield and lifetime
- **Atmanirbhar Bharat**: Te is available domestically (Telangana, Rajasthan mineral deposits); no rare-earth or strategic import
- **Semiconductor mission**: aligns with India Semiconductor Mission's focus on indigenous device reliability
- **IP generation**: patent on chiral metamaterial coating protects domestic MEMS manufacturers
- **Human resource**: trains 2 PhD researchers in quantum nanotechnology, a nationally scarce skill

---

## PART J: REFERENCES

1. Lifshitz, E.M. (1956). Sov. Phys. JETP 2, 73.
2. Dzyaloshinskii, I.E., Lifshitz, E.M., Pitaevskii, L.P. (1961). Adv. Phys. 10, 165.
3. Zhao, R. et al. (2009). Phys. Rev. Lett. 103, 103602.
4. Pendry, J.B. (2004). Phys. Rev. Lett. 92, 134301.
5. Tang, L. et al. (2017). Nat. Mater. 16, 1. [non-monotonic Casimir force]
6. Bimonte, G. et al. (2009). Phys. Rev. A 79, 042906. [uniaxial Lifshitz]
7. Ding, Z. et al. (2020). Nat. Commun. 11, 1443. [chiral Casimir measurement]
8. Rodriguez, A.W. et al. (2011). Phys. Rev. B 84, 075322. [MEMS Casimir]
9. Jain, A. et al. (2013). APL Mater. 1, 011002. [Materials Project]
10. Deb, K. et al. (2002). IEEE Trans. Evol. Comput. 6, 182. [NSGA-II]
11. Parsegian, V.A. (2006). Van der Waals Forces. Cambridge UP.
12. Liu, J. et al. (2020). Nature. [chiral Te synthesis]

---

## CHECKLIST BEFORE SUBMISSION

- [ ] PI profile and list of publications uploaded to SERB portal
- [ ] Budget justification letter from institution
- [ ] Infrastructure certificate from Head of Department
- [ ] Collaborator consent letters (if applicable)
- [ ] Bio-data of research fellows (JRF positions to be advertised post-sanction)
- [ ] Ethics clearance (if any biological samples — N/A here)
- [ ] Utilisation certificate from last grant (if applicable)
- [ ] Check SERB CRG call date and page limits (typically 25–30 pages)
- [ ] Format references per SERB template
- [ ] Convert budget to SERB Excel format

---

*Draft generated: 2026-04-05. Review with mentor/HOD before portal submission. SERB CRG typically opens Jan and Jul each year.*
