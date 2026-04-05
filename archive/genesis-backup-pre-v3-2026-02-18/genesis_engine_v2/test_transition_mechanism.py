"""
Test Suite for Gradual Transition Mechanism

This test suite verifies the dual-evaluator transition system, with emphasis on:
1. Transition weight decay
2. Score normalization to [0, 1]
3. Final score blending
4. Population stability during transition
"""

import sys
from pathlib import Path

# Add the parent directory to the path so we can import the engine module
sys.path.insert(0, str(Path(__file__).parent))

from engine.genesis_engine import GenesisEngine


def test_transition_weight_decay():
    """Test that transition weight decays linearly from 1.0 to 0.0."""
    print("Test 1: Transition Weight Decay (CRITICAL)")
    
    engine = GenesisEngine(
        population_size=10,
        mutation_rate=0.2,
        transition_start_generation=0,
        transition_total_generations=10
    )
    
    # Initial weight should be 1.0
    assert engine.transition_weight == 1.0, f"Initial weight should be 1.0, got {engine.transition_weight}"
    print(f"  Initial weight: {engine.transition_weight:.2f}")
    
    # Run 10 generations
    for gen in range(10):
        engine.run_cycle()
        expected_weight = max(0.0, 1.0 - (gen + 1) * 0.1)
        actual_weight = engine.transition_weight
        
        assert abs(actual_weight - expected_weight) < 0.01, \
            f"Gen {gen+1}: expected weight {expected_weight:.2f}, got {actual_weight:.2f}"
        
        print(f"  Gen {gen+1}: weight={actual_weight:.2f} (expected {expected_weight:.2f})")
    
    # After 10 generations, weight should be 0.0 (within floating point tolerance)
    assert abs(engine.transition_weight) < 0.01, \
        f"Final weight should be ~0.0, got {engine.transition_weight}"
    
    print("  [PASS] Weight decayed from 1.0 to 0.0")
    print("  PASSED\n")


def test_score_normalization():
    """Test that scores are normalized to [0, 1] range."""
    print("Test 2: Score Normalization (CRITICAL)")
    
    engine = GenesisEngine(
        population_size=10,
        mutation_rate=0.2,
        transition_start_generation=0,
        transition_total_generations=100
    )
    
    # Run one cycle
    engine.run_cycle()
    
    # Check statistics
    stats = engine.statistics[-1]
    
    # External and internal scores should be raw (can be any value)
    print(f"  Raw external: avg={stats['avg_external_score']:.2f}, max={stats['max_external_score']:.2f}")
    print(f"  Raw internal: avg={stats['avg_internal_score']:.2f}, max={stats['max_internal_score']:.2f}")
    
    # Final score should be in [0, 1] (it's a blend of normalized scores)
    final_avg = stats['avg_final_score']
    final_max = stats['max_final_score']
    
    assert 0.0 <= final_avg <= 1.0, \
        f"Final avg score should be in [0,1], got {final_avg}"
    assert 0.0 <= final_max <= 1.0, \
        f"Final max score should be in [0,1], got {final_max}"
    
    print(f"  Final (normalized): avg={final_avg:.2f}, max={final_max:.2f}")
    print("  [PASS] Final scores in [0, 1] range")
    print("  PASSED\n")


def test_final_score_blending():
    """Test that final score is correctly blended."""
    print("Test 3: Final Score Blending")
    
    # Test at different transition points
    test_cases = [
        (0, 10, 1.0, "100% external"),   # Generation 0, weight=1.0
        (5, 10, 0.5, "50/50 blend"),     # Generation 5, weight=0.5
        (10, 10, 0.0, "100% internal"),  # Generation 10, weight=0.0
    ]
    
    for gen_to_run, total_gens, expected_weight, description in test_cases:
        engine = GenesisEngine(
            population_size=10,
            mutation_rate=0.2,
            transition_start_generation=0,
            transition_total_generations=total_gens
        )
        
        # Run to specific generation
        for _ in range(gen_to_run):
            engine.run_cycle()
        
        actual_weight = engine.transition_weight
        assert abs(actual_weight - expected_weight) < 0.01, \
            f"{description}: expected weight {expected_weight:.2f}, got {actual_weight:.2f}"
        
        print(f"  {description}: weight={actual_weight:.2f}")
    
    print("  [PASS] Blending weights correct at all stages")
    print("  PASSED\n")


def test_population_stability():
    """Test that population remains stable during transition."""
    print("Test 4: Population Stability During Transition")
    
    engine = GenesisEngine(
        population_size=20,
        mutation_rate=0.2,
        transition_start_generation=0,
        transition_total_generations=15
    )
    
    print(f"  Initial population: {len(engine.population)}")
    
    # Run through complete transition
    for gen in range(20):
        engine.run_cycle()
        
        # Population should persist
        assert len(engine.population) > 0, \
            f"Population extinct at generation {gen+1}"
        
        if gen % 5 == 0:
            stats = engine.statistics[-1]
            print(f"  Gen {gen+1}: pop={stats['population_size']}, "
                  f"weight={stats['transition_weight']:.2f}")
    
    final_pop = len(engine.population)
    print(f"  Final population: {final_pop}")
    print("  [PASS] Population stable through complete transition")
    print("  PASSED\n")


def test_dual_score_calculation():
    """Test that both evaluators are called and produce scores."""
    print("Test 5: Dual Score Calculation")
    
    engine = GenesisEngine(
        population_size=10,
        mutation_rate=0.2,
        transition_start_generation=0,
        transition_total_generations=100
    )
    
    # Run one cycle
    engine.run_cycle()
    
    stats = engine.statistics[-1]
    
    # Both score types should be present
    assert 'avg_external_score' in stats, "Should have external scores"
    assert 'avg_internal_score' in stats, "Should have internal scores"
    assert 'avg_final_score' in stats, "Should have final scores"
    
    # Scores should be non-negative
    assert stats['avg_external_score'] >= 0, "External score should be non-negative"
    assert stats['avg_internal_score'] >= 0, "Internal score should be non-negative"
    assert stats['avg_final_score'] >= 0, "Final score should be non-negative"
    
    print(f"  External: {stats['avg_external_score']:.2f}")
    print(f"  Internal: {stats['avg_internal_score']:.2f}")
    print(f"  Final: {stats['avg_final_score']:.2f}")
    print("  [PASS] Both evaluators producing scores")
    print("  PASSED\n")


def test_transition_statistics_logging():
    """Test that transition weight is logged in statistics."""
    print("Test 6: Transition Statistics Logging")
    
    engine = GenesisEngine(
        population_size=10,
        mutation_rate=0.2,
        transition_start_generation=0,
        transition_total_generations=10
    )
    
    # Run 5 generations
    for gen in range(5):
        engine.run_cycle()
    
    # Check all statistics have transition_weight
    for i, stats in enumerate(engine.statistics):
        assert 'transition_weight' in stats, \
            f"Generation {i} should have transition_weight"
        
        expected_weight = max(0.0, 1.0 - (i + 1) * 0.1)
        actual_weight = stats['transition_weight']
        
        assert abs(actual_weight - expected_weight) < 0.01, \
            f"Gen {i+1}: weight mismatch"
    
    print("  [PASS] Transition weight logged in all statistics")
    print("  PASSED\n")


def run_all_tests():
    """Run all tests and report results."""
    print("=" * 60)
    print("Gradual Transition Mechanism Test Suite")
    print("Testing Phase 4.2: Dual-Evaluator Transition")
    print("=" * 60)
    print()
    
    tests = [
        test_transition_weight_decay,
        test_score_normalization,
        test_final_score_blending,
        test_population_stability,
        test_dual_score_calculation,
        test_transition_statistics_logging,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"  FAILED: {e}\n")
            failed += 1
        except Exception as e:
            print(f"  ERROR: {e}\n")
            failed += 1
    
    print("=" * 60)
    print(f"Test Results: {passed} passed, {failed} failed")
    print("=" * 60)
    
    if failed == 0:
        print("\n[SUCCESS] ALL TESTS PASSED!")
        print("\nGradual Transition Mechanism Verification Summary:")
        print("  - Transition weight decays linearly")
        print("  - Scores normalized to [0, 1]")
        print("  - Final score blending correct")
        print("  - Population stable during transition")
        print("  - Both evaluators working")
        print("  - Statistics logging complete")
        print("\nPhase 4.2 (Gradual Transition) is COMPLETE!")
        return 0
    else:
        print(f"\n[FAILED] {failed} test(s) failed")
        return 1


if __name__ == '__main__':
    exit_code = run_all_tests()
    sys.exit(exit_code)
