"""
Phase 1 Integration: Smoke Test (100 generations)

Quick validation before 1,000-gen test to prevent compute waste.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from engine.genesis_engine import GenesisEngine
from engine.carp.species import Species


def run_smoke_test():
    """
    100-generation smoke test with critical assertions.
    
    Expert warning: "Validate integration before long runs."
    """
    print("=" * 70)
    print("PHASE 1: INTEGRATION SMOKE TEST (100 GENERATIONS)")
    print("=" * 70)
    print()
    
    print("Initializing GenesisEngine with all three tracks...")
    engine = GenesisEngine(population_size=100, mutation_rate=0.3)
    
    print(f"  Population: {len(engine.population)}")
    print(f"  Physics Gatekeeper: {engine.physics_gatekeeper}")
    print(f"  Interaction Handler: {engine.interaction_handler}")
    print(f"  Species Assigner: {engine.species_assigner}")
    print()
    
    print("Running 100 generations with critical checks...")
    print()
    
    for gen in range(100):
        engine.run_cycle()
        
        # CRITICAL CHECK 1: Physics law integrity
        violations = engine.physics_gatekeeper.total_violations
        assert violations == 0, f"FAIL: Physics law broken! {violations} violations at gen {gen}"
        
        # CRITICAL CHECK 2: Forager population stability
        foragers = len([a for a in engine.population 
                       if hasattr(a, 'species') and a.species == Species.FORAGER])
        assert foragers > 20, f"FAIL: Foragers collapsing! Only {foragers} at gen {gen}"
        
        # CRITICAL CHECK 3: Predator population stability
        predators = len([a for a in engine.population 
                        if hasattr(a, 'species') and a.species == Species.PREDATOR])
        assert predators > 10, f"FAIL: Predators collapsing! Only {predators} at gen {gen}"
        
        # CRITICAL CHECK 4: Population exists
        assert len(engine.population) > 0, f"FAIL: Population extinct at gen {gen}"
        
        # Log every 25 generations
        if (gen + 1) % 25 == 0:
            stats = engine.physics_gatekeeper.logger.get_summary_statistics()
            capture_stats = engine.interaction_handler.get_statistics()
            
            print(f"  Gen {gen+1}:")
            print(f"    Population: {len(engine.population)}")
            print(f"    Foragers: {foragers}, Predators: {predators}")
            print(f"    Violations: {violations}")
            print(f"    Captures: {capture_stats['successful_captures']}")
            print(f"    Rejection rate: {stats['overall_rejection_rate']:.2%}")
    
    print()
    print("=" * 70)
    print("SMOKE TEST RESULTS")
    print("=" * 70)
    print()
    
    # Final statistics
    final_stats = engine.physics_gatekeeper.logger.get_summary_statistics()
    capture_stats = engine.interaction_handler.get_statistics()
    
    foragers = len([a for a in engine.population 
                   if hasattr(a, 'species') and a.species == Species.FORAGER])
    predators = len([a for a in engine.population 
                    if hasattr(a, 'species') and a.species == Species.PREDATOR])
    
    print(f"Final Population: {len(engine.population)}")
    print(f"  Foragers: {foragers}")
    print(f"  Predators: {predators}")
    print()
    
    print(f"Physics Enforcement:")
    print(f"  Total checks: {final_stats['total_parent_checks'] + final_stats['total_offspring_checks']}")
    print(f"  Violations: {engine.physics_gatekeeper.total_violations}")
    print(f"  Rejection rate: {final_stats['overall_rejection_rate']:.2%}")
    print()
    
    print(f"CARP Interactions:")
    print(f"  Total encounters: {capture_stats['total_encounters']}")
    print(f"  Successful captures: {capture_stats['successful_captures']}")
    print(f"  Capture rate: {capture_stats['capture_rate']:.2%}")
    print(f"  Energy transferred: {capture_stats['total_energy_transferred']:.4f}")
    print()
    
    print("=" * 70)
    print("✅ SMOKE TEST PASSED")
    print("=" * 70)
    print()
    print("All critical checks passed:")
    print("  ✓ Systems integrated")
    print("  ✓ Populations stable")
    print("  ✓ Zero violations")
    print("  ✓ No runtime crashes")
    print()
    print("Ready for 1,000-generation co-evolution test!")
    
    return True


if __name__ == '__main__':
    try:
        success = run_smoke_test()
        sys.exit(0 if success else 1)
    except AssertionError as e:
        print(f"\n❌ SMOKE TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
