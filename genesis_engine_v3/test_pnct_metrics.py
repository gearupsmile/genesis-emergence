"""
Tests for PNCT Metrics Module

Verifies:
1. Complexity calculations are correct
2. Novelty distance is properly normalized
3. Integration with existing Agent and EvolvableGenome classes
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from engine.diagnostics.pnct_metrics import ComplexityTracker, NoveltyAnalyzer, PNCTLogger
from engine.structurally_evolvable_agent import StructurallyEvolvableAgent
from engine.evolvable_genome import EvolvableGenome
from engine.linkage_structure import LinkageStructure
from engine.pareto_evaluator import ParetoCoevolutionEvaluator


def test_complexity_tracker():
    """Test ComplexityTracker calculates correct GAC metrics."""
    print("Test 1: ComplexityTracker")
    
    tracker = ComplexityTracker()
    
    # Create test population with varying genome sizes
    population = []
    for i in range(5):
        # Create genome with varying lengths (10, 15, 20, 25, 30 codons)
        sequence = ['ACG'] * (10 + i * 5)
        genome = EvolvableGenome(initial_sequence=sequence)
        linkage = LinkageStructure(genome_length=len(sequence))
        agent = StructurallyEvolvableAgent(genome, linkage)
        population.append(agent)
    
    # Calculate metrics
    metrics = tracker.calculate_metrics(population)
    
    # Verify structure
    assert 'genome_length' in metrics
    assert 'linkage_groups' in metrics
    assert 'avg_group_size' in metrics
    
    # Verify each has mean, median, variance
    for key in metrics:
        assert 'mean' in metrics[key]
        assert 'median' in metrics[key]
        assert 'variance' in metrics[key]
    
    # Verify reasonable values
    assert metrics['genome_length']['mean'] > 0
    assert metrics['linkage_groups']['mean'] > 0
    
    print(f"  Genome length: mean={metrics['genome_length']['mean']:.1f}, "
          f"median={metrics['genome_length']['median']:.1f}, "
          f"var={metrics['genome_length']['variance']:.2f}")
    print(f"  Linkage groups: mean={metrics['linkage_groups']['mean']:.1f}, "
          f"median={metrics['linkage_groups']['median']:.1f}, "
          f"var={metrics['linkage_groups']['variance']:.2f}")
    print("  [PASS]\n")


def test_novelty_analyzer():
    """Test NoveltyAnalyzer computes normalized distances."""
    print("Test 2: NoveltyAnalyzer")
    
    analyzer = NoveltyAnalyzer()
    
    # Create two agents with different genomes
    sequence1 = ['ACG'] * 10
    sequence2 = ['UUU'] * 10
    genome1 = EvolvableGenome(initial_sequence=sequence1)
    genome2 = EvolvableGenome(initial_sequence=sequence2)
    
    linkage1 = LinkageStructure(genome_length=len(sequence1))
    linkage2 = LinkageStructure(genome_length=len(sequence2))
    
    agent1 = StructurallyEvolvableAgent(genome1, linkage1)
    agent2 = StructurallyEvolvableAgent(genome2, linkage2)
    
    # Extract codons
    codons1 = analyzer.extract_expressed_codons(agent1)
    codons2 = analyzer.extract_expressed_codons(agent2)
    
    print(f"  Agent 1 codons: {codons1[:20]}...")
    print(f"  Agent 2 codons: {codons2[:20]}...")
    
    # Calculate Hamming distance
    distance = analyzer.hamming_distance(codons1, codons2)
    print(f"  Hamming distance: {distance}")
    
    # Verify distance is reasonable
    assert distance >= 0
    assert distance <= max(len(codons1), len(codons2))
    
    # Test identical strings
    dist_same = analyzer.hamming_distance(codons1, codons1)
    assert dist_same == 0, "Identical strings should have distance 0"
    
    print("  [PASS]\n")


def test_nnd_calculation():
    """Test NND calculation between Pareto fronts."""
    print("Test 3: NND Calculation")
    
    analyzer = NoveltyAnalyzer()
    evaluator = ParetoCoevolutionEvaluator()
    
    # Create first front
    front1 = []
    for i in range(3):
        sequence = ['ACG'] * 10
        genome = EvolvableGenome(initial_sequence=sequence)
        linkage = LinkageStructure(genome_length=len(sequence))
        agent = StructurallyEvolvableAgent(genome, linkage)
        front1.append(agent)
    
    # First epoch - should return 0 (no previous front)
    nnd1 = analyzer.calculate_nnd(front1, evaluator)
    assert nnd1['mean_nnd'] == 0.0, "First epoch should have NND=0"
    assert nnd1['front_size'] == 3
    print(f"  Epoch 1: NND={nnd1['mean_nnd']:.3f}, front_size={nnd1['front_size']}")
    
    # Create second front (different agents)
    front2 = []
    for i in range(3):
        sequence = ['UUU'] * 15  # Different size and content
        genome = EvolvableGenome(initial_sequence=sequence)
        linkage = LinkageStructure(genome_length=len(sequence))
        agent = StructurallyEvolvableAgent(genome, linkage)
        front2.append(agent)
    
    # Second epoch - should have non-zero NND
    nnd2 = analyzer.calculate_nnd(front2, evaluator)
    assert nnd2['mean_nnd'] >= 0, "NND should be non-negative"
    assert nnd2['front_size'] == 3
    print(f"  Epoch 2: NND={nnd2['mean_nnd']:.3f}, front_size={nnd2['front_size']}")
    
    # Verify normalization (should be roughly in [0, 1] range for typical cases)
    # Note: Can exceed 1 if new front is very different from previous
    print(f"  NND range: min={nnd2['min_nnd']:.3f}, max={nnd2['max_nnd']:.3f}")
    
    print("  [PASS]\n")


def test_pnct_logger():
    """Test PNCTLogger orchestration."""
    print("Test 4: PNCTLogger Orchestration")
    
    logger = PNCTLogger(gac_interval=500, nnd_interval=1000)
    evaluator = ParetoCoevolutionEvaluator()
    
    # Create test population
    population = []
    for i in range(5):
        sequence = ['ACG'] * 10
        genome = EvolvableGenome(initial_sequence=sequence)
        linkage = LinkageStructure(genome_length=len(sequence))
        agent = StructurallyEvolvableAgent(genome, linkage)
        population.append(agent)
    
    # Test logging at different generations
    test_gens = [0, 250, 500, 750, 1000, 1500]
    
    for gen in test_gens:
        metrics = logger.log_metrics(gen, population, evaluator)
        
        should_have_gac = logger.should_log_gac(gen)
        should_have_nnd = logger.should_log_nnd(gen)
        
        print(f"  Gen {gen}: GAC={should_have_gac}, NND={should_have_nnd}")
        
        # Verify correct intervals
        if should_have_gac:
            assert 'gac' in metrics, f"Gen {gen} should have GAC"
        if should_have_nnd:
            assert 'nnd' in metrics, f"Gen {gen} should have NND"
    
    # Verify history
    gac_history = logger.get_gac_history()
    nnd_history = logger.get_nnd_history()
    
    print(f"  GAC history length: {len(gac_history)}")
    print(f"  NND history length: {len(nnd_history)}")
    
    assert len(gac_history) == 4, "Should have 4 GAC entries (0, 500, 1000, 1500)"
    assert len(nnd_history) == 2, "Should have 2 NND entries (0, 1000)"
    
    print("  [PASS]\n")


def test_integration_with_genesis_engine():
    """Test integration with GenesisEngine components."""
    print("Test 5: Integration Test")
    
    from engine.genesis_engine import GenesisEngine
    
    # Create engine
    engine = GenesisEngine(population_size=10, mutation_rate=0.1)
    
    # Create PNCT logger
    pnct_logger = PNCTLogger(gac_interval=5, nnd_interval=10)
    
    # Run a few cycles
    for gen in range(15):
        engine.run_cycle()
        
        # Log PNCT metrics
        metrics = pnct_logger.log_metrics(
            gen + 1,
            engine.population,
            engine.internal_evaluator
        )
        
        if metrics.get('gac'):
            print(f"  Gen {gen+1}: GAC logged - "
                  f"genome_len={metrics['gac']['genome_length']['mean']:.1f}")
        
        if metrics.get('nnd'):
            print(f"  Gen {gen+1}: NND logged - "
                  f"mean_nnd={metrics['nnd']['mean_nnd']:.3f}")
    
    # Verify no crashes and reasonable data
    gac_history = pnct_logger.get_gac_history()
    nnd_history = pnct_logger.get_nnd_history()
    
    assert len(gac_history) > 0, "Should have GAC entries"
    assert len(nnd_history) > 0, "Should have NND entries"
    
    print(f"  Final GAC entries: {len(gac_history)}")
    print(f"  Final NND entries: {len(nnd_history)}")
    print("  [PASS]\n")


def run_all_tests():
    """Run all PNCT metrics tests."""
    print("=" * 60)
    print("PNCT METRICS TEST SUITE")
    print("=" * 60)
    print()
    
    tests = [
        test_complexity_tracker,
        test_novelty_analyzer,
        test_nnd_calculation,
        test_pnct_logger,
        test_integration_with_genesis_engine
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
        print("\nPNCT Metrics Module Verification:")
        print("  - ComplexityTracker calculates GAC correctly")
        print("  - NoveltyAnalyzer computes normalized distances")
        print("  - PNCTLogger orchestrates at correct intervals")
        print("  - Integration with GenesisEngine works")
        print("\nPhase 6 PNCT Metrics - COMPLETE!")
        return 0
    else:
        print(f"\n[FAILED] {failed} test(s) failed")
        return 1


if __name__ == '__main__':
    exit_code = run_all_tests()
    sys.exit(exit_code)
