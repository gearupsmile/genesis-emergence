"""
Phase 2 Validation: Frequency-Dependent Selection Test

500-generation test to verify:
1. Species ratio stable via inheritance (rebalancing <10%)
2. Trait divergence emerging (>0.02)
3. Zero physics violations maintained
"""

import sys
from pathlib import Path
import numpy as np

sys.path.insert(0, str(Path(__file__).parent))

from engine.genesis_engine_minimal import GenesisEngineMinimal
from engine.carp.species import Species


def test_frequency_dependent_selection():
    """
    500-generation test of inheritance-based selection.
    
    Success Criteria:
    1. Species ratio remains viable (minimal rebalancing)
    2. Trait divergence begins to emerge
    3. Zero physics violations (maintained from Phase 1)
    """
    print("=" * 70)
    print("PHASE 2 VALIDATION: FREQUENCY-DEPENDENT SELECTION TEST")
    print("=" * 70)
    print()
    print("Testing: Inheritance-based species propagation")
    print("Duration: 500 generations")
    print("Expected: Trait divergence emerges, ratio stable")
    print()
    
    engine = GenesisEngineMinimal(population_size=100, mutation_rate=0.3)
    
    print(f"Initial population: {len(engine.population)}")
    print(f"Initial ratio: 70F / 30P (assigned)")
    print()
    print("Running 500 generations...")
    print()
    
    # Track metrics
    rebalance_count = 0
    aggression_divergence_history = []
    exploration_divergence_history = []
    
    for gen in range(500):
        # Count rebalances by checking output
        import io
        import sys as sys_module
        old_stdout = sys_module.stdout
        sys_module.stdout = io.StringIO()
        
        engine.run_cycle()
        
        output = sys_module.stdout.getvalue()
        sys_module.stdout = old_stdout
        
        if "[REBALANCE]" in output:
            rebalance_count += 1
            print(output.strip())
        
        # HARD ASSERTION: Physics violations must remain zero
        violations = engine.physics_gatekeeper.total_violations
        assert violations == 0, f"Gen {gen}: Physics violations detected! Phase 1 fix broken!"
        
        # Track divergence
        stats = engine.get_statistics()
        agg_div = abs(stats['predator_aggression'] - stats['forager_aggression'])
        exp_div = abs(stats['forager_exploration'] - stats['predator_exploration'])
        aggression_divergence_history.append(agg_div)
        exploration_divergence_history.append(exp_div)
        
        # Report every 100 generations
        if (gen + 1) % 100 == 0:
            print(f"  Gen {gen+1}:")
            print(f"    Ratio: {stats['forager_count']}F / {stats['predator_count']}P")
            print(f"    Aggression: F={stats['forager_aggression']:.3f}, P={stats['predator_aggression']:.3f} (D={agg_div:.3f})")
            print(f"    Exploration: F={stats['forager_exploration']:.3f}, P={stats['predator_exploration']:.3f} (D={exp_div:.3f})")
            print(f"    Rebalances so far: {rebalance_count}")
    
    print()
    print("=" * 70)
    print("PHASE 2 VALIDATION: RESULTS")
    print("=" * 70)
    print()
    
    # Final statistics
    final_stats = engine.get_statistics()
    
    print(f"Final Ratio: {final_stats['forager_count']}F / {final_stats['predator_count']}P")
    print(f"Rebalance events: {rebalance_count}/500 ({rebalance_count/500*100:.1f}%)")
    print()
    
    # Trait divergence
    final_agg_div = abs(final_stats['predator_aggression'] - final_stats['forager_aggression'])
    final_exp_div = abs(final_stats['forager_exploration'] - final_stats['predator_exploration'])
    
    print(f"Trait Divergence:")
    print(f"  Aggression: {final_agg_div:.4f} (target: >0.02)")
    print(f"  Exploration: {final_exp_div:.4f} (target: >0.02)")
    print()
    
    # Trend analysis
    early_agg_div = np.mean(aggression_divergence_history[:100])
    late_agg_div = np.mean(aggression_divergence_history[-100:])
    agg_trend = late_agg_div - early_agg_div
    
    early_exp_div = np.mean(exploration_divergence_history[:100])
    late_exp_div = np.mean(exploration_divergence_history[-100:])
    exp_trend = late_exp_div - early_exp_div
    
    print(f"Divergence Trends:")
    print(f"  Aggression: {early_agg_div:.4f} -> {late_agg_div:.4f} ({'+' if agg_trend > 0 else ''}{agg_trend:.4f})")
    print(f"  Exploration: {early_exp_div:.4f} -> {late_exp_div:.4f} ({'+' if exp_trend > 0 else ''}{exp_trend:.4f})")
    print()
    
    # Physics integrity
    print(f"Physics Integrity:")
    print(f"  Violations: {engine.physics_gatekeeper.total_violations} (must be 0)")
    print()
    
    # Success criteria
    print("=" * 70)
    print("SUCCESS CRITERIA")
    print("=" * 70)
    print()
    
    criterion1 = rebalance_count < 50  # <10% rebalancing
    criterion2 = (final_agg_div > 0.02 or final_exp_div > 0.02)  # Divergence emerging
    criterion3 = engine.physics_gatekeeper.total_violations == 0  # Zero violations
    
    print(f"1. Minimal rebalancing (<10%): {rebalance_count < 50} {'[PASS]' if criterion1 else '[FAIL]'}")
    print(f"2. Trait divergence (>0.02): {criterion2} {'[PASS]' if criterion2 else '[FAIL]'}")
    print(f"3. Zero violations: {criterion3} {'[PASS]' if criterion3 else '[FAIL]'}")
    print()
    
    overall_pass = criterion1 and criterion2 and criterion3
    
    if overall_pass:
        print("[SUCCESS] PHASE 2 VALIDATION PASSED")
        print()
        print("Frequency-dependent selection restored!")
        print("Ready for Phase 3: Final 1,000-generation test")
    else:
        print("[PARTIAL] Some criteria not met")
        print()
        if not criterion1:
            print("  - Too much rebalancing (ratio unstable)")
        if not criterion2:
            print("  - Trait divergence not emerging yet")
        if not criterion3:
            print("  - Physics violations detected (Phase 1 broken)")
        print()
        print("May need parameter tuning before Phase 3")
    
    print()
    print("=" * 70)
    
    return overall_pass


if __name__ == '__main__':
    try:
        import time
        start_time = time.time()
        
        success = test_frequency_dependent_selection()
        
        elapsed = time.time() - start_time
        print(f"\nCompleted in {elapsed:.1f} seconds")
        
        sys.exit(0 if success else 1)
    except AssertionError as e:
        print(f"\n[FAILURE] {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
