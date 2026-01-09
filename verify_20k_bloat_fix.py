"""
20k Generation Bloat Validation Test

This test validates that the multi-layered bloat control system prevents
genome bloat in longer runs (20k generations).

Success Criteria:
- GAC stays < 40 for entire run
- No exponential growth trend
- Performance stable (>30 gen/s)
- No bloat circuit breaker triggers
"""

import sys
from pathlib import Path
import time

# Add genesis_engine_v2 to path
sys.path.insert(0, str(Path(__file__).parent / 'genesis_engine_v2'))

from engine.genesis_engine import GenesisEngine
from engine.verification.constraint_checker import ConstraintChecker


def run_20k_validation():
    """Run 20,000-generation validation test."""
    print("=" * 70)
    print("20K BLOAT VALIDATION TEST")
    print("=" * 70)
    print()
    
    # Step 1: Pre-flight constraint check
    print("Step 1: Running pre-flight constraint verification...")
    checker = ConstraintChecker()
    
    if not checker.run_all_checks():
        print("\n[FAIL] Pre-flight constraint checks failed!")
        return False
    
    print("[PASS] Pre-flight checks passed")
    print()
    
    # Step 2: Run 20,000-generation simulation
    print("Step 2: Running 20,000-generation simulation...")
    print()
    
    total_gens = 20000
    population_size = 50
    mutation_rate = 0.3
    
    print(f"Configuration:")
    print(f"  Generations: {total_gens:,}")
    print(f"  Population: {population_size}")
    print(f"  Mutation rate: {mutation_rate}")
    print(f"  Bloat circuit breaker: GAC > 40")
    print()
    print(f"Bloat Control:")
    print(f"  Hard limit: MAX_GENOME_SIZE = 100")
    print(f"  Cost coefficient: 0.02 (4x stronger)")
    print(f"  Cost exponent: 1.8 (more aggressive)")
    print()
    
    # Initialize engine
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
        # Run one generation
        engine.run_cycle()
        
        # Calculate GAC statistics
        genome_lengths = [agent.genome.get_length() for agent in engine.population]
        metabolic_costs = [agent.genome.metabolic_cost for agent in engine.population]
        
        gac_mean = sum(genome_lengths) / len(genome_lengths)
        gac_max = max(genome_lengths)
        cost_mean = sum(metabolic_costs) / len(metabolic_costs)
        
        gac_history.append(gac_mean)
        
        # BLOAT CIRCUIT BREAKER (tighter threshold for 20k test)
        if gac_mean > 40:
            elapsed = time.time() - start_time
            gens_per_sec = (gen + 1) / elapsed
            
            print(f"{gen+1:6d} {len(engine.population):5d} "
                  f"{gac_mean:9.1f} {gac_max:8d} {cost_mean:10.4f} {gens_per_sec:7.1f} {'BLOAT!':>12}")
            print()
            print("=" * 70)
            print("[FAIL] BLOAT CIRCUIT BREAKER TRIGGERED")
            print("=" * 70)
            print()
            print(f"Mean GAC exceeded 40 at generation {gen+1}")
            print(f"Current GAC: {gac_mean:.1f}")
            print(f"Max GAC: {gac_max}")
            print()
            print("The bloat control system is INSUFFICIENT.")
            print()
            return False
        
        # Progress reporting
        if (gen + 1) % 1000 == 0:
            current_time = time.time()
            interval_time = current_time - last_report_time
            gens_per_sec = 1000 / interval_time if interval_time > 0 else 0
            last_report_time = current_time
            
            status = "OK"
            if gac_mean > 30:
                status = "WARNING"
            elif gac_mean > 35:
                status = "CRITICAL"
            
            print(f"{gen+1:6d} {len(engine.population):5d} "
                  f"{gac_mean:9.1f} {gac_max:8d} {cost_mean:10.4f} {gens_per_sec:7.1f} {status:>12}")
    
    total_time = time.time() - start_time
    gens_per_sec = total_gens / total_time
    
    print("-" * 75)
    print(f"Completed {total_gens:,} generations in {total_time:.1f}s ({gens_per_sec:.1f} gen/s)")
    print()
    
    # Step 3: Analyze results
    print("=" * 70)
    print("ANALYSIS")
    print("=" * 70)
    print()
    
    final_gac = gac_history[-1]
    initial_gac = gac_history[0]
    
    # Check for upward trend
    n = len(gac_history)
    x_mean = n / 2
    y_mean = sum(gac_history) / n
    
    numerator = sum((i - x_mean) * (gac - y_mean) for i, gac in enumerate(gac_history))
    denominator = sum((i - x_mean) ** 2 for i in range(n))
    
    slope = numerator / denominator if denominator > 0 else 0
    
    print(f"Initial GAC: {initial_gac:.1f}")
    print(f"Final GAC: {final_gac:.1f}")
    print(f"Change: {final_gac - initial_gac:+.1f}")
    print(f"Trend slope: {slope:.6f} genes/gen")
    print()
    
    # Determine success
    success = True
    
    if final_gac > 40:
        print(f"[FAIL] Final GAC ({final_gac:.1f}) exceeds threshold (40)")
        success = False
    elif final_gac > 35:
        print(f"[WARNING] Final GAC ({final_gac:.1f}) approaching threshold")
    else:
        print(f"[PASS] Final GAC in acceptable range: {final_gac:.1f} genes")
    
    if slope > 0.001:
        print(f"[FAIL] Upward trend detected (slope: {slope:.6f}). Bloat is occurring.")
        success = False
    elif slope > 0.0005:
        print(f"[WARNING] Slight upward trend (slope: {slope:.6f}). Monitor closely.")
    else:
        print(f"[PASS] No significant upward trend (slope: {slope:.6f})")
    
    if gens_per_sec < 30:
        print(f"[WARNING] Performance below target ({gens_per_sec:.1f} gen/s < 30 gen/s)")
    else:
        print(f"[PASS] Performance acceptable ({gens_per_sec:.1f} gen/s)")
    
    print()
    
    if success:
        print("=" * 70)
        print("[SUCCESS] 20K VALIDATION TEST PASSED")
        print("=" * 70)
        print()
        print("The multi-layered bloat control system is working correctly.")
        print("Genome bloat is under control for long runs.")
        print("System is ready for 200k-generation experiment.")
    else:
        print("=" * 70)
        print("[FAILURE] 20K VALIDATION TEST FAILED")
        print("=" * 70)
        print()
        print("The bloat control system is NOT sufficient for long runs.")
        print("Do NOT proceed with 200k experiment until this is fixed.")
    
    print()
    return success


if __name__ == '__main__':
    success = run_20k_validation()
    sys.exit(0 if success else 1)
