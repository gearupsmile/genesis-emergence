"""
CARP Step 1 Validation Test

Tests minimal co-evolutionary arms race implementation.

Goal: Measure if predator-prey dynamics create behavioral diversity
where environmental pressures alone failed.

Target: Behavioral variance > 0.02 (4x improvement from Week 3's 0.0000)
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from engine.genesis_engine import GenesisEngine
from engine.carp import Species


def test_carp_step1():
    """
    Run 2,000-generation CARP validation.
    
    Measures:
    - Behavioral variance with co-evolution
    - Species survival rates
    - Interaction frequency
    - Population stability
    """
    print("=" * 70)
    print("CARP STEP 1 VALIDATION - MINIMAL CO-EVOLUTION TEST")
    print("=" * 70)
    print()
    
    print("Testing if predator-prey dynamics create behavioral diversity")
    print("Week 3 baseline (environmental pressures only): 0.0000")
    print("Target (with co-evolution): > 0.02 (4x improvement)")
    print()
    
    # Create engine with CARP
    engine = GenesisEngine(
        population_size=100,
        mutation_rate=0.3,
        simulation_steps=5
    )
    
    print(f"Systems initialized:")
    print(f"  Population: {len(engine.population)}")
    print(f"  Species assigner: {engine.species_assigner}")
    print(f"  Interaction handler: {engine.interaction_handler}")
    print()
    
    # Check initial species distribution
    species_counts = engine.species_assigner.get_species_counts(engine.population)
    print(f"Initial species distribution:")
    print(f"  Foragers: {species_counts['foragers']}")
    print(f"  Predators: {species_counts['predators']}")
    print()
    
    # Track metrics
    variance_history = []
    species_history = []
    interaction_history = []
    
    print("Running 2,000 generations...")
    print("Tracking every 100 generations...")
    print()
    
    for gen in range(2000):
        engine.run_cycle()
        
        # Track every 100 gens
        if (gen + 1) % 100 == 0:
            # Species counts
            counts = engine.species_assigner.get_species_counts(engine.population)
            species_history.append((gen + 1, counts))
            
            # Interaction stats
            interaction_stats = engine.interaction_handler.get_statistics()
            interaction_history.append((gen + 1, interaction_stats))
            
            # Behavioral variance (using behavioral tracker)
            agent_ids = [a.id for a in engine.population]
            variance = engine.behavioral_tracker.calculate_population_variance(agent_ids)
            variance_history.append((gen + 1, variance))
            
            # Progress report
            print(f"  Gen {gen+1}: "
                  f"Variance={variance:.4f}, "
                  f"Foragers={counts['foragers']}, "
                  f"Predators={counts['predators']}, "
                  f"Captures={interaction_stats['successful_captures']}")
            
            # Early feedback at 500 gens
            if gen + 1 == 500:
                print()
                print("  " + "=" * 66)
                print(f"  EARLY FEEDBACK (500 generations):")
                print(f"    Behavioral variance: {variance:.4f}")
                print(f"    Week 3 baseline: 0.0000")
                if variance > 0.02:
                    print(f"    Status: ON TRACK (>{variance/0.02:.1f}x target)")
                elif variance > 0.01:
                    print(f"    Status: PROMISING (partial improvement)")
                else:
                    print(f"    Status: NEEDS WORK (minimal improvement)")
                print("  " + "=" * 66)
                print()
    
    print()
    print("=" * 70)
    print("FINAL RESULTS")
    print("=" * 70)
    
    final_variance = variance_history[-1][1]
    final_species = species_history[-1][1]
    final_interactions = interaction_history[-1][1]
    
    print(f"\nBehavioral Variance (PRIMARY METRIC):")
    print(f"  Initial: {variance_history[0][1]:.4f}")
    print(f"  Final: {final_variance:.4f}")
    print(f"  Week 3 baseline: 0.0000")
    if final_variance > 0:
        print(f"  Improvement: {final_variance / 0.0012:.1f}x over structural baseline")
    print()
    
    print(f"Species Survival:")
    print(f"  Foragers: {final_species['foragers']}/70 initial")
    print(f"  Predators: {final_species['predators']}/30 initial")
    print(f"  Total: {final_species['total']}")
    print()
    
    print(f"Interaction Statistics:")
    print(f"  Total encounters: {final_interactions['total_encounters']}")
    print(f"  Successful captures: {final_interactions['successful_captures']}")
    print(f"  Successful evasions: {final_interactions['successful_evasions']}")
    print(f"  Capture rate: {final_interactions['capture_rate']:.2%}")
    print()
    
    # SUCCESS CRITERIA
    print("=" * 70)
    print("SUCCESS CRITERIA")
    print("=" * 70)
    
    # C1: Variance > 0.02
    c1_pass = final_variance > 0.02
    print(f"C1: Behavioral variance > 0.02")
    print(f"    Actual: {final_variance:.4f}")
    print(f"    Result: {'PASS' if c1_pass else 'FAIL'}")
    print()
    
    # C2: Both species survive
    c2_pass = final_species['foragers'] >= 20 and final_species['predators'] >= 10
    print(f"C2: Both species survive (F>=20, P>=10)")
    print(f"    Actual: F={final_species['foragers']}, P={final_species['predators']}")
    print(f"    Result: {'PASS' if c2_pass else 'FAIL'}")
    print()
    
    # C3: Meaningful interactions
    avg_captures = final_interactions['successful_captures'] / 2000
    c3_pass = avg_captures > 0.3
    print(f"C3: Meaningful interactions (>0.3 captures/gen)")
    print(f"    Actual: {avg_captures:.2f} captures/gen")
    print(f"    Result: {'PASS' if c3_pass else 'FAIL'}")
    print()
    
    # Overall
    print("=" * 70)
    if c1_pass and c2_pass:
        print("[SUCCESS] CARP Step 1 validates co-evolution creates diversity!")
        print("Proceed to CARP Step 2 (behavioral niches)")
        decision = "CONTINUE_FULL_CARP"
    elif final_variance > 0.01 and c2_pass:
        print("[PARTIAL] CARP shows promise but needs tuning")
        print("Adjust parameters and extend test to 5,000 generations")
        decision = "ADJUST_AND_RETRY"
    else:
        print("[NEEDS WORK] CARP insufficient or species extinction")
        print("Reassess approach or consult experts")
        decision = "REASSESS"
    
    print()
    print(f"RECOMMENDATION: {decision}")
    print("=" * 70)
    
    return decision, final_variance


if __name__ == '__main__':
    try:
        decision, variance = test_carp_step1()
        
        # Exit code based on decision
        if decision == "CONTINUE_FULL_CARP":
            sys.exit(0)  # Success
        elif decision == "ADJUST_AND_RETRY":
            sys.exit(2)  # Partial
        else:
            sys.exit(1)  # Needs work
            
    except Exception as e:
        print(f"\n[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
