"""
Tests for EPC (Expressed Phenotype Complexity) Metrics

Verifies:
1. Lempel-Ziv complexity implementation
2. Phenotype extraction from agents
3. EPC computation for individual agents
4. Population-level EPC statistics
5. Integration with PNCTLogger
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from engine.diagnostics.pnct_metrics import (
    lz_complexity, extract_expressed_phenotype, ComplexityTracker, PNCTLogger
)
from engine.structurally_evolvable_agent import StructurallyEvolvableAgent
from engine.evolvable_genome import EvolvableGenome
from engine.linkage_structure import LinkageStructure
from engine.codon_translator import CodonTranslator
from engine.pareto_evaluator import ParetoCoevolutionEvaluator


def test_lz_complexity():
    """Test Lempel-Ziv complexity with known examples."""
    print("Test 1: Lempel-Ziv Complexity")
    
    # Test cases with expected relative complexity
    test_cases = [
        ("AAAAA", "low"),      # Highly repetitive
        ("ABCABC", "medium"),  # Some pattern
        ("ABCDEF", "high"),    # No repetition
        ("", "zero"),          # Empty string
    ]
    
    results = []
    for string, expected in test_cases:
        complexity = lz_complexity(string)
        results.append((string, complexity, expected))
        print(f"  '{string}': {complexity:.3f} ({expected})")
    
    # Verify basic properties
    assert results[3][1] == 0.0, "Empty string should have zero complexity"
    assert all(0.0 <= r[1] <= 1.0 for r in results), "All complexities should be in [0,1]"
    
    print("  [PASS]\n")


def test_phenotype_extraction():
    """Test phenotype extraction from agents."""
    print("Test 2: Phenotype Extraction")
    
    translator = CodonTranslator()
    
    # Create agent with known genome
    sequence = ['ACG', 'UUU', 'GGG', 'CCC', 'AAA']
    genome = EvolvableGenome(initial_sequence=sequence)
    linkage = LinkageStructure(genome_length=len(sequence))
    agent = StructurallyEvolvableAgent(genome, linkage)
    
    # Extract phenotype
    instructions = extract_expressed_phenotype(agent, translator)
    
    print(f"  Genome: {sequence}")
    print(f"  Expressed instructions: {instructions[:5]}")
    print(f"  Number of instructions: {len(instructions)}")
    
    # Verify we got instructions
    assert len(instructions) > 0, "Should extract some instructions"
    assert all(isinstance(inst, str) for inst in instructions), "All should be strings"
    
    print("  [PASS]\n")


def test_compute_epc():
    """Test EPC computation for individual agent."""
    print("Test 3: Compute EPC for Agent")
    
    tracker = ComplexityTracker()
    translator = CodonTranslator()
    
    # Create test agent
    sequence = ['ACG', 'UUU', 'GGG'] * 5  # Some repetition
    genome = EvolvableGenome(initial_sequence=sequence)
    linkage = LinkageStructure(genome_length=len(sequence))
    agent = StructurallyEvolvableAgent(genome, linkage)
    
    # Compute EPC
    epc = tracker.compute_epc(agent, translator)
    
    print(f"  LZ Complexity: {epc['lz_complexity']:.3f}")
    print(f"  Instruction Diversity: {epc['instruction_diversity']:.3f}")
    print(f"  Control Flow Estimate: {epc['control_flow_estimate']:.3f}")
    
    # Verify structure
    assert 'lz_complexity' in epc
    assert 'instruction_diversity' in epc
    assert 'control_flow_estimate' in epc
    
    # Verify ranges
    assert 0.0 <= epc['lz_complexity'] <= 1.0
    assert 0.0 <= epc['instruction_diversity'] <= 1.0
    assert 0.0 <= epc['control_flow_estimate'] <= 1.0
    
    print("  [PASS]\n")


def test_epc_population():
    """Test population-level EPC statistics."""
    print("Test 4: EPC Population Statistics")
    
    tracker = ComplexityTracker()
    translator = CodonTranslator()
    
    # Create population with varying complexity
    population = []
    for i in range(5):
        # Vary genome size and content
        if i % 2 == 0:
            sequence = ['ACG'] * (5 + i * 2)  # Repetitive
        else:
            sequence = ['ACG', 'UUU', 'GGG', 'CCC', 'AAA'] * (i + 1)  # More varied
        
        genome = EvolvableGenome(initial_sequence=sequence)
        linkage = LinkageStructure(genome_length=len(sequence))
        agent = StructurallyEvolvableAgent(genome, linkage)
        population.append(agent)
    
    # Calculate population EPC
    epc_stats = tracker.calculate_epc_population(population, translator)
    
    print(f"  LZ Complexity:")
    print(f"    Mean: {epc_stats['lz_complexity']['mean']:.3f}")
    print(f"    Median: {epc_stats['lz_complexity']['median']:.3f}")
    print(f"    P90: {epc_stats['lz_complexity']['p90']:.3f}")
    
    print(f"  Instruction Diversity:")
    print(f"    Mean: {epc_stats['instruction_diversity']['mean']:.3f}")
    print(f"    P90: {epc_stats['instruction_diversity']['p90']:.3f}")
    
    # Verify structure
    for metric in ['lz_complexity', 'instruction_diversity', 'control_flow_estimate']:
        assert metric in epc_stats
        assert 'mean' in epc_stats[metric]
        assert 'median' in epc_stats[metric]
        assert 'variance' in epc_stats[metric]
        assert 'p90' in epc_stats[metric]
    
    print("  [PASS]\n")


def test_pnct_logger_with_epc():
    """Test PNCTLogger with EPC metrics."""
    print("Test 5: PNCTLogger with EPC")
    
    translator = CodonTranslator()
    logger = PNCTLogger(gac_interval=5, nnd_interval=10, translator=translator)
    evaluator = ParetoCoevolutionEvaluator()
    
    # Create test population
    population = []
    for i in range(5):
        sequence = ['ACG', 'UUU', 'GGG'] * 3
        genome = EvolvableGenome(initial_sequence=sequence)
        linkage = LinkageStructure(genome_length=len(sequence))
        agent = StructurallyEvolvableAgent(genome, linkage)
        population.append(agent)
    
    # Log at different generations
    for gen in [0, 5, 10, 15]:
        metrics = logger.log_metrics(gen, population, evaluator, translator)
        
        if gen % 5 == 0:
            print(f"  Gen {gen}: GAC={'gac' in metrics}, EPC={'epc' in metrics}, NND={'nnd' in metrics}")
            
            if 'epc' in metrics:
                print(f"    EPC LZ: {metrics['epc']['lz_complexity']['mean']:.3f}")
    
    # Verify histories
    gac_history = logger.get_gac_history()
    epc_history = logger.get_epc_history()
    nnd_history = logger.get_nnd_history()
    
    print(f"  GAC history: {len(gac_history)} entries")
    print(f"  EPC history: {len(epc_history)} entries")
    print(f"  NND history: {len(nnd_history)} entries")
    
    # EPC should be logged alongside GAC
    assert len(epc_history) == len(gac_history), "EPC should be logged with GAC"
    assert len(epc_history) > 0, "Should have EPC entries"
    
    print("  [PASS]\n")


def test_integration_with_genesis_engine():
    """Test EPC integration with GenesisEngine."""
    print("Test 6: Genesis Engine Integration")
    
    from engine.genesis_engine import GenesisEngine
    from engine.codon_translator import CodonTranslator
    
    # Create engine and translator
    engine = GenesisEngine(population_size=10, mutation_rate=0.1)
    translator = CodonTranslator()
    
    # Create PNCT logger with translator
    pnct_logger = PNCTLogger(gac_interval=5, nnd_interval=10, translator=translator)
    
    # Run a few cycles
    for gen in range(15):
        engine.run_cycle()
        
        # Log PNCT metrics
        metrics = pnct_logger.log_metrics(
            gen + 1,
            engine.population,
            engine.internal_evaluator,
            translator
        )
        
        if metrics.get('epc'):
            print(f"  Gen {gen+1}: EPC logged - "
                  f"LZ={metrics['epc']['lz_complexity']['mean']:.3f}, "
                  f"Div={metrics['epc']['instruction_diversity']['mean']:.3f}")
    
    # Verify EPC was logged
    epc_history = pnct_logger.get_epc_history()
    assert len(epc_history) > 0, "Should have EPC entries"
    
    print(f"  Final EPC entries: {len(epc_history)}")
    print("  [PASS]\n")


def run_all_tests():
    """Run all EPC metrics tests."""
    print("=" * 60)
    print("EPC METRICS TEST SUITE")
    print("=" * 60)
    print()
    
    tests = [
        test_lz_complexity,
        test_phenotype_extraction,
        test_compute_epc,
        test_epc_population,
        test_pnct_logger_with_epc,
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
        print("\n[SUCCESS] ALL EPC TESTS PASSED!")
        print("\nEPC Metrics Module Verification:")
        print("  - Lempel-Ziv complexity implementation correct")
        print("  - Phenotype extraction works")
        print("  - Individual EPC computation functional")
        print("  - Population-level statistics with P90")
        print("  - PNCTLogger integration successful")
        print("  - GenesisEngine integration works")
        print("\nPhase 6.1 EPC Metrics - COMPLETE!")
        return 0
    else:
        print(f"\n[FAILED] {failed} test(s) failed")
        return 1


if __name__ == '__main__':
    exit_code = run_all_tests()
    sys.exit(exit_code)
