import React, { useRef, useEffect } from 'react';
import * as THREE from 'three';

interface ThreeVisualizationProps {
  results: {
    paths: number[][];
    finalValues: number[];
    timestamps: number[];
    confidenceIntervals?: {
      '10%': number[];
      '25%': number[];
      '50%': number[];
      '75%': number[];
      '90%': number[];
    };
  };
}

const ThreeVisualization: React.FC<ThreeVisualizationProps> = ({ results }) => {
  const mountRef = useRef<HTMLDivElement>(null);
  const sceneRef = useRef<THREE.Scene | null>(null);
  const rendererRef = useRef<THREE.WebGLRenderer | null>(null);
  const animationRef = useRef<number | null>(null);

  // 3D Visualization with Three.js
  useEffect(() => {
    if (!results || !mountRef.current) return;

    // Clean up previous scene
    if (rendererRef.current) {
      rendererRef.current.dispose();
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
    }

    const width = mountRef.current.clientWidth;
    const height = 400;

    // Scene setup
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0xf8fafc);
    sceneRef.current = scene;

    const camera = new THREE.PerspectiveCamera(75, width / height, 0.1, 1000);
    const renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setSize(width, height);
    renderer.shadowMap.enabled = true;
    renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    rendererRef.current = renderer;

    mountRef.current.appendChild(renderer.domElement);

    // Add lighting
    const ambientLight = new THREE.AmbientLight(0x404040, 0.6);
    scene.add(ambientLight);

    const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8);
    directionalLight.position.set(50, 50, 50);
    directionalLight.castShadow = true;
    scene.add(directionalLight);

    // Create 3D paths
    const pathsToShow = Math.min(results.paths.length, 100); // Limit for performance
    const pathStep = Math.floor(results.paths.length / pathsToShow);
    
    for (let i = 0; i < pathsToShow; i++) {
      const pathIndex = i * pathStep;
      const path = results.paths[pathIndex];
      const points: THREE.Vector3[] = [];
      
      // Normalize path data for 3D space
      const maxValue = Math.max(...results.finalValues);
      const minValue = Math.min(...results.finalValues);
      const valueRange = maxValue - minValue;
      
      path.forEach((value, timeIndex) => {
        const x = (timeIndex / path.length) * 20 - 10; // Time axis
        const y = ((value - minValue) / valueRange) * 10 - 5; // Value axis (normalized)
        const z = (Math.random() - 0.5) * 2; // Add some depth variation
        points.push(new THREE.Vector3(x, y, z));
      });

      // Create path geometry
      const geometry = new THREE.BufferGeometry().setFromPoints(points);
      
      // Color based on final performance
      const finalValue = path[path.length - 1];
      const performance = (finalValue - path[0]) / path[0];
      const color = performance > 0 
        ? new THREE.Color().setHSL(0.3, 0.7, 0.5) // Green for gains
        : new THREE.Color().setHSL(0, 0.7, 0.5);   // Red for losses
      
      const material = new THREE.LineBasicMaterial({ 
        color,
        opacity: 0.6,
        transparent: true,
        linewidth: 1
      });
      
      const line = new THREE.Line(geometry, material);
      scene.add(line);
    }

    // Add confidence interval surfaces
    if (results.confidenceIntervals) {
      const intervals = ['10%', '25%', '50%', '75%', '90%'];
      intervals.forEach((interval, index) => {
        const values = results.confidenceIntervals[interval as keyof typeof results.confidenceIntervals];
        const geometry = new THREE.BufferGeometry();
        const points: number[] = [];
        
        values.forEach((value, timeIndex) => {
          const x = (timeIndex / values.length) * 20 - 10;
          const y = ((value - Math.min(...results.finalValues)) / 
                   (Math.max(...results.finalValues) - Math.min(...results.finalValues))) * 10 - 5;
          const z = index * 0.5 - 1;
          points.push(x, y, z);
        });
        
        geometry.setAttribute('position', new THREE.Float32BufferAttribute(points, 3));
        
        const material = new THREE.LineBasicMaterial({
          color: new THREE.Color().setHSL(0.6, 0.5, 0.7 - index * 0.1),
          opacity: 0.8,
          transparent: true
        });
        
        const line = new THREE.Line(geometry, material);
        scene.add(line);
      });
    }

    // Position camera
    camera.position.set(15, 5, 15);
    camera.lookAt(0, 0, 0);

    // Animation loop
    const animate = () => {
      animationRef.current = requestAnimationFrame(animate);
      
      // Rotate the scene slowly
      scene.rotation.y += 0.005;
      
      renderer.render(scene, camera);
    };
    animate();

    // Handle resize
    const handleResize = () => {
      if (!mountRef.current) return;
      const newWidth = mountRef.current.clientWidth;
      camera.aspect = newWidth / height;
      camera.updateProjectionMatrix();
      renderer.setSize(newWidth, height);
    };

    window.addEventListener('resize', handleResize);

    return () => {
      if (rendererRef.current) {
        rendererRef.current.dispose();
      }
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
      window.removeEventListener('resize', handleResize);
    };
  }, [results]);

  return (
    <div 
      ref={mountRef} 
      className="w-full h-96 border rounded-lg bg-gray-50" 
      id="three-js-container"
    />
  );
};

export default ThreeVisualization;