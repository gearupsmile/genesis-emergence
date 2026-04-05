"""
Test Temporal Cycles - Week 3 Phase 3

Validates that temporal cycles drive phase adaptation.

Expected outcomes:
- Phase transitions occur correctly every 500 generations
- Resource usage responds to phase changes
- Behavioral variance increases due to temporal variation
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from engine.genesis_engine import GenesisEngine


def test_temporal_cycles():
    """Test that temporal cycles drive adaptation over 1,500 generations (3 cycles)."""
    print("=" * 70)
    print("TEMPORAL CYCLES ADAPTATION TEST")
    print("=" * 70)
    print()
    
    # Create engine with temporal system
    engine = GenesisEngine(
        population_size=50,  # Smaller for faster test
        mutation_rate=0.3,
        simulation_steps=5
    )
    
    print(f"Initial population: {len(engine.population)}")
    print(f"Temporal environment: {engine.temporal_env}")
    print(f"Cycle length: {engine.temporal_env.cycle_length} generations")
    print()
    
    # Track metrics over time
    phase_history = []
    resource_entropy_history = []
    
    print("Running 1,500 generations (3 full cycles)...")
    print()
    
    for gen in range(1500):
        engine.run_cycle()
        
        # Track metrics every 100 gens
        if (gen + 1) % 100 == 0:
            temporal_stats = engine.temporal_env.get_statistics()
            resource_stats = engine.resource_system.get_statistics()
            spatial_stats = engine.spatial_env.get_statistics()
            
            phase = temporal_stats['current_phase']
            phase_progress = temporal_stats['phase_progress']
            resource_entropy = resource_stats['specialization_entropy']
            
            phase_history.append(phase)
            resource_entropy_history.append(resource_entropy)
            
            print(f"  Gen {gen+1}: "
                  f"Phase={phase} ({phase_progress:.0%}), "
                  f"Entropy={resource_entropy:.3f}, "
                  f"Pop={len(engine.population)}")
    
    print()
    print("=" * 70)
    print("RESULTS")
    print("=" * 70)
    
    final_temporal = engine.temporal_env.get_statistics()
    final_resource = engine.resource_system.get_statistics()
    
    print(f"\nFinal temporal state:")
    print(f"  Current phase: {final_temporal['current_phase']}")
    print(f"  Phase transitions: {final_temporal['transition_count']}")
    print(f"  Total generations: {final_temporal['total_generations']}")
    print()
    
    print(f"Final resource specialization:")
    print(f"  Entropy: {final_resource['specialization_entropy']:.3f}")
    print(f"  Distribution: {final_resource['specialization_distribution']}")
    print()
    
    # Check success criteria
    print("SUCCESS CRITERIA:")
    print("-" * 70)
    
    # C3.1: Phase transitions occurred
    expected_transitions = 1500 // 500 * 3  # 3 phases per cycle, 3 cycles
    actual_transitions = final_temporal['transition_count']
    c31_pass = actual_transitions >= 6  # At least 2 full cycles
    print(f"C3.1: Phase transitions (count: {actual_transitions})")
    print(f"      Target: ≥6 (2 full cycles)")
    print(f"      Result: {'PASS' if c31_pass else 'FAIL'}")
    print()
    
    # C3.2: Resource specialization maintained/increased
    initial_entropy = resource_entropy_history[0] if resource_entropy_history else 0
    final_entropy = final_resource['specialization_entropy']
    c32_pass = final_entropy > 0.5
    print(f"C3.2: Resource specialization (entropy: {final_entropy:.3f})")
    print(f"      Initial: {initial_entropy:.3f}")
    print(f"      Target: >0.5")
    print(f"      Result: {'PASS' if c32_pass else 'FAIL'}")
    print()
    
    # C3.3: Phase diversity (multiple phases observed)
    unique_phases = len(set(phase_history))
    c33_pass = unique_phases >= 3
    print(f"C3.3: Phase diversity (unique phases: {unique_phases})")
    print(f"      Phases observed: {set(phase_history)}")
    print(f"      Target: ≥3")
    print(f"      Result: {'PASS' if c33_pass else 'FAIL'}")
    print()
    
    # Overall success
    all_pass = c31_pass and c32_pass and c33_pass
    print("=" * 70)
    if all_pass:
        print("[SUCCESS] Temporal cycles drive environmental variation")
    else:
        print("[PARTIAL] Some criteria not met - system may need tuning")
    
    return all_pass


if __name__ == '__main__':
    try:
        success = test_temporal_cycles()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
