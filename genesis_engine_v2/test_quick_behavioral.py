"""
Quick Behavioral Variance Test - Emergency Fix Validation

Tests if action-based behavioral tracking increases variance.

Target: Variance > 0.02 (16x improvement from 0.0012)
"""

import sys
from pathlib import Path
import numpy as np

sys.path.insert(0, str(Path(__file__).parent))

from engine.genesis_engine import GenesisEngine


def run_quick_behavioral_test():
    """
    Run 500-generation test with action-based behavioral tracking.
    
    This is the CRITICAL test to validate the emergency fix approach.
    """
    print("=" * 70)
    print("QUICK BEHAVIORAL VARIANCE TEST - EMERGENCY FIX VALIDATION")
    print("=" * 70)
    print()
    
    print("Testing if action-based behavioral tracking increases variance")
    print("Current (structural): 0.0012")
    print("Target (action-based): > 0.02 (16x improvement)")
    print()
    
    # Create engine with ALL systems + behavioral tracker
    engine = GenesisEngine(
        population_size=100,
        mutation_rate=0.3,
        simulation_steps=5
    )
    
    print(f"Systems initialized:")
    print(f"  Population: {len(engine.population)}")
    print(f"  Behavioral tracker: {engine.behavioral_tracker}")
    print()
    
    # Track variance over time
    variance_history = []
    
    print("Running 500 generations...")
    print("Tracking behavioral variance every 25 generations...")
    print()
    
    for gen in range(500):
        engine.run_cycle()
        
        # Track variance every 25 gens
        if (gen + 1) % 25 == 0:
            # Calculate action-based behavioral variance
            agent_ids = [agent.id for agent in engine.population]
            variance = engine.behavioral_tracker.calculate_population_variance(agent_ids)
            variance_history.append((gen + 1, variance))
            
            # Progress report
            print(f"  Gen {gen+1}: Variance={variance:.4f}, Pop={len(engine.population)}")
            
            # Early feedback at 100 gens
            if gen + 1 == 100:
                print()
                print("  " + "=" * 66)
                print(f"  EARLY FEEDBACK (100 generations):")
                print(f"    Action-based variance: {variance:.4f}")
                print(f"    Old structural variance: 0.0012")
                print(f"    Improvement: {variance / 0.0012:.1f}x")
                print(f"    Target: > 0.02 (16.7x)")
                if variance > 0.02:
                    print(f"    Status: ✓ ON TRACK")
                elif variance > 0.005:
                    print(f"    Status: ⚠️ PARTIAL IMPROVEMENT")
                else:
                    print(f"    Status: ✗ NO IMPROVEMENT")
                print("  " + "=" * 66)
                print()
    
    print()
    print("=" * 70)
    print("FINAL RESULTS")
    print("=" * 70)
    
    initial_variance = variance_history[0][1]
    final_variance = variance_history[-1][1]
    
    print(f"\nAction-Based Behavioral Variance:")
    print(f"  Initial (gen 25): {initial_variance:.4f}")
    print(f"  Final (gen 500): {final_variance:.4f}")
    print(f"  Change: {final_variance - initial_variance:+.4f}")
    print()
    
    print(f"Comparison to Structural Variance:")
    print(f"  Old structural variance: 0.0012")
    print(f"  New action-based variance: {final_variance:.4f}")
    print(f"  Improvement: {final_variance / 0.0012:.1f}x")
    print()
    
    # DECISION CRITERIA
    print("=" * 70)
    print("DECISION CRITERIA")
    print("=" * 70)
    
    if final_variance > 0.02:
        print(f"✅ SCENARIO A: Variance > 0.02 ({final_variance:.4f})")
        print("   Action-based tracking WORKS!")
        print("   Next: Amplify environmental pressures 5-10x")
        print("   Goal: Reach variance > 0.05")
        decision = "CONTINUE_EMERGENCY_FIX"
    elif final_variance > 0.005:
        print(f"⚠️ SCENARIO B: Variance 0.005-0.02 ({final_variance:.4f})")
        print("   Partial improvement but insufficient")
        print("   Next: Adjust behavioral signature dimensions")
        print("   Add: Movement pattern analysis, temporal coordination")
        decision = "ADJUST_AND_RETRY"
    else:
        print(f"❌ SCENARIO C: Variance < 0.005 ({final_variance:.4f})")
        print("   No significant improvement")
        print("   Next: Pivot to co-evolutionary arms race (CARP)")
        print("   Implement: Predator-prey dynamics, explicit niches")
        decision = "PIVOT_TO_CARP"
    
    print()
    print(f"RECOMMENDATION: {decision}")
    print("=" * 70)
    
    return decision, final_variance


if __name__ == '__main__':
    try:
        decision, variance = run_quick_behavioral_test()
        
        # Exit code based on decision
        if decision == "CONTINUE_EMERGENCY_FIX":
            sys.exit(0)  # Success
        elif decision == "ADJUST_AND_RETRY":
            sys.exit(2)  # Partial success
        else:
            sys.exit(1)  # Need pivot
            
    except Exception as e:
        print(f"\n[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
