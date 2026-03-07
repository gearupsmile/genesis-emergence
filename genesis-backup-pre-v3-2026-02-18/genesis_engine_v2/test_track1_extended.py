"""
Track 1: Extended Validation Test (1,000 generations)

Quick validation to confirm gatekeeper stability before Track 2.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from engine.genesis_engine import GenesisEngine


def run_extended_validation():
    """Run 1,000-generation validation."""
    print("=" * 70)
    print("TRACK 1: EXTENDED VALIDATION (1,000 GENERATIONS)")
    print("=" * 70)
    print()
    
    engine = GenesisEngine(
        population_size=100,
        mutation_rate=0.3,
        simulation_steps=5
    )
    
    print(f"Running 1,000 generations...")
    print()
    
    for gen in range(1000):
        engine.run_cycle()
        
        if (gen + 1) % 250 == 0:
            stats = engine.physics_gatekeeper.logger.get_summary_statistics()
            print(f"  Gen {gen+1}: Pop={len(engine.population)}, "
                  f"Rejection={stats['overall_rejection_rate']:.2%}, "
                  f"Violations={engine.physics_gatekeeper.total_violations}")
    
    print()
    print("=" * 70)
    print("FINAL RESULTS")
    print("=" * 70)
    
    stats = engine.physics_gatekeeper.logger.get_summary_statistics()
    
    print(f"\nTotal checks: {stats['total_parent_checks'] + stats['total_offspring_checks']}")
    print(f"Total rejections: {stats['total_parent_rejections'] + stats['total_offspring_rejections']}")
    print(f"Overall rejection rate: {stats['overall_rejection_rate']:.2%}")
    print(f"Violations: {engine.physics_gatekeeper.total_violations}")
    print(f"Final population: {len(engine.population)}")
    print()
    
    if engine.physics_gatekeeper.total_violations == 0:
        print("[SUCCESS] Zero violations maintained!")
    else:
        print(f"[FAILURE] {engine.physics_gatekeeper.total_violations} violations detected!")
    
    print("=" * 70)
    
    return engine.physics_gatekeeper.total_violations == 0


if __name__ == '__main__':
    try:
        success = run_extended_validation()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
