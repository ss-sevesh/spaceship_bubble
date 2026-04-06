import React, { useRef, useMemo } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { OrbitControls, Stars, Float, Text, MeshDistortMaterial, PerspectiveCamera } from '@react-three/drei';
import * as THREE from 'three';

// Helical Te chain: a chain of spheres winding around a central axis — models
// the real Te crystal structure (P3₁21 helical chains along c-axis).
const TeHelicalChain = ({ radius = 0.08, pitch = 0.32, turns = 3, color = '#a5b4fc' }) => {
  const points = useMemo(() => {
    const pts = [];
    const N = Math.round(turns * 12);
    for (let i = 0; i < N; i++) {
      const t = (i / N) * turns * Math.PI * 2;
      pts.push(new THREE.Vector3(
        Math.cos(t) * radius * 8,
        (i / N) * turns * pitch - (turns * pitch) / 2,
        Math.sin(t) * radius * 8
      ));
    }
    return pts;
  }, [radius, pitch, turns]);

  return (
    <group>
      {points.map((p, i) => (
        <mesh key={i} position={[p.x, p.y, p.z]}>
          <sphereGeometry args={[0.04, 8, 8]} />
          <meshStandardMaterial color={color} emissive={color} emissiveIntensity={0.8} roughness={0.2} metalness={0.9} />
        </mesh>
      ))}
    </group>
  );
};

// Orthorhombic WTe₂ unit cell wireframe — Td phase Pmn2₁ geometry
const WTe2UnitCell = ({ scale = 0.6 }) => {
  const edgeGeo = useMemo(() => new THREE.EdgesGeometry(new THREE.BoxGeometry(scale * 0.55, scale * 2.24, scale * 1.0)), [scale]);
  return (
    <group>
      <lineSegments geometry={edgeGeo}>
        <lineBasicMaterial color="#c084fc" transparent opacity={0.6} />
      </lineSegments>
      <mesh>
        <boxGeometry args={[scale * 0.55, scale * 2.24, scale * 1.0]} />
        <meshStandardMaterial color="#7e22ce" transparent opacity={0.08} side={THREE.DoubleSide} />
      </mesh>
    </group>
  );
};

// Global background nebula effect
export const GlobalBackground = () => {
  const points = useMemo(() => {
    const p = new Float32Array(2000 * 3);
    for (let i = 0; i < 2000; i++) {
      p[i * 3] = (Math.random() - 0.5) * 50;
      p[i * 3 + 1] = (Math.random() - 0.5) * 50;
      p[i * 3 + 2] = (Math.random() - 0.5) * 50;
    }
    return p;
  }, []);

  const ref = useRef();
  useFrame((state) => {
    if (!ref.current) return;
    const time = state.clock.elapsedTime;
    ref.current.rotation.y = time * 0.05;
    ref.current.rotation.x = Math.sin(time * 0.1) * 0.1;
  });

  return (
    <points ref={ref}>
      <bufferGeometry>
        <bufferAttribute attach="attributes-position" count={2000} array={points} itemSize={3} />
      </bufferGeometry>
      <pointsMaterial size={0.02} color="#4338ca" transparent opacity={0.4} sizeAttenuation />
    </points>
  );
};

const ParticleField = ({ count = 200, gap }) => {
  const points = useMemo(() => {
    const p = new Float32Array(count * 3);
    for (let i = 0; i < count; i++) {
      p[i * 3] = (Math.random() - 0.5) * 6;
      p[i * 3 + 1] = (Math.random() - 0.5) * gap;
      p[i * 3 + 2] = (Math.random() - 0.5) * 6;
    }
    return p;
  }, [count, gap]);

  const ref = useRef();
  useFrame((state) => {
    if (!ref.current) return;
    const time = state.clock.elapsedTime;
    const positions = ref.current.geometry.attributes.position.array;
    for (let i = 0; i < count; i++) {
      positions[i * 3 + 1] += Math.sin(time * 2 + i) * 0.002;
    }
    ref.current.geometry.attributes.position.needsUpdate = true;
    ref.current.rotation.y = time * 0.1;
  });

  return (
    <points ref={ref}>
      <bufferGeometry>
        <bufferAttribute attach="attributes-position" count={count} array={points} itemSize={3} />
      </bufferGeometry>
      <pointsMaterial size={0.04} color="#6366f1" transparent opacity={0.8} sizeAttenuation blending={THREE.AdditiveBlending} />
    </points>
  );
};

// Hexagonal prism — models the P3₁21 Te crystal cross-section
const HexPlate = ({ position, color, label, speed = 2, distort = 0.15, showChains = false }) => {
  const hex = useMemo(() => new THREE.CylinderGeometry(2.5, 2.5, 0.18, 6, 1), []);
  const wireGeo = useMemo(() => new THREE.CylinderGeometry(2.51, 2.51, 0.19, 6, 1), []);
  const ref = useRef();

  useFrame(({ clock }) => {
    if (ref.current) ref.current.rotation.y = clock.elapsedTime * 0.08;
  });

  // Chain positions at hex vertices + center
  const chainPositions = useMemo(() => [
    [0, 0], [1.5, 0], [-1.5, 0],
    [0.75, 1.3], [-0.75, 1.3], [0.75, -1.3], [-0.75, -1.3]
  ], []);

  return (
    <group position={position} ref={ref}>
      {/* Main plate */}
      <mesh>
        <primitive object={hex} />
        <meshPhysicalMaterial
          color={color}
          transparent
          opacity={0.65}
          roughness={0.05}
          metalness={0.9}
          clearcoat={1}
          clearcoatRoughness={0.1}
          emissive={color}
          emissiveIntensity={0.15}
        />
      </mesh>
      {/* Crystal edge wireframe */}
      <lineSegments>
        <edgesGeometry args={[wireGeo]} />
        <lineBasicMaterial color={color} transparent opacity={0.9} />
      </lineSegments>
      {/* Helical Te chains at crystal sites */}
      {showChains && chainPositions.map(([x, z], i) => (
        <group key={i} position={[x, 0, z]}>
          <TeHelicalChain radius={0.06} pitch={0.28} turns={2} color={color} />
        </group>
      ))}
      <Text position={[0, 0.5, 0]} fontSize={0.17} color="white" anchorX="center">
        {label}
      </Text>
    </group>
  );
};

// Orthorhombic WTe₂ plate with unit-cell decoration
const WTe2Plate = ({ position, color, label }) => {
  const ref = useRef();
  useFrame(({ clock }) => {
    if (ref.current) ref.current.rotation.y = -clock.elapsedTime * 0.06;
  });

  const cellPositions = useMemo(() => {
    const pos = [];
    for (let x = -1.5; x <= 1.5; x += 1.5)
      for (let z = -1.5; z <= 1.5; z += 1.5)
        pos.push([x, z]);
    return pos;
  }, []);

  const edgeGeo = useMemo(() => new THREE.EdgesGeometry(new THREE.BoxGeometry(5.01, 0.15, 5.01)), []);

  return (
    <group position={position} ref={ref}>
      <mesh>
        <boxGeometry args={[5.0, 0.14, 5.0]} />
        <meshPhysicalMaterial
          color={color}
          transparent
          opacity={0.6}
          roughness={0.1}
          metalness={0.85}
          clearcoat={0.8}
          emissive={color}
          emissiveIntensity={0.12}
        />
      </mesh>
      <lineSegments geometry={edgeGeo}>
        <lineBasicMaterial color={color} transparent opacity={0.85} />
      </lineSegments>
      {/* Td unit cell lattice ornaments */}
      {cellPositions.map(([x, z], i) => (
        <group key={i} position={[x, 0.1, z]}>
          <WTe2UnitCell scale={0.5} />
        </group>
      ))}
      <Text position={[0, 0.5, 0]} fontSize={0.17} color="white" anchorX="center">
        {label}
      </Text>
    </group>
  );
};

const MaterialPlate = ({ position, color, label, speed = 2, distort = 0.2 }) => {
  return (
    <group position={position}>
      <mesh>
        <boxGeometry args={[4.5, 0.15, 4.5]} />
        <MeshDistortMaterial
          color={color}
          speed={speed}
          distort={distort}
          radius={1}
          transparent
          opacity={0.7}
          roughness={0}
          metalness={1}
          emissive={color}
          emissiveIntensity={0.2}
        />
      </mesh>
      <Text position={[0, 0.4, 0]} fontSize={0.18} color="white" anchorX="center">
        {label}
      </Text>
    </group>
  );
};

const MetamaterialLayers = ({ nLayers, gap, kappa }) => {
  const layers = useMemo(() => {
    const l = [];
    const step = gap / (nLayers + 1);
    for (let i = 1; i <= nLayers; i++) {
      l.push({
        y: -gap / 2 + i * step,
        color: new THREE.Color().setHSL(0.6 + (i / nLayers) * 0.1, 0.9, 0.6),
        delay: i * 0.1
      });
    }
    return l;
  }, [nLayers, gap]);

  return (
    <group>
      {layers.map((layer, idx) => (
        <Float key={idx} speed={3} rotationIntensity={0.1} floatIntensity={0.2}>
          <mesh position={[0, layer.y, 0]}>
            <boxGeometry args={[4.3, 0.015, 4.3]} />
            <meshStandardMaterial 
              color={layer.color} 
              transparent 
              opacity={0.3 + (kappa * 0.5)} 
              emissive={layer.color}
              emissiveIntensity={1}
            />
          </mesh>
        </Float>
      ))}
    </group>
  );
};

const CasimirScene = ({ selectedDesign }) => {
  const nLayers = selectedDesign?.N_layers || 14;
  const gap = (selectedDesign?.d_nm || 50) / 10;
  const kappa = selectedDesign?.kappa_eff || 0.7;

  return (
    <div style={{ width: '100%', height: '100%', minHeight: '550px', background: 'transparent', position: 'relative' }}>
      <Canvas dpr={[1, 2]}>
        <PerspectiveCamera makeDefault position={[8, 6, 8]} fov={40} />
        <color attach="background" args={['#020408']} />
        
        <GlobalBackground />
        
        <ambientLight intensity={0.2} />
        <spotLight position={[10, 10, 10]} angle={0.15} penumbra={1} intensity={2} castShadow />
        <pointLight position={[-10, -10, -10]} color="#a855f7" intensity={1} />
        
        <Stars radius={100} depth={50} count={3000} factor={4} saturation={0} fade speed={1} />
        
        <Float speed={1.5} rotationIntensity={0.25} floatIntensity={0.3}>
          <group>
            {/* Te crystal: hexagonal P3₁21 with helical chains */}
            <HexPlate
              position={[0, gap / 2, 0]}
              color="#4f46e5"
              label="Te Crystal (P3₁21)"
              showChains={nLayers <= 10}
            />
            {/* WTe₂ substrate: orthorhombic Td with unit-cell wireframes */}
            <WTe2Plate
              position={[0, -gap / 2, 0]}
              color="#9333ea"
              label="Td-WTe₂ (Pmn2₁)"
            />
            <MetamaterialLayers nLayers={nLayers} gap={gap} kappa={kappa} />
            <ParticleField count={300} gap={gap} />
          </group>
        </Float>

        <OrbitControls makeDefault enableDamping dampingFactor={0.05} minDistance={5} maxDistance={20} />
      </Canvas>
      
      <div className="glass-panel" style={{ position: 'absolute', bottom: '1.5rem', left: '1.5rem', padding: '1rem', borderRadius: '16px', pointerEvents: 'none', background: 'rgba(0,0,0,0.4)' }}>
        <div style={{ fontSize: '0.6rem', color: 'var(--text-dim)', textTransform: 'uppercase', letterSpacing: '0.1em' }}>Quantum State</div>
        <div style={{ fontSize: '1.1rem', color: 'white', fontWeight: 'bold', display: 'flex', gap: '1rem' }}>
          <span>{nLayers} Layers</span>
          <span style={{ color: 'var(--primary)' }}>{ (gap*10).toFixed(1) }nm Gap</span>
        </div>
      </div>
    </div>
  );
};

export default CasimirScene;
