"""
Feature 1 Verification Script
"""
import sys
import os
import numpy as np
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from engine.genesis_engine import GenesisEngine

def verify_feature_1():
    print("Initializing Engine...")
    engine = GenesisEngine(population_size=10, mutation_rate=0.1)
    
    # Verify Substrate exists
    if not hasattr(engine, 'substrate'):
        print("FAIL: engine.substrate missing")
        return
    print("PASS: engine.substrate exists")
    
    # Check initial S state
    if np.max(engine.substrate.S) != 0:
        print(f"FAIL: Initial S not zero (max={np.max(engine.substrate.S)})")
    
    print("\nRunning simulation loop manually (10 steps)...")
    
    initial_energy = [a.energy for a in engine.population]
    
    # Manually run loop to avoid reproduction replacing (and resetting) agents
    for _ in range(engine.simulation_steps):
        engine.substrate.diffuse_secretion()
        for agent in engine.population:
            if hasattr(agent, 'step'):
                agent.step(engine.substrate)
            
    # Check if S field has activity
    max_S = np.max(engine.substrate.S)
    print(f"Max S after 1 cycle: {max_S}")
    
    if max_S <= 0:
        print("FAIL: No secretion detected in S field")
    else:
        print("PASS: Secretion detected")
        
    # Check diffusion (non-zero neighbors)
    # Find a peak
    py, px = np.unravel_index(np.argmax(engine.substrate.S), engine.substrate.S.shape)
    print(f"Peak at ({px}, {py}) value {engine.substrate.S[py, px]}")
    
    # Check neighbors
    neighbors = []
    h, w = engine.substrate.S.shape
    for dy in [-2, -1, 0, 1, 2]:
        for dx in [-2, -1, 0, 1, 2]:
            ny, nx = (py+dy)%h, (px+dx)%w
            neighbors.append(engine.substrate.S[ny, nx])
    
    print(f"Neighborhood values: {neighbors}")
    if sum(n > 0 for n in neighbors) > 1:
        print("PASS: Diffusion detected (multiple non-zero pixels)")
    else:
        print("WARNING: Diffusion might be too slow or only center pixel active")

    # Check energy deduction
    final_energy = [a.energy for a in engine.population]
    energy_loss = [i - f for i, f in zip(initial_energy, final_energy)]
    print(f"Energy losses: {energy_loss}")
    if any(loss > 0 for loss in energy_loss):
        print("PASS: Metabolic cost deducted")
    else:
        print("FAIL: No energy deducted (agents didn't secrete?)")

if __name__ == "__main__":
    verify_feature_1()
