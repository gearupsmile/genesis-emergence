"""
Phase 1 Validation: Gatekeeper Zero-Violation Test

HARD assertion test - crashes if ANY violation occurs.
Success = 0 violations across 100 generations.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from engine.genesis_engine_minimal import GenesisEngineMinimal


def test_gatekeeper_zero_violations():
    """
    100-generation test with HARD assertion on zero violations.
    
    This test enforces the fundamental law: Physics violations MUST be zero.
    If this test fails, the gatekeeper is broken and nothing else matters.
    """
    print("=" * 70)
    print("PHASE 1 VALIDATION: GATEKEEPER ZERO-VIOLATION TEST")
    print("=" * 70)
    print()
    print("Testing: Physics Gatekeeper must achieve ZERO violations")
    print("Duration: 100 generations")
    print("Failure mode: CRASH on first violation")
    print()
    
    engine = GenesisEngineMinimal(population_size=100, mutation_rate=0.3)
    
    print(f"Initial population: {len(engine.population)}")
    print(f"Energy constant: {engine.physics_gatekeeper.energy_constant}")
    print()
    print("Running 100 generations with hard assertions...")
    print()
    
    for gen in range(100):
        engine.run_cycle()
        
        # HARD ASSERTION 1: Total violations must be zero
        violations = engine.physics_gatekeeper.total_violations
        assert violations == 0, \
            f"GATEKEEPER FAILURE at Gen {gen}: {violations} violations detected!"
        
        # HARD ASSERTION 2: Manually verify all agents
        for agent in engine.population:
            metabolic_cost = agent.genome.metabolic_cost
            assert metabolic_cost <= 0.5, \
                f"AGENT VIOLATION at Gen {gen}: Agent {agent.id[:8]} has cost {metabolic_cost:.4f} > 0.5"
        
        # Report every 25 generations
        if (gen + 1) % 25 == 0:
            stats = engine.get_statistics()
            total_checks = (engine.physics_gatekeeper.logger.total_parent_checks + 
                          engine.physics_gatekeeper.logger.total_offspring_checks)
            print(f"  Gen {gen+1}: {total_checks} checks, {violations} violations, "
                  f"Pop={stats['population_size']}")
    
    print()
    print("=" * 70)
    print("PHASE 1 VALIDATION: PASSED")
    print("=" * 70)
    print()
    
    # Final statistics
    final_stats = engine.get_statistics()
    physics_stats = final_stats['physics_stats']
    total_checks = physics_stats['total_parent_checks'] + physics_stats['total_offspring_checks']
    
    print(f"Final Results:")
    print(f"  Total checks: {total_checks}")
    print(f"  Violations: {engine.physics_gatekeeper.total_violations}")
    print(f"  Population: {final_stats['population_size']}")
    print(f"  Foragers: {final_stats['forager_count']}")
    print(f"  Predators: {final_stats['predator_count']}")
    print()
    print("[SUCCESS] Physics Gatekeeper achieving ZERO violations")
    print("Universe's laws are now inviolable.")
    print()
    print("Ready for Phase 2: Frequency-Dependent Selection")
    
    return True


if __name__ == '__main__':
    try:
        success = test_gatekeeper_zero_violations()
        sys.exit(0 if success else 1)
    except AssertionError as e:
        print(f"\n[FAILURE] {e}")
        print("\nGatekeeper is broken. Fix required before proceeding.")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
