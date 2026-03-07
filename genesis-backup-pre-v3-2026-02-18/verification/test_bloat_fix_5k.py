"""
Direct 5k Bloat Test - No Dependencies

Tests the bloat fix directly with the updated parameters.
"""

import sys
from pathlib import Path
import time

sys.path.insert(0, str(Path(__file__).parent / 'genesis_engine_v2'))

from engine.genesis_engine import GenesisEngine


print("=" * 70)
print("5K BLOAT FIX VALIDATION")
print("=" * 70)
print()

print("Bloat Control Parameters:")
print("  MAX_GENOME_SIZE: 100 (hard limit)")
print("  COST_COEFFICIENT: 0.02 (was 0.005 - 4x stronger)")
print("  COST_EXPONENT: 1.8 (was 1.5 - more aggressive)")
print()

total_gens = 5000
engine = GenesisEngine(population_size=50, mutation_rate=0.3, simulation_steps=10)

print(f"{'Gen':>6} {'Pop':>5} {'GAC':>7} {'Max':>5} {'Cost':>8} {'Gen/s':>7}")
print("-" * 50)

start_time = time.time()
gac_history = []

for gen in range(total_gens):
    engine.run_cycle()
    
    lengths = [a.genome.get_length() for a in engine.population]
    costs = [a.genome.metabolic_cost for a in engine.population]
    
    gac_mean = sum(lengths) / len(lengths)
    gac_max = max(lengths)
    cost_mean = sum(costs) / len(costs)
    
    gac_history.append(gac_mean)
    
    if (gen + 1) % 500 == 0:
        elapsed = time.time() - start_time
        gps = (gen + 1) / elapsed
        print(f"{gen+1:6d} {len(engine.population):5d} {gac_mean:7.1f} {gac_max:5d} {cost_mean:8.4f} {gps:7.1f}")

total_time = time.time() - start_time
print("-" * 50)
print(f"Time: {total_time:.1f}s ({total_gens/total_time:.1f} gen/s)")
print()

# Analysis
final_gac = gac_history[-1]
initial_gac = gac_history[0]
n = len(gac_history)
x_mean = n / 2
y_mean = sum(gac_history) / n
slope = sum((i - x_mean) * (gac - y_mean) for i, gac in enumerate(gac_history)) / sum((i - x_mean) ** 2 for i in range(n))

print("RESULTS:")
print(f"  Initial GAC: {initial_gac:.1f}")
print(f"  Final GAC: {final_gac:.1f}")
print(f"  Trend: {slope:.6f} genes/gen")
print()

if final_gac < 30 and slope < 0.002:
    print("[SUCCESS] Bloat controlled - ready for 200k!")
    sys.exit(0)
else:
    print(f"[WARNING] GAC={final_gac:.1f}, slope={slope:.6f}")
    sys.exit(1)
