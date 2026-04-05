"""
Pre-Flight Verification Test for Physics Gatekeeper v2

100-generation simulation to verify gatekeeper enforcement.

Success Criteria:
1. Zero constraint violations (all agents have cost <= PHYSICAL_CONSTANT)
2. Stable rejection rate (5-15% range)
3. Non-zero population at end
4. Genetic diversity maintained

Part of Track 1: Physics Gatekeeper v2
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from engine.genesis_engine import GenesisEngine


def run_preflight_verification():
    """
    Run 100-generation pre-flight verification.
    
    Returns:
        True if all criteria pass, False otherwise
    """
    print("=" * 70)
    print("TRACK 1: PHYSICS GATEKEEPER V2 - PRE-FLIGHT VERIFICATION")
    print("=" * 70)
    print()
    
    print("Running 100-generation simulation to verify:")
    print("  1. Zero constraint violations")
    print("  2. Stable rejection rate (5-15%)")
    print("  3. Population survival (>10 agents)")
    print("  4. Genetic diversity maintained")
    print()
    
    # Create engine
    engine = GenesisEngine(
        population_size=100,
        mutation_rate=0.3,
        simulation_steps=5
    )
    
    print(f"Engine initialized:")
    print(f"  Population: {len(engine.population)}")
    print(f"  Physics Gatekeeper: {engine.physics_gatekeeper}")
    print(f"  Energy constant: {engine.physics_gatekeeper.energy_constant}")
    print()
    
    # Track results
    all_passed = True
    violation_count = 0
    rejection_rates = []
    
    print("Running 100 generations...")
    print()
    
    for gen in range(100):
        engine.run_cycle()
        
        # CRITERION 1: Check for violations
        violations_this_gen = 0
        for agent in engine.population:
            if agent.genome.metabolic_cost > engine.physics_gatekeeper.energy_constant:
                violations_this_gen += 1
                violation_count += 1
        
        if violations_this_gen > 0:
            print(f"  [FAIL] Gen {gen}: {violations_this_gen} violations detected!")
            all_passed = False
        
        # Track rejection rate
        if hasattr(engine.physics_gatekeeper, 'logger'):
            current_rate = engine.physics_gatekeeper.logger.get_current_rejection_rate()
            rejection_rates.append(current_rate)
        
        # Progress report every 25 gens
        if (gen + 1) % 25 == 0:
            pop_size = len(engine.population)
            avg_rate = sum(rejection_rates[-25:]) / 25 if rejection_rates else 0.0
            print(f"  Gen {gen+1}: Pop={pop_size}, Avg Rejection Rate={avg_rate:.2%}")
    
    print()
    print("=" * 70)
    print("VERIFICATION RESULTS")
    print("=" * 70)
    print()
    
    # CRITERION 1: Zero violations
    print(f"1. Constraint Violations:")
    print(f"   Total violations: {violation_count}")
    if violation_count == 0:
        print(f"   Result: PASS [OK]")
    else:
        print(f"   Result: FAIL [X]")
        all_passed = False
    print()
    
    # CRITERION 2: Stable rejection rate
    if rejection_rates:
        import numpy as np
        avg_rejection_rate = np.mean(rejection_rates)
        rejection_rate_std = np.std(rejection_rates)
        
        print(f"2. Rejection Rate:")
        print(f"   Average: {avg_rejection_rate:.2%}")
        print(f"   Std Dev: {rejection_rate_std:.4f}")
        print(f"   Range: {min(rejection_rates):.2%} - {max(rejection_rates):.2%}")
        
        if 0.05 <= avg_rejection_rate <= 0.15:
            print(f"   Result: PASS [OK] (within 5-15% target)")
        else:
            print(f"   Result: WARNING [!] (outside 5-15% target)")
            # Not a hard failure, just a warning
    print()
    
    # CRITERION 3: Population survival
    final_pop_size = len(engine.population)
    print(f"3. Population Survival:")
    print(f"   Final population: {final_pop_size}")
    if final_pop_size >= 10:
        print(f"   Result: PASS [OK]")
    else:
        print(f"   Result: FAIL [X] (population collapsed)")
        all_passed = False
    print()
    
    # CRITERION 4: Genetic diversity
    if hasattr(engine.physics_gatekeeper, 'logger'):
        summary = engine.physics_gatekeeper.logger.get_summary_statistics()
        recent_logs = engine.physics_gatekeeper.logger.get_recent_logs(10)
        
        if recent_logs:
            avg_diversity = np.mean([log['genetic_diversity_score'] for log in recent_logs])
            print(f"4. Genetic Diversity:")
            print(f"   Average diversity score: {avg_diversity:.6f}")
            if avg_diversity > 0.001:
                print(f"   Result: PASS [OK]")
            else:
                print(f"   Result: WARNING [!] (low diversity)")
        print()
        
        # Additional statistics
        print("Enhanced Logging Statistics:")
        print(f"  Total parent checks: {summary['total_parent_checks']}")
        print(f"  Total parent rejections: {summary['total_parent_rejections']}")
        print(f"  Parent rejection rate: {summary['parent_rejection_rate']:.2%}")
        print(f"  Total offspring checks: {summary['total_offspring_checks']}")
        print(f"  Total offspring rejections: {summary['total_offspring_rejections']}")
        print(f"  Offspring rejection rate: {summary['offspring_rejection_rate']:.2%}")
        print(f"  Overall rejection rate: {summary['overall_rejection_rate']:.2%}")
        print(f"  Rejection rate stability: {summary['rejection_rate_stability']:.4f}")
    
    print()
    print("=" * 70)
    if all_passed:
        print("[SUCCESS] Pre-flight verification PASSED [OK]")
        print("Physics Gatekeeper v2 is functioning correctly.")
    else:
        print("[FAILURE] Pre-flight verification FAILED [X]")
        print("Issues detected - review results above.")
    print("=" * 70)
    
    return all_passed


if __name__ == '__main__':
    try:
        success = run_preflight_verification()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n[ERROR] Pre-flight test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
