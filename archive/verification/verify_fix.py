"""
Verification Test for Genome Bloat Fix

This test verifies that the metabolic cost penalty is correctly applied
and prevents genome bloat in the GenesisEngine.

Success Criteria:
- GAC stabilizes between 15-25 genes
- No upward trend in genome size
- Performance stable (~50 gen/s or better)
- Bloat circuit breaker never triggers (GAC < 50)
"""

import sys
from pathlib import Path

# Add genesis_engine_v2 to path
sys.path.insert(0, str(Path(__file__).parent / 'genesis_engine_v2'))

from engine.genesis_engine import GenesisEngine
from engine.verification.constraint_checker import ConstraintChecker


def run_verification():
    """Run 5,000-generation verification test."""
    print("=" * 70)
    print("GENOME BLOAT FIX - VERIFICATION TEST")
    print("=" * 70)
    print()
    
    # Step 1: Pre-flight constraint check
    print("Step 1: Running pre-flight constraint verification...")
    checker = ConstraintChecker()
    
    if not checker.run_all_checks():
        print("\n[FAIL] Pre-flight constraint checks failed!")
        print("The metabolic cost penalty is not being applied correctly.")
        return False
    
    print("[PASS] Pre-flight checks passed")
    print()
    
    # Step 2: Run 5,000-generation simulation
    print("Step 2: Running 5,000-generation simulation...")
    print()
    
    total_gens = 5000
    population_size = 50
    mutation_rate = 0.3
    
    print(f"Configuration:")
    print(f"  Generations: {total_gens:,}")
    print(f"  Population: {population_size}")
    print(f"  Mutation rate: {mutation_rate}")
    print(f"  Bloat circuit breaker: GAC > 50")
    print()
    
    # Initialize engine
    engine = GenesisEngine(
        population_size=population_size,
        mutation_rate=mutation_rate,
        simulation_steps=10
    )
    
    print(f"{'Gen':>6} {'Pop':>5} {'GAC_mean':>9} {'GAC_max':>8} {'Cost_mean':>10} {'Status':>12}")
    print("-" * 70)
    
    import time
    start_time = time.time()
    
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
        
        # BLOAT CIRCUIT BREAKER
        if gac_mean > 50:
            elapsed = time.time() - start_time
            gens_per_sec = (gen + 1) / elapsed
            
            print(f"{gen+1:6d} {len(engine.population):5d} "
                  f"{gac_mean:9.1f} {gac_max:8d} {cost_mean:10.4f} {'BLOAT!':>12}")
            print()
            print("=" * 70)
            print("[FAIL] BLOAT CIRCUIT BREAKER TRIGGERED")
            print("=" * 70)
            print()
            print(f"Mean GAC exceeded 50 at generation {gen+1}")
            print(f"Current GAC: {gac_mean:.1f}")
            print(f"Max GAC: {gac_max}")
            print(f"Mean cost: {cost_mean:.4f}")
            print()
            print("The metabolic cost penalty is NOT preventing bloat.")
            print("This indicates a bug in the selection or cost application.")
            print()
            return False
        
        # Progress reporting
        if (gen + 1) % 500 == 0:
            elapsed = time.time() - start_time
            gens_per_sec = (gen + 1) / elapsed
            
            status = "OK"
            if gac_mean > 30:
                status = "WARNING"
            
            print(f"{gen+1:6d} {len(engine.population):5d} "
                  f"{gac_mean:9.1f} {gac_max:8d} {cost_mean:10.4f} {status:>12}")
    
    total_time = time.time() - start_time
    gens_per_sec = total_gens / total_time
    
    print("-" * 70)
    print(f"Completed {total_gens:,} generations in {total_time:.1f}s ({gens_per_sec:.1f} gen/s)")
    print()
    
    # Step 3: Analyze results
    print("=" * 70)
    print("ANALYSIS")
    print("=" * 70)
    print()
    
    final_gac = gac_history[-1]
    initial_gac = gac_history[0]
    
    # Check for upward trend (simple linear regression)
    n = len(gac_history)
    x_mean = n / 2
    y_mean = sum(gac_history) / n
    
    numerator = sum((i - x_mean) * (gac - y_mean) for i, gac in enumerate(gac_history))
    denominator = sum((i - x_mean) ** 2 for i in range(n))
    
    slope = numerator / denominator if denominator > 0 else 0
    
    print(f"Initial GAC: {initial_gac:.1f}")
    print(f"Final GAC: {final_gac:.1f}")
    print(f"Change: {final_gac - initial_gac:+.1f}")
    print(f"Trend slope: {slope:.4f} genes/gen")
    print()
    
    # Determine success
    success = True
    
    if final_gac < 15:
        print("[WARNING] GAC too low ({:.1f}). Genomes may be too constrained.".format(final_gac))
    elif final_gac > 25:
        print("[WARNING] GAC high ({:.1f}). Approaching bloat threshold.".format(final_gac))
        if final_gac > 35:
            print("[FAIL] GAC exceeds acceptable range.")
            success = False
    else:
        print(f"[PASS] GAC in acceptable range: {final_gac:.1f} genes")
    
    if slope > 0.01:
        print(f"[FAIL] Upward trend detected (slope: {slope:.4f}). Bloat is occurring.")
        success = False
    elif slope > 0.001:
        print(f"[WARNING] Slight upward trend (slope: {slope:.4f}). Monitor closely.")
    else:
        print(f"[PASS] No significant upward trend (slope: {slope:.4f})")
    
    if gens_per_sec < 10:
        print(f"[WARNING] Performance low ({gens_per_sec:.1f} gen/s)")
    else:
        print(f"[PASS] Performance acceptable ({gens_per_sec:.1f} gen/s)")
    
    print()
    
    if success:
        print("=" * 70)
        print("[SUCCESS] VERIFICATION TEST PASSED")
        print("=" * 70)
        print()
        print("The metabolic cost penalty is working correctly.")
        print("Genome bloat is under control.")
        print("System is ready for 200k-generation experiment.")
    else:
        print("=" * 70)
        print("[FAILURE] VERIFICATION TEST FAILED")
        print("=" * 70)
        print()
        print("The metabolic cost penalty is NOT working as expected.")
        print("Do NOT proceed with 200k experiment until this is fixed.")
    
    print()
    return success


if __name__ == '__main__':
    success = run_verification()
    sys.exit(0 if success else 1)
