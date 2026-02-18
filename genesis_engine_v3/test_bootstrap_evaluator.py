"""
Test Suite for BootstrapEvaluator

This test suite verifies the BootstrapEvaluator implementation, with emphasis on:
1. Fitness calculation correctness
2. Fitness gradient (complexity vs cost)
3. Tournament selection reliability
4. Edge cases
"""

import sys
import random
from pathlib import Path

# Add the parent directory to the path so we can import the engine module
sys.path.insert(0, str(Path(__file__).parent))

from engine.bootstrap_evaluator import calculate_fitness, tournament_selection
from engine.evolvable_genome import EvolvableGenome
from engine.linkage_structure import LinkageStructure
from engine.structurally_evolvable_agent import StructurallyEvolvableAgent
from engine.codon_translator import CodonTranslator


def test_fitness_calculation():
    """Test fitness calculation formula."""
    print("Test 1: Fitness Calculation")
    
    translator = CodonTranslator()
    
    # Create agent with known properties
    genome = EvolvableGenome(['AAA', 'CAA', 'GAA'])  # 3 genes, cost = 0.03
    agent = StructurallyEvolvableAgent(genome)
    agent.develop(translator)
    
    fitness = calculate_fitness(agent)
    
    # Expected: (1 + phenotype_length) / (1 + 0.03)
    phenotype_length = len(agent.phenotype) if agent.phenotype else 0
    expected_fitness = (1 + phenotype_length) / (1 + agent.genome.metabolic_cost)
    
    assert abs(fitness - expected_fitness) < 0.01, \
        f"Expected fitness ~{expected_fitness:.2f}, got {fitness:.2f}"
    print(f"  [PASS] Fitness calculated correctly: {fitness:.2f}")
    print(f"    Phenotype length: {phenotype_length}, Cost: {agent.genome.metabolic_cost:.3f}")
    
    print("  PASSED\n")


def test_fitness_gradient_complexity():
    """Test that higher complexity yields higher fitness."""
    print("Test 2: Fitness Gradient - Complexity")
    
    translator = CodonTranslator()
    
    # Create agents with increasing complexity
    agents = []
    fitness_scores = []
    
    for num_genes in [3, 5, 8]:
        genome = EvolvableGenome(['AAA'] * num_genes)
        agent = StructurallyEvolvableAgent(genome)
        agent.develop(translator)
        agents.append(agent)
        
        fitness = calculate_fitness(agent)
        fitness_scores.append(fitness)
        print(f"  {num_genes} genes: phenotype={len(agent.phenotype)}, fitness={fitness:.2f}")
    
    # Verify fitness increases with complexity
    assert fitness_scores[1] > fitness_scores[0], \
        "5-gene agent should have higher fitness than 3-gene"
    assert fitness_scores[2] > fitness_scores[1], \
        "8-gene agent should have higher fitness than 5-gene"
    
    print("  [PASS] Fitness increases with complexity")
    print("  PASSED\n")


def test_fitness_gradient_cost():
    """Test that higher metabolic cost yields lower fitness."""
    print("Test 3: Fitness Gradient - Metabolic Cost")
    
    translator = CodonTranslator()
    
    # Create agents with same phenotype but different costs
    # Agent 1: 3 genes (cost = 0.03)
    genome1 = EvolvableGenome(['AAA', 'CAA', 'GAA'])
    agent1 = StructurallyEvolvableAgent(genome1)
    agent1.develop(translator)
    fitness1 = calculate_fitness(agent1)
    
    # Agent 2: 3 genes but we'll artificially increase cost by adding then removing genes
    genome2 = EvolvableGenome(['AAA', 'CAA', 'GAA'])
    for _ in range(5):
        genome2.add_gene()  # Increases cost
    for _ in range(5):
        genome2.remove_gene()  # Doesn't decrease cost
    agent2 = StructurallyEvolvableAgent(genome2)
    agent2.develop(translator)
    fitness2 = calculate_fitness(agent2)
    
    print(f"  Agent 1: cost={agent1.genome.metabolic_cost:.3f}, fitness={fitness1:.2f}")
    print(f"  Agent 2: cost={agent2.genome.metabolic_cost:.3f}, fitness={fitness2:.2f}")
    
    # Verify higher cost yields lower fitness
    assert fitness2 < fitness1, \
        "Agent with higher metabolic cost should have lower fitness"
    
    print("  [PASS] Fitness decreases with metabolic cost")
    print("  PASSED\n")


def test_tournament_selection():
    """Test that tournament selection favors high-fitness agents."""
    print("Test 4: Tournament Selection (CRITICAL)")
    
    # Set seed for reproducibility
    random.seed(42)
    
    translator = CodonTranslator()
    
    # Create population with known fitness gradient
    population = []
    fitness_scores = {}
    
    for i in range(10):
        # Create agents with increasing complexity
        genome = EvolvableGenome(['AAA'] * (i + 1))
        agent = StructurallyEvolvableAgent(genome)
        agent.develop(translator)
        population.append(agent)
        
        fitness = calculate_fitness(agent)
        fitness_scores[agent.id] = fitness
    
    print(f"  Population size: {len(population)}")
    print(f"  Fitness range: {min(fitness_scores.values()):.2f} to {max(fitness_scores.values()):.2f}")
    
    # Select parents
    parents = tournament_selection(population, fitness_scores, num_parents=5, tournament_size=3)
    
    assert len(parents) == 5, f"Should select 5 parents, got {len(parents)}"
    print(f"  [PASS] Selected {len(parents)} parents")
    
    # Verify high-fitness agents selected
    parent_fitness = [fitness_scores[p.id] for p in parents]
    avg_parent_fitness = sum(parent_fitness) / len(parent_fitness)
    avg_population_fitness = sum(fitness_scores.values()) / len(fitness_scores)
    
    print(f"  Avg population fitness: {avg_population_fitness:.2f}")
    print(f"  Avg parent fitness: {avg_parent_fitness:.2f}")
    
    assert avg_parent_fitness > avg_population_fitness, \
        "Selected parents should have higher average fitness than population"
    
    print("  [PASS] Tournament selection favors high-fitness agents")
    print("  PASSED\n")


def test_edge_cases():
    """Test edge cases."""
    print("Test 5: Edge Cases")
    
    translator = CodonTranslator()
    
    # Agent with no phenotype (not developed)
    genome = EvolvableGenome(['AAA', 'CAA', 'GAA'])
    agent = StructurallyEvolvableAgent(genome)
    # Don't develop - phenotype is None
    
    fitness = calculate_fitness(agent)
    # Expected: (1 + 0) / (1 + 0.03) = 1 / 1.03 ≈ 0.97
    expected = 1.0 / (1 + agent.genome.metabolic_cost)
    assert abs(fitness - expected) < 0.01, \
        f"Undeveloped agent fitness should be ~{expected:.2f}, got {fitness:.2f}"
    print(f"  [PASS] Undeveloped agent: fitness={fitness:.2f}")
    
    # Empty population
    parents = tournament_selection([], {}, num_parents=5)
    assert len(parents) == 0, "Empty population should return empty parent list"
    print("  [PASS] Empty population handled")
    
    # Tournament size larger than population
    genome = EvolvableGenome(['AAA'])
    agent = StructurallyEvolvableAgent(genome)
    agent.develop(translator)
    population = [agent]
    fitness_scores = {agent.id: calculate_fitness(agent)}
    
    parents = tournament_selection(population, fitness_scores, num_parents=1, tournament_size=10)
    assert len(parents) == 1, "Should handle tournament_size > population"
    print("  [PASS] Large tournament size handled")
    
    print("  PASSED\n")


def test_selection_diversity():
    """Test that tournament selection maintains diversity."""
    print("Test 6: Selection Diversity")
    
    random.seed(42)
    translator = CodonTranslator()
    
    # Create uniform population (all same fitness)
    population = []
    fitness_scores = {}
    
    for i in range(10):
        genome = EvolvableGenome(['AAA', 'CAA', 'GAA'])
        agent = StructurallyEvolvableAgent(genome)
        agent.develop(translator)
        population.append(agent)
        fitness_scores[agent.id] = calculate_fitness(agent)
    
    # Select many parents
    parents = tournament_selection(population, fitness_scores, num_parents=20, tournament_size=3)
    
    # Verify diversity (should select different agents)
    unique_parents = set(p.id for p in parents)
    print(f"  Selected {len(parents)} parents, {len(unique_parents)} unique")
    
    # With uniform fitness, should see some diversity
    assert len(unique_parents) > 1, "Should maintain some diversity"
    print("  [PASS] Tournament selection maintains diversity")
    
    print("  PASSED\n")


def run_all_tests():
    """Run all tests and report results."""
    print("=" * 60)
    print("BootstrapEvaluator Test Suite")
    print("Testing Phase 3.1: Simple External Fitness")
    print("=" * 60)
    print()
    
    tests = [
        test_fitness_calculation,
        test_fitness_gradient_complexity,
        test_fitness_gradient_cost,
        test_tournament_selection,
        test_edge_cases,
        test_selection_diversity,
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
        print("\nBootstrapEvaluator Verification Summary:")
        print("  - Fitness calculation correct")
        print("  - Fitness increases with complexity")
        print("  - Fitness decreases with metabolic cost")
        print("  - Tournament selection favors high fitness")
        print("  - Edge cases handled")
        print("  - Selection maintains diversity")
        print("\nPhase 3.1 (Simple External Fitness) is COMPLETE!")
        return 0
    else:
        print(f"\n[FAILED] {failed} test(s) failed")
        return 1


if __name__ == '__main__':
    exit_code = run_all_tests()
    sys.exit(exit_code)
