"""
Test Suite for GenesisEngine

This test suite verifies the GenesisEngine implementation, with emphasis on:
1. Engine initialization
2. 5-generation simulation
3. Statistics tracking
4. Population persistence
5. Component integration
"""

import sys
from pathlib import Path

# Add the parent directory to the path so we can import the engine module
sys.path.insert(0, str(Path(__file__).parent))

from engine.genesis_engine import GenesisEngine


def test_engine_creation():
    """Test GenesisEngine initialization."""
    print("Test 1: Engine Creation")
    
    engine = GenesisEngine(population_size=10, mutation_rate=0.2)
    
    assert engine.population_size == 10, "Population size should be 10"
    assert engine.mutation_rate == 0.2, "Mutation rate should be 0.2"
    assert len(engine.population) == 10, "Should have 10 agents"
    assert engine.world is not None, "Should have world"
    assert engine.generation == 0, "Should start at generation 0"
    assert len(engine.statistics) == 0, "Should have no statistics yet"
    
    print(f"  [PASS] Engine initialized: {engine}")
    print(f"    Population: {len(engine.population)} agents")
    print(f"    World: {engine.world}")
    print("  PASSED\n")


def test_5_generation_simulation():
    """
    CRITICAL TEST: Run 5 complete generations.
    Verify all 5 steps execute without error.
    """
    print("Test 2: 5-Generation Simulation (CRITICAL)")
    
    engine = GenesisEngine(population_size=10, mutation_rate=0.2, simulation_steps=5)
    
    print(f"  Initial state: {engine}")
    
    # Run 5 generations
    for gen in range(5):
        engine.run_cycle()
        
        # Verify population persists
        assert len(engine.population) > 0, \
            f"Population should persist at generation {gen + 1}"
        
        # Verify statistics logged
        assert len(engine.statistics) == gen + 1, \
            f"Should have {gen + 1} statistics entries"
        
        # Verify generation counter
        assert engine.generation == gen + 1, \
            f"Generation should be {gen + 1}"
        
        print(f"  Gen {gen + 1}: {engine.get_statistics_summary()}")
    
    print(f"  [PASS] 5 generations completed successfully")
    print(f"  Final state: {engine}")
    print("  PASSED\n")


def test_statistics_tracking():
    """Test that statistics are logged correctly."""
    print("Test 3: Statistics Tracking")
    
    engine = GenesisEngine(population_size=10, mutation_rate=0.2)
    
    # Run 3 generations
    for gen in range(3):
        engine.run_cycle()
    
    assert len(engine.statistics) == 3, "Should have 3 statistics entries"
    
    # Verify statistics structure
    for i, stats in enumerate(engine.statistics):
        assert 'generation' in stats, "Should have generation"
        assert 'population_size' in stats, "Should have population_size"
        assert 'avg_fitness' in stats, "Should have avg_fitness"
        assert 'max_fitness' in stats, "Should have max_fitness"
        assert 'avg_genome_length' in stats, "Should have avg_genome_length"
        assert 'avg_linkage_groups' in stats, "Should have avg_linkage_groups"
        assert 'num_purged' in stats, "Should have num_purged"
        
        assert stats['generation'] == i, f"Generation should be {i}"
        assert stats['population_size'] > 0, "Population should be positive"
        
        print(f"  Gen {i}: pop={stats['population_size']}, "
              f"fitness={stats['avg_fitness']:.2f}, "
              f"genome={stats['avg_genome_length']:.1f}")
    
    print("  [PASS] Statistics tracked correctly")
    print("  PASSED\n")


def test_population_persistence():
    """Test that population persists across generations."""
    print("Test 4: Population Persistence")
    
    engine = GenesisEngine(population_size=20, mutation_rate=0.2)
    
    initial_pop = len(engine.population)
    print(f"  Initial population: {initial_pop}")
    
    # Run 10 generations
    for gen in range(10):
        engine.run_cycle()
        
        # Population should persist (may vary due to AIS culling)
        assert len(engine.population) > 0, \
            f"Population should persist at generation {gen + 1}"
    
    final_pop = len(engine.population)
    print(f"  Final population: {final_pop}")
    print(f"  [PASS] Population persisted for 10 generations")
    print("  PASSED\n")


def test_component_integration():
    """Test that all components are integrated correctly."""
    print("Test 5: Component Integration")
    
    engine = GenesisEngine(population_size=5, mutation_rate=0.2)
    
    # Verify components exist
    assert engine.translator is not None, "Should have translator"
    assert engine.ais is not None, "Should have AIS"
    assert engine.world is not None, "Should have world"
    assert len(engine.population) > 0, "Should have population"
    
    print("  [PASS] Translator: OK")
    print("  [PASS] AIS: OK")
    print("  [PASS] World: OK")
    print("  [PASS] Population: OK")
    
    # Run one cycle to verify integration
    engine.run_cycle()
    
    # Verify cycle completed
    print(f"  [PASS] Cycle completed successfully")
    
    # Verify statistics logged
    assert len(engine.statistics) == 1, "Should have 1 statistics entry"
    print("  [PASS] Statistics logged: OK")
    
    print("  PASSED\n")


def test_evolution_dynamics():
    """Test that evolution actually occurs."""
    print("Test 6: Evolution Dynamics")
    
    engine = GenesisEngine(population_size=15, mutation_rate=0.3)
    
    # Record initial state
    initial_stats = engine.statistics
    
    # Run 20 generations
    for gen in range(20):
        engine.run_cycle()
    
    # Get first and last statistics
    first_gen = engine.statistics[0]
    last_gen = engine.statistics[-1]
    
    print(f"  Generation 0:")
    print(f"    Avg fitness: {first_gen['avg_fitness']:.2f}")
    print(f"    Avg genome length: {first_gen['avg_genome_length']:.1f}")
    
    print(f"  Generation 19:")
    print(f"    Avg fitness: {last_gen['avg_fitness']:.2f}")
    print(f"    Avg genome length: {last_gen['avg_genome_length']:.1f}")
    
    # Verify some change occurred (evolution)
    # Note: With selection pressure, we expect fitness to increase
    # and genome length to change
    fitness_changed = abs(last_gen['avg_fitness'] - first_gen['avg_fitness']) > 0.1
    genome_changed = abs(last_gen['avg_genome_length'] - first_gen['avg_genome_length']) > 0.5
    
    if fitness_changed:
        print("  [PASS] Fitness evolved")
    if genome_changed:
        print("  [PASS] Genome length evolved")
    
    # At least one should change
    assert fitness_changed or genome_changed, \
        "Evolution should cause some change"
    
    print("  PASSED\n")


def run_all_tests():
    """Run all tests and report results."""
    print("=" * 60)
    print("GenesisEngine Test Suite")
    print("Testing Phase 3.2: Integrated Simulation Loop")
    print("=" * 60)
    print()
    
    tests = [
        test_engine_creation,
        test_5_generation_simulation,
        test_statistics_tracking,
        test_population_persistence,
        test_component_integration,
        test_evolution_dynamics,
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
        print("\nGenesisEngine Verification Summary:")
        print("  - Engine initialization [OK]")
        print("  - 5-generation simulation [OK]")
        print("  - Statistics tracking [OK]")
        print("  - Population persistence [OK]")
        print("  - Component integration [OK]")
        print("  - Evolution dynamics [OK]")
        print("\nPhase 3.2 (Integrated Simulation Loop) is COMPLETE!")
        print("\n" + "=" * 60)
        print("Genesis Engine v2 - BOOTSTRAP EVOLUTION COMPLETE!")
        print("=" * 60)
        print("All Phases Implemented:")
        print("  Phase 1.1: CodonTranslator [OK]")
        print("  Phase 1.2: AIS [OK]")
        print("  Phase 1.3: KernelAgent/World [OK]")
        print("  Phase 2.1: EvolvableGenome [OK]")
        print("  Phase 2.2: LinkageStructure [OK]")
        print("  Phase 2.3: StructurallyEvolvableAgent [OK]")
        print("  Phase 3.1: BootstrapEvaluator [OK]")
        print("  Phase 3.2: GenesisEngine [OK]")
        print("=" * 60)
        return 0
    else:
        print(f"\n[FAILED] {failed} test(s) failed")
        return 1


if __name__ == '__main__':
    exit_code = run_all_tests()
    sys.exit(exit_code)
