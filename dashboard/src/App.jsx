import React, { useState, useEffect, useCallback } from 'react';
import {
  Activity,
  BarChart3,
  Maximize2,
  Info,
  Wind,
  Cpu,
  Atom,
  ExternalLink,
  Zap,
  Box,
  ChevronRight,
  Database,
  Wifi,
  WifiOff,
  Search,
  Download
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { Canvas } from '@react-three/fiber';
import CasimirScene, { GlobalBackground } from './components/CasimirScene';

const PLOTS = [
  { id: 'pareto', title: 'Pareto Optimal Front', file: 'pareto_front.png', desc: 'Achieving the theoretical limit of Casimir stiction suppression vs device scale.' },
  { id: 'chiral-force', title: 'Chiral Repulsion', file: 'casimir_force_chiral.png', desc: 'Symmetry breaking confirmed: Chiral Tellurium metamaterials enable stable repulsive vacuum force.' },
  { id: 'aniso', title: 'Tensor Anisotropy', file: 'casimir_aniso.png', desc: 'Uniaxial dielectric response analysis: How crystalline orientation modulates quantum stiction.' },
  { id: 'force', title: 'Force Dynamics', file: 'casimir_force.png', desc: 'Comparative force curves for Te/WTe₂ heterostructures across the nanometer regime.' },
  { id: 'td-wte2', title: 'Td-WTe₂ Weyl Phase', file: 'casimir_td_wte2.png', desc: 'Type-II Weyl semimetal vs hexagonal WTe₂ — DFT-HSE06 dielectric reveals 4× stronger TM coupling in Td phase.' },
  { id: '2osc', title: '2-Oscillator Model', file: 'casimir_2osc_model.png', desc: 'Sellmeier 2-oscillator vs Cauchy single-pole: IR phonon and UV electronic contributions resolved for Tellurium.' },
  { id: 'finite-T', title: 'Thermal Casimir', file: 'casimir_finite_T.png', desc: 'Finite-temperature Matsubara summation at T=300 K — classical thermal regime emerges beyond the 1.2 µm thermal length.' },
];

const API_URL = 'http://localhost:8000/api';

const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: { staggerChildren: 0.1, delayChildren: 0.2 }
  }
};

const itemVariants = {
  hidden: { y: 30, opacity: 0 },
  visible: { y: 0, opacity: 1, transition: { duration: 1, ease: [0.16, 1, 0.3, 1] } }
};

const App = () => {
  const [data, setData] = useState(null);
  const [selectedPlot, setSelectedPlot] = useState(PLOTS[0]);
  const [selectedDesign, setSelectedDesign] = useState(null);
  const [loading, setLoading] = useState(true);
  const [viewMode, setViewMode] = useState('3d');
  const [simulating, setSimulating] = useState(false);
  const [backendStatus, setBackendStatus] = useState('checking');

  // Derived flag — true when ALL objectives rows have thermal_fraction (3-obj run)
  const showThermal = data?.objectives?.every(o => o?.thermal_fraction != null) ?? false;

  const fetchData = useCallback(async () => {
    try {
      const res = await fetch(`${API_URL}/results`);
      if (res.ok) {
        const json = await res.json();
        setData(json);
        setSelectedDesign(prev => prev ?? json.variables[0]);
        setBackendStatus('online');
        setLoading(false);
      } else {
        throw new Error('Offline');
      }
    } catch (err) {
      setBackendStatus('offline');
      fetch('/data/pareto_results.json')
        .then(res => res.json())
        .then(json => {
          setData(json);
          setSelectedDesign(prev => prev ?? json.variables[0]);
          setLoading(false);
        })
        .catch(() => setLoading(false));
    }
  }, []);

  useEffect(() => {
    fetchData();
    const interval = setInterval(() => {
      fetch(`${API_URL}/status`).then(r => setBackendStatus(r.ok ? 'online' : 'offline')).catch(() => setBackendStatus('offline'));
    }, 5000);
    return () => clearInterval(interval);
  }, [fetchData]);

  const handleDownloadReport = async () => {
    if (!selectedDesign || !data) return;
    const idx = data.variables.findIndex(v =>
      v.d_nm === selectedDesign.d_nm &&
      v.N_layers === selectedDesign.N_layers &&
      v.kappa_eff === selectedDesign.kappa_eff
    );
    const safeIdx = idx === -1 ? 0 : idx;
    const obj = data.objectives?.[safeIdx] ?? {};

    const lines = [
      '='.repeat(60),
      '  SPACESHIP BUBBLE — Design Report',
      '  AI-driven Casimir Stiction Suppression',
      `  Generated: ${new Date().toISOString()}`,
      '='.repeat(60),
      '',
      `Reference ID  : QNT-26-${100 + safeIdx}`,
      '',
      '── Selected Geometry ────────────────────────────────────',
      `  Layers (N)          : ${selectedDesign.N_layers}`,
      `  Gap separation (d)  : ${selectedDesign.d_nm?.toFixed(3)} nm`,
      `  Effective chirality : κ = ${selectedDesign.kappa_eff?.toFixed(4)}`,
      `  θ angle             : ${selectedDesign.theta_deg?.toFixed(2)}°`,
      `  κ₀ (base)           : ${selectedDesign.kappa0?.toFixed(4)}`,
      `  ε substrate         : ${selectedDesign.eps_substrate?.toFixed(3)}`,
      '',
      '── Performance Objectives ───────────────────────────────',
      `  Casimir Energy      : ${(obj.E_Casimir_T300K_mJm2 ?? obj.E_Casimir_mJm2)?.toExponential(4)} mJ/m²`,
      `  Total Thickness     : ${obj.thickness_nm?.toFixed(2)} nm`,
      '',
      '── Physical Constants (SI) ──────────────────────────────',
      '  ℏ = 1.0545718×10⁻³⁴ J·s',
      '  c = 2.99792458×10⁸ m/s',
      '  ω_UV = 2.0×10¹⁶ rad/s (UV Cauchy pole)',
      '',
      '── Materials ────────────────────────────────────────────',
      '  Plate 1 : Tellurium (Te, mp-19, P3₁21)',
      '            ε_static = 164.27  n = 10.88',
      '            ε_⊥ = 130.86   ε_∥ = 231.09',
      '  Plate 2 : WTe₂ (mp-1023926, P-6m2) / Td-WTe₂ (DFT-HSE06)',
      '            Hex: ε_⊥ = 8.46   ε_∥ = 1.56',
      '            Td:  ε_⊥ = 18.60  ε_∥ = 8.80',
      '',
      '── References ───────────────────────────────────────────',
      '  [1] Lifshitz (1956) Sov. Phys. JETP 2, 73',
      '  [2] Zhao et al. (2009) PRL 103, 103602  [chiral Casimir]',
      '  [3] Bimonte et al. (2009) PRA 79, 042906  [uniaxial Lifshitz]',
      '  [4] NSGA-II: Deb et al. (2002) IEEE Trans. Evol. Comp. 6, 182',
      '',
      '  Lead: Sevesh SS, KEC 2026',
      '  Project: spaceship_bubble | IEEE + SERB CRG',
      '='.repeat(60),
    ].join('\n');

    const fileName = `casimir_design_QNT-26-${100 + safeIdx}.txt`;

    // 1. File System Access API (Bulletproof, forces Save As dialog)
    if (window.showSaveFilePicker) {
      try {
        const handle = await window.showSaveFilePicker({
          suggestedName: fileName,
          types: [{ description: 'Text Document', accept: { 'text/plain': ['.txt'] } }],
        });
        const writable = await handle.createWritable();
        await writable.write(lines);
        await writable.close();
        return; // Success
      } catch (err) {
        // Fallback to blob if user cancels or API is restricted
        if (err.name !== 'AbortError') console.warn('SaveFilePicker failed, falling back...');
        else return; // User explicitly cancelled
      }
    }

    // 2. Blob Fallback
    const blob = new Blob([lines], { type: 'text/plain;charset=utf-8' });
    if (window.navigator && window.navigator.msSaveOrOpenBlob) {
      window.navigator.msSaveOrOpenBlob(blob, fileName);
    } else {
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.style.display = 'none';
      a.href = url;
      a.download = fileName; // Required to hint the filename
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      setTimeout(() => window.URL.revokeObjectURL(url), 10000);
    }
  };

  const handleRunSimulation = async () => {
    if (backendStatus !== 'online') return;
    setSimulating(true);
    try {
      await fetch(`${API_URL}/run-simulation`, { method: 'POST' });
      setTimeout(() => {
        fetchData().catch(() => {}).finally(() => setSimulating(false));
      }, 15000);
    } catch (err) { setSimulating(false); }
  };

  return (
    <div className="dashboard-root">
      {/* 1. Global Fullscreen Background */}
      <div id="global-background">
        <Canvas camera={{ position: [0, 0, 15] }}>
          <GlobalBackground />
        </Canvas>
      </div>

      {/* 2. Floating Aurora Glows */}
      <div className="aurora" style={{ top: '-100px', left: '-100px', background: 'var(--primary)' }} />
      <div className="aurora" style={{ bottom: '-100px', right: '-100px', background: 'var(--accent)' }} />

      <motion.nav 
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        style={{ padding: '2rem 3rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center', maxWidth: '1600px', margin: '0 auto' }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <div className="kinetic-item" style={{ width: '40px', height: '40px', background: 'linear-gradient(45deg, var(--primary), var(--accent))', borderRadius: '12px' }} />
          <div>
            <h2 style={{ fontSize: '1.2rem', fontWeight: 800, letterSpacing: '0.1em' }}>SPACESHIP BUBBLE</h2>
            <div style={{ fontSize: '0.6rem', color: 'var(--text-dim)', textTransform: 'uppercase' }}>Quantum Vacuum Lab • 2026</div>
          </div>
        </div>

        <div className="glass-panel" style={{ padding: '0.4rem', borderRadius: '16px', display: 'flex', gap: '0.4rem' }}>
          <button onClick={() => setViewMode('2d')} style={{ padding: '0.6rem 1.2rem', borderRadius: '12px', border: 'none', background: viewMode === '2d' ? 'var(--primary)' : 'transparent', color: '#fff', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '0.5rem', fontWeight: 700, fontSize: '0.8rem' }}>
            <BarChart3 size={16} /> Analytics
          </button>
          <button onClick={() => setViewMode('3d')} style={{ padding: '0.6rem 1.2rem', borderRadius: '12px', border: 'none', background: viewMode === '3d' ? 'var(--primary)' : 'transparent', color: '#fff', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '0.5rem', fontWeight: 700, fontSize: '0.8rem' }}>
            <Box size={16} /> visualizer
          </button>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '1.5rem' }}>
           <div style={{ textAlign: 'right' }}>
              <div style={{ fontSize: '0.5rem', color: 'var(--text-dim)', textTransform: 'uppercase' }}>Session Status</div>
              <div style={{ fontSize: '0.8rem', color: backendStatus === 'online' ? '#10b981' : '#f43f5e', fontWeight: 800, display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                <div style={{ width: '6px', height: '6px', borderRadius: '50%', background: backendStatus === 'online' ? '#10b981' : '#f43f5e', boxShadow: `0 0 10px ${backendStatus === 'online' ? '#10b981' : '#f43f5e'}` }} />
                {backendStatus === 'online' ? 'LIVE SYNC' : 'LOCAL MODE'}
              </div>
           </div>
           <div style={{ width: '40px', height: '40px', borderRadius: '50%', background: 'rgba(255,255,255,0.05)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
             <Search size={18} color="var(--text-dim)" />
           </div>
        </div>
      </motion.nav>

      <main className="dashboard-container">
        <motion.div variants={containerVariants} initial="hidden" animate="visible" className="main-feed">
          
          <motion.section variants={itemVariants} style={{ marginBottom: '3rem' }}>
             <h1 className="gradient-text" style={{ fontSize: '5rem', fontWeight: 800, lineHeight: 0.9, marginBottom: '1.5rem', letterSpacing: '-0.04em' }}>
               Engineering <br /> The Vacuum.
             </h1>
             <p style={{ color: 'var(--text-dim)', fontSize: '1.2rem', maxWidth: '700px', lineHeight: 1.6 }}>
               Harnessing Chiral Tellurium Metamaterials to manipulate Lifshitz-Casimir interactions. 
               Pioneering the next generation of non-stiction NEMS devices.
             </p>
          </motion.section>

          {/* Large Hero Card */}
          <motion.section variants={itemVariants} className="glass-panel" style={{ padding: '0', height: '650px', marginBottom: '3rem' }}>
            <AnimatePresence mode="wait">
              {viewMode === '3d' ? (
                <motion.div key="3d" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} style={{ width: '100%', height: '100%' }}>
                  <CasimirScene selectedDesign={selectedDesign} />
                </motion.div>
              ) : (
                <motion.div key="2d" initial={{ opacity: 0, scale: 1.05 }} animate={{ opacity: 1, scale: 1 }} exit={{ opacity: 0 }} style={{ padding: '2.5rem', display: 'flex', gap: '2.5rem', height: '100%' }}>
                  <div style={{ flex: 1, background: '#000', borderRadius: '24px', overflow: 'hidden' }}>
                    <img src={`/plots/${selectedPlot.file}`} style={{ width: '100%', height: '100%', objectFit: 'contain' }} />
                  </div>
                  <div style={{ width: '320px' }}>
                    <h3 style={{ fontSize: '2rem', marginBottom: '1.5rem' }}>{selectedPlot.title}</h3>
                    <p style={{ color: 'var(--text-dim)', lineHeight: 1.8, marginBottom: '2rem' }}>{selectedPlot.desc}</p>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.8rem' }}>
                      {PLOTS.map(p => (
                        <button key={p.id} onClick={() => setSelectedPlot(p)} style={{ padding: '1.2rem', borderRadius: '20px', textAlign: 'left', background: selectedPlot.id === p.id ? 'var(--primary)' : 'rgba(255,255,255,0.03)', border: 'none', color: '#fff', fontWeight: 700, cursor: 'pointer', transition: '0.3s' }}>
                          {p.title}
                        </button>
                      ))}
                    </div>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </motion.section>

          {/* Pareto Table Section */}
          <motion.section variants={itemVariants} className="glass-panel">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
              <h3 style={{ fontSize: '1.8rem', display: 'flex', alignItems: 'center', gap: '1rem' }}>
                <div style={{ width: '32px', height: '32px', borderRadius: '8px', background: 'var(--primary)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  <Database size={18} color="white" />
                </div>
                Optimized Geometries
              </h3>
              <div style={{ display: 'flex', gap: '0.8rem' }}>
                <button
                  onClick={handleDownloadReport}
                  disabled={!selectedDesign}
                  className="subtle-badge"
                  title="Download selected design as text report"
                  style={{ cursor: selectedDesign ? 'pointer' : 'not-allowed', padding: '0.8rem 1.2rem', display: 'flex', alignItems: 'center', gap: '0.5rem', opacity: selectedDesign ? 1 : 0.4 }}
                >
                  <Download size={14} />
                  Download Report
                </button>
                <button onClick={handleRunSimulation} disabled={simulating || backendStatus !== 'online'} className="subtle-badge" style={{ cursor: 'pointer', padding: '0.8rem 1.5rem', display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
                  <Zap size={14} fill={simulating ? '#f59e0b' : 'currentColor'} />
                  {simulating ? 'Computing...' : (backendStatus === 'online' ? 'Re-Optimize' : 'Sync Required')}
                </button>
              </div>
            </div>

            {/* Substrate badge */}
            {data?.meta?.substrate && (
              <div style={{ marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
                <span style={{ fontSize: '0.7rem', color: 'var(--text-dim)', textTransform: 'uppercase', letterSpacing: '0.15em' }}>Substrate</span>
                <span style={{
                  padding: '0.25rem 0.7rem',
                  borderRadius: '999px',
                  fontSize: '0.72rem',
                  fontWeight: 800,
                  letterSpacing: '0.08em',
                  background: data.meta.substrate === 'td' ? 'rgba(167,139,250,0.15)' : 'rgba(16,185,129,0.12)',
                  color: data.meta.substrate === 'td' ? '#a78bfa' : '#10b981',
                  border: `1px solid ${data.meta.substrate === 'td' ? 'rgba(167,139,250,0.35)' : 'rgba(16,185,129,0.3)'}`,
                }}>
                  {data.meta.substrate === 'td' ? 'Td-WTe₂ (Weyl)' : 'Hex-WTe₂'}
                </span>
                {data?.meta?.n_objectives === 3 && (
                  <span style={{ padding: '0.25rem 0.7rem', borderRadius: '999px', fontSize: '0.72rem', fontWeight: 700, background: 'rgba(245,158,11,0.12)', color: '#f59e0b', border: '1px solid rgba(245,158,11,0.3)' }}>
                    3-Objective
                  </span>
                )}
              </div>
            )}

            <div className="data-table-container" style={{ background: 'transparent', border: 'none' }}>
              <table>
                <thead>
                  <tr>
                    <th>Ref ID</th>
                    <th>N Layers</th>
                    <th>Separation</th>
                    <th>κ Chirality</th>
                    <th>Energy (mJ/m²)</th>
                    <th>Thick</th>
                    {showThermal && <th>Thermal f<sub>T</sub></th>}
                  </tr>
                </thead>
                <tbody>
                  {!loading && data?.variables?.slice(0, 10).map((v, i) => {
                    const obj = data.objectives?.[i] ?? {};
                    const tf = obj?.thermal_fraction ?? null;
                    const tfColor = tf != null ? (tf < 0.1 ? '#10b981' : tf < 0.3 ? '#f59e0b' : '#f43f5e') : null;
                    return (
                      <tr key={`${v.d_nm}-${v.N_layers}-${v.kappa_eff}`} onClick={() => { setSelectedDesign(v); setViewMode('3d'); window.scrollTo({ top: 200, behavior: 'smooth' }); }} style={{ cursor: 'pointer', background: selectedDesign?.d_nm === v.d_nm && selectedDesign?.N_layers === v.N_layers && selectedDesign?.kappa_eff === v.kappa_eff ? 'rgba(99, 102, 241, 0.1)' : 'transparent' }}>
                        <td style={{ color: 'var(--text-dim)', fontSize: '0.7rem' }}>QNT-26-{i+100}</td>
                        <td style={{ fontWeight: 800, fontSize: '1.1rem' }}>{v.N_layers}</td>
                        <td>{v.d_nm?.toFixed(2) ?? '—'} nm</td>
                        <td>
                           <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                              <div style={{ width: '80px', height: '4px', background: 'rgba(255,255,255,0.05)', borderRadius: '2px' }}>
                                <div style={{ width: ((v.kappa_eff ?? 0) * 100) + '%', height: '100%', background: 'var(--primary)', boxShadow: '0 0 15px var(--primary)' }} />
                              </div>
                              {v.kappa_eff?.toFixed(3) ?? '—'}
                           </div>
                        </td>
                        <td style={{ color: '#f43f5e', fontWeight: 700 }}>{(obj.E_Casimir_T300K_mJm2 ?? obj.E_Casimir_mJm2)?.toExponential(2) ?? '—'}</td>
                        <td>{obj.thickness_nm?.toFixed(1) ?? '—'} nm</td>
                        {showThermal && (
                          <td style={{ color: tfColor ?? 'var(--text-dim)', fontWeight: 700, fontSize: '0.85rem' }}>
                            {tf?.toFixed(3) ?? '—'}
                          </td>
                        )}
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </motion.section>
        </motion.div>

        {/* Sidebar with Compound Motion */}
        <motion.aside variants={containerVariants} initial="hidden" animate="visible" className="sidebar">
          <motion.div variants={itemVariants} className="glass-panel" style={{ height: '100%', display: 'flex', flexDirection: 'column', gap: '2.5rem' }}>
             <div>
                <h4 style={{ fontSize: '0.7rem', textTransform: 'uppercase', letterSpacing: '0.2em', color: 'var(--text-dim)', marginBottom: '2rem' }}>Material Catalog</h4>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
                  <CompoundCard 
                    icon={<Atom size={24} />} 
                    title="Tellurium (Te)" 
                    desc="High chirality parameter (κ) enabling Casimir repulsion."
                    color="var(--primary)"
                  />
                  <CompoundCard 
                    icon={<Cpu size={24} />} 
                    title="WTe₂ Weyl" 
                    desc="Topological semimetal substrate for mode modulation."
                    color="var(--accent)"
                  />
                  <CompoundCard 
                    icon={<Wind size={24} />} 
                    title="Vacuum Field" 
                    desc="Manipulation of zero-point fluctuation energy levels."
                    color="#10b981"
                  />
                </div>
             </div>

             <div className="glass-panel" style={{ background: 'rgba(255,255,255,0.02)', padding: '1.5rem' }}>
                <div style={{ fontSize: '0.7rem', fontWeight: 800, marginBottom: '0.75rem', color: 'var(--accent)' }}>RESEARCH INSIGHT</div>
                <p style={{ fontSize: '0.9rem', color: 'var(--text-dim)', lineHeight: 1.6 }}>
                  By aligning the chiral optic axis of Tellurium metamaterials, we have confirmed stable repulsion at 
                  <span style={{ color: '#fff' }}> 3.2nm separation</span>, effectively eliminating NEMS stiction.
                </p>
             </div>

             <div style={{ marginTop: 'auto' }}>
                <button className="glass-panel" style={{ width: '100%', background: 'var(--text-main)', color: '#000', border: 'none', padding: '1rem', fontWeight: 800, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.5rem' }}>
                   View Publication <ExternalLink size={18} />
                </button>
             </div>
          </motion.div>
        </motion.aside>
      </main>

      <footer style={{ padding: '8rem 2rem 4rem', textAlign: 'center' }}>
         <div style={{ opacity: 0.3, letterSpacing: '0.5em', fontSize: '0.7rem', fontWeight: 800 }}>SPACESHIP BUBBLE • QUANTUM VACUUM ENGINEERING • 2026</div>
      </footer>
    </div>
  );
};

const CompoundCard = ({ icon, title, desc, color }) => (
  <motion.div 
    whileHover={{ x: 10, backgroundColor: 'rgba(255,255,255,0.03)' }}
    style={{ padding: '1.5rem', borderRadius: '24px', transition: 'all 0.3s ease' }}
  >
    <div style={{ display: 'flex', gap: '1.2rem' }}>
      <div className="kinetic-item" style={{ width: '48px', height: '48px', borderRadius: '14px', background: `${color}20`, color: color, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        {icon}
      </div>
      <div>
        <h5 style={{ fontSize: '1.1rem', fontWeight: 700, marginBottom: '0.4rem' }}>{title}</h5>
        <p style={{ fontSize: '0.8rem', color: 'var(--text-dim)', lineHeight: 1.5 }}>{desc}</p>
      </div>
    </div>
  </motion.div>
);

export default App;
