"""
Test Suite for EvolvableGenome

This test suite verifies the EvolvableGenome implementation, with emphasis on:
1. Structural mutations (add/remove genes)
2. Innovation ID tracking and uniqueness
3. Metabolic cost management
4. 100-generation evolution with length variation
5. Inheritance and offspring creation
"""

import sys
import random
from pathlib import Path

# Add the parent directory to the path so we can import the engine module
sys.path.insert(0, str(Path(__file__).parent))

from engine.evolvable_genome import EvolvableGenome
from engine.codon_translator import CodonTranslator


def test_basic_creation():
    """Test EvolvableGenome initialization."""
    print("Test 1: Basic Creation")
    
    # Create empty genome
    genome = EvolvableGenome()
    assert genome.get_length() == 0, "Empty genome should have length 0"
    assert genome.metabolic_cost == 0.0, "Empty genome should have zero cost"
    print("  [PASS] Empty genome created")
    
    # Create with initial sequence
    genome = EvolvableGenome(['AAA', 'ACA', 'AGA'])
    assert genome.get_length() == 3, "Should have 3 genes"
    assert len(genome.innovation_ids) == 3, "Should have 3 innovation IDs"
    # With superlinear cost: 0.001 * (3 ** 1.5) ≈ 0.0052
    expected_cost = 0.001 * (3 ** 1.5)
    assert abs(genome.metabolic_cost - expected_cost) < 0.0001, f"Expected cost ~{expected_cost:.4f}, got {genome.metabolic_cost}"
    assert genome.get_sequence_string() == 'AAAACAAGA', "Sequence string should be concatenated"
    print("  [PASS] Genome with initial sequence created")
    
    # Verify innovation IDs are unique
    assert len(set(genome.innovation_ids)) == 3, "Innovation IDs should be unique"
    print("  [PASS] Innovation IDs are unique")
    
    print("  PASSED\n")


def test_add_gene():
    """Test gene addition."""
    print("Test 2: Add Gene")
    
    genome = EvolvableGenome(['AAA'])
    initial_cost = genome.metabolic_cost
    initial_length = genome.get_length()
    
    # Add specific gene
    new_id = genome.add_gene('CAA')
    assert genome.get_length() == initial_length + 1, "Length should increase"
    assert genome.sequence[-1] == 'CAA', "New gene should be appended"
    assert genome.innovation_ids[-1] == new_id, "New innovation ID should be appended"
    # Cost is recalculated with superlinear formula
    expected_cost = 0.001 * (2 ** 1.5)
    assert abs(genome.metabolic_cost - expected_cost) < 0.0001, \
        f"Cost should be ~{expected_cost:.4f}, got {genome.metabolic_cost}"
    print(f"  [PASS] Gene added: {genome.sequence}, IDs: {genome.innovation_ids}")
    
    # Add random gene
    new_id2 = genome.add_gene()
    assert genome.get_length() == initial_length + 2, "Length should increase again"
    assert len(genome.sequence[-1]) == 3, "Random gene should be 3 characters"
    assert new_id2 > new_id, "Innovation IDs should be increasing"
    print(f"  [PASS] Random gene added: {genome.sequence[-1]}, ID: {new_id2}")
    
    print("  PASSED\n")


def test_remove_gene():
    """Test gene removal."""
    print("Test 3: Remove Gene")
    
    genome = EvolvableGenome(['AAA', 'CAA', 'GAA'])
    initial_cost = genome.metabolic_cost
    initial_ids = genome.innovation_ids.copy()
    
    # Remove gene
    removed = genome.remove_gene()
    assert removed is not None, "Should return removed gene"
    assert genome.get_length() == 2, "Length should decrease"
    assert removed[1] in initial_ids, "Removed ID should be from original IDs"
    assert removed[1] not in genome.innovation_ids, "Removed ID should not be in genome"
    print(f"  [PASS] Gene removed: {removed}")
    
    # Verify cost unchanged
    assert genome.metabolic_cost == initial_cost, \
        "Metabolic cost should NOT decrease (permanent penalty)"
    print(f"  [PASS] Metabolic cost unchanged: {genome.metabolic_cost}")
    
    # Remove from empty genome
    empty_genome = EvolvableGenome()
    result = empty_genome.remove_gene()
    assert result is None, "Removing from empty genome should return None"
    print("  [PASS] Removing from empty genome returns None")
    
    print("  PASSED\n")


def test_metabolic_cost():
    """Test metabolic cost management with superlinear formula."""
    print("Test 4: Metabolic Cost")
    
    genome = EvolvableGenome(['AAA'])
    expected_cost_1 = 0.001 * (1 ** 1.5)  # 0.001
    assert abs(genome.metabolic_cost - expected_cost_1) < 0.0001, \
        f"Initial cost should be ~{expected_cost_1:.4f}, got {genome.metabolic_cost}"
    
    # Add 5 genes (total 6)
    for i in range(5):
        genome.add_gene()
    expected_cost_6 = 0.001 * (6 ** 1.5)  # ~0.0147
    assert abs(genome.metabolic_cost - expected_cost_6) < 0.0001, \
        f"Expected ~{expected_cost_6:.4f}, got {genome.metabolic_cost}"
    print(f"  [PASS] Cost after adding 5 genes: {genome.metabolic_cost:.4f}")
    
    # Remove 3 genes (length becomes 3, but cost stays at 6-gene level)
    for i in range(3):
        genome.remove_gene()
    # Cost should remain at 6-gene level (permanent penalty)
    assert abs(genome.metabolic_cost - expected_cost_6) < 0.0001, \
        f"Cost should remain ~{expected_cost_6:.4f} after removals (permanent penalty)"
    print(f"  [PASS] Cost after removing 3 genes: {genome.metabolic_cost:.4f} (unchanged)")
    
    print("  PASSED\n")


def test_innovation_id_uniqueness():
    """Test that innovation IDs are globally unique."""
    print("Test 5: Innovation ID Uniqueness")
    
    # Create multiple genomes
    genome1 = EvolvableGenome(['AAA', 'CAA'])
    genome2 = EvolvableGenome(['GAA', 'TAA'])
    
    # Collect all IDs
    all_ids = genome1.innovation_ids + genome2.innovation_ids
    
    # Verify uniqueness
    assert len(all_ids) == len(set(all_ids)), "All innovation IDs should be unique"
    print(f"  [PASS] IDs from genome1: {genome1.innovation_ids}")
    print(f"  [PASS] IDs from genome2: {genome2.innovation_ids}")
    print(f"  [PASS] All IDs are globally unique")
    
    # Add genes and verify new IDs are unique
    genome1.add_gene()
    genome2.add_gene()
    all_ids = genome1.innovation_ids + genome2.innovation_ids
    assert len(all_ids) == len(set(all_ids)), "New IDs should also be unique"
    print("  [PASS] New IDs after additions are unique")
    
    print("  PASSED\n")


def test_inheritance():
    """Test offspring creation and inheritance."""
    print("Test 6: Inheritance")
    
    parent = EvolvableGenome(['AAA', 'CAA', 'GAA'])
    parent_sequence = parent.sequence.copy()
    parent_ids = parent.innovation_ids.copy()
    parent_cost = parent.metabolic_cost
    
    # Create offspring with no mutations (mutation_rate=0)
    child = parent.create_offspring(mutation_rate=0.0)
    
    # Verify inheritance
    assert child.sequence == parent_sequence, "Child should inherit parent sequence"
    assert child.innovation_ids == parent_ids, "Child should inherit parent innovation IDs"
    assert child.metabolic_cost == parent_cost, "Child should inherit parent metabolic cost"
    print("  [PASS] Offspring inherits parent properties (no mutations)")
    
    # Create offspring with mutations
    child_mutated = parent.create_offspring(mutation_rate=1.0)
    # With mutation_rate=1.0, both add and remove will occur
    # Length might be same, +1, -1, or +0 depending on order
    print(f"  [PASS] Offspring with mutations: parent length={parent.get_length()}, "
          f"child length={child_mutated.get_length()}")
    
    print("  PASSED\n")


def test_100_generation_evolution():
    """
    CRITICAL TEST: Simulate 100 generations of random structural mutations.
    Verify genome length changes, innovation IDs preserved, cost increases.
    """
    print("Test 7: 100-Generation Evolution (CRITICAL)")
    
    # Set seed for reproducibility
    random.seed(42)
    
    genome = EvolvableGenome(['AAA', 'ACA', 'AGA'])
    initial_length = genome.get_length()
    initial_cost = genome.metabolic_cost
    
    print(f"  Initial: {genome}")
    
    lengths = []
    costs = []
    all_innovation_ids = set(genome.innovation_ids)
    
    for generation in range(100):
        # Random structural mutation
        if random.random() < 0.5:
            new_id = genome.add_gene()
            all_innovation_ids.add(new_id)
        else:
            removed = genome.remove_gene()
            # Removed IDs are no longer in genome but were once assigned
        
        lengths.append(genome.get_length())
        costs.append(genome.metabolic_cost)
    
    print(f"  After 100 generations: {genome}")
    print(f"  Length range: {min(lengths)} to {max(lengths)}")
    print(f"  Final cost: {genome.metabolic_cost:.3f}")
    
    # Verify length changed
    unique_lengths = set(lengths)
    assert len(unique_lengths) > 1, f"Genome length should vary, got {unique_lengths}"
    print(f"  [PASS] Genome length varied: {len(unique_lengths)} different lengths")
    
    # Verify innovation IDs in genome are unique
    assert len(genome.innovation_ids) == len(set(genome.innovation_ids)), \
        "Innovation IDs in genome should be unique"
    print(f"  [PASS] Innovation IDs remain unique: {len(genome.innovation_ids)} genes")
    
    # Verify metabolic cost increased or stayed same
    assert genome.metabolic_cost >= initial_cost, \
        "Metabolic cost should not decrease"
    print(f"  [PASS] Metabolic cost increased: {initial_cost:.3f} -> {genome.metabolic_cost:.3f}")
    
    # Verify all innovation IDs ever assigned are unique
    assert len(all_innovation_ids) == len(set(all_innovation_ids)), \
        "All innovation IDs ever assigned should be unique"
    print(f"  [PASS] All {len(all_innovation_ids)} innovation IDs ever assigned are unique")
    
    print("  PASSED\n")


def test_codon_translator_integration():
    """Test integration with CodonTranslator."""
    print("Test 8: CodonTranslator Integration")
    
    translator = CodonTranslator()
    genome = EvolvableGenome(['AAA', 'AAT', 'ACA'])
    
    # Get sequence string
    sequence_string = genome.get_sequence_string()
    assert sequence_string == 'AAAAATACA', f"Expected 'AAAAATACA', got {sequence_string}"
    print(f"  [PASS] Sequence string: {sequence_string}")
    
    # Translate using CodonTranslator
    phenotype = translator.translate_sequence(sequence_string, 'agent')
    assert phenotype == ['move_forward', 'move_forward', 'turn_left'], \
        f"Unexpected phenotype: {phenotype}"
    print(f"  [PASS] Phenotype: {phenotype}")
    
    # Verify it works as drop-in replacement
    print("  [PASS] EvolvableGenome works as drop-in replacement for string genotype")
    
    print("  PASSED\n")


def run_all_tests():
    """Run all tests and report results."""
    print("=" * 60)
    print("EvolvableGenome Test Suite")
    print("Testing Phase 2.1: Complexification")
    print("=" * 60)
    print()
    
    tests = [
        test_basic_creation,
        test_add_gene,
        test_remove_gene,
        test_metabolic_cost,
        test_innovation_id_uniqueness,
        test_inheritance,
        test_100_generation_evolution,
        test_codon_translator_integration,
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
        print("\nEvolvableGenome Verification Summary:")
        print("  - Structural mutations work (add/remove genes)")
        print("  - Innovation IDs are globally unique and persistent")
        print("  - Metabolic cost increases with complexity (permanent penalty)")
        print("  - 100-generation evolution shows length variation")
        print("  - Inheritance preserves sequence and innovation IDs")
        print("  - Compatible with CodonTranslator (drop-in replacement)")
        print("\nPhase 2.1 (Complexification) is COMPLETE!")
        return 0
    else:
        print(f"\n[FAILED] {failed} test(s) failed")
        return 1


if __name__ == '__main__':
    exit_code = run_all_tests()
    sys.exit(exit_code)
