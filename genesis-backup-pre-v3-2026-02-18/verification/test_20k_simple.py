"""
Simple 20k Bloat Validation Test (No Constraint Checker)

Tests the bloat fix directly without pre-flight checks.
"""

import sys
from pathlib import Path
import time

# Add genesis_engine_v2 to path
sys.path.insert(0, str(Path(__file__).parent / 'genesis_engine_v2'))

from engine.genesis_engine import GenesisEngine


def run_simple_20k_test():
    """Run 20,000-generation test."""
    print("=" * 70)
    print("SIMPLE 20K BLOAT VALIDATION")
    print("=" * 70)
    print()
    
    total_gens = 20000
    population_size = 50
    mutation_rate = 0.3
    
    print(f"Configuration:")
    print(f"  Generations: {total_gens:,}")
    print(f"  Population: {population_size}")
    print(f"  Bloat circuit breaker: GAC > 40")
    print()
    print(f"Bloat Control (NEW):")
    print(f"  Hard limit: MAX_GENOME_SIZE = 100")
    print(f"  Cost coefficient: 0.02 (was 0.005 - 4x stronger)")
    print(f"  Cost exponent: 1.8 (was 1.5 - more aggressive)")
    print()
    
    engine = GenesisEngine(
        population_size=population_size,
        mutation_rate=mutation_rate,
        simulation_steps=10
    )
    
    print(f"{'Gen':>6} {'Pop':>5} {'GAC_mean':>9} {'GAC_max':>8} {'Cost_mean':>10} {'Gen/s':>7} {'Status':>12}")
    print("-" * 75)
    
    start_time = time.time()
    last_report_time = start_time
    
    gac_history = []
    
    for gen in range(total_gens):
        engine.run_cycle()
        
        genome_lengths = [agent.genome.get_length() for agent in engine.population]
        metabolic_costs = [agent.genome.metabolic_cost for agent in engine.population]
        
        gac_mean = sum(genome_lengths) / len(genome_lengths)
        gac_max = max(genome_lengths)
        cost_mean = sum(metabolic_costs) / len(metabolic_costs)
        
        gac_history.append(gac_mean)
        
        # BLOAT CIRCUIT BREAKER
        if gac_mean > 40:
            elapsed = time.time() - start_time
            gens_per_sec = (gen + 1) / elapsed
            
            print(f"{gen+1:6d} {len(engine.population):5d} "
                  f"{gac_mean:9.1f} {gac_max:8d} {cost_mean:10.4f} {gens_per_sec:7.1f} {'BLOAT!':>12}")
            print()
            print(f"[FAIL] GAC exceeded 40 at generation {gen+1}")
            print(f"Current GAC: {gac_mean:.1f}, Max: {gac_max}")
            return False
        
        if (gen + 1) % 1000 == 0:
            current_time = time.time()
            interval_time = current_time - last_report_time
            gens_per_sec = 1000 / interval_time if interval_time > 0 else 0
            last_report_time = current_time
            
            status = "OK" if gac_mean < 30 else ("WARNING" if gac_mean < 35 else "CRITICAL")
            
            print(f"{gen+1:6d} {len(engine.population):5d} "
                  f"{gac_mean:9.1f} {gac_max:8d} {cost_mean:10.4f} {gens_per_sec:7.1f} {status:>12}")
    
    total_time = time.time() - start_time
    gens_per_sec = total_gens / total_time
    
    print("-" * 75)
    print(f"Completed {total_gens:,} gens in {total_time:.1f}s ({gens_per_sec:.1f} gen/s)")
    print()
    
    # Analysis
    final_gac = gac_history[-1]
    initial_gac = gac_history[0]
    
    n = len(gac_history)
    x_mean = n / 2
    y_mean = sum(gac_history) / n
    numerator = sum((i - x_mean) * (gac - y_mean) for i, gac in enumerate(gac_history))
    denominator = sum((i - x_mean) ** 2 for i in range(n))
    slope = numerator / denominator if denominator > 0 else 0
    
    print("ANALYSIS:")
    print(f"  Initial GAC: {initial_gac:.1f}")
    print(f"  Final GAC: {final_gac:.1f}")
    print(f"  Change: {final_gac - initial_gac:+.1f}")
    print(f"  Trend slope: {slope:.6f} genes/gen")
    print()
    
    success = final_gac <= 40 and slope <= 0.001
    
    if success:
        print("[SUCCESS] Bloat control working - ready for 200k!")
    else:
        print("[FAIL] Bloat control insufficient")
    
    return success


if __name__ == '__main__':
    success = run_simple_20k_test()
    sys.exit(0 if success else 1)
