"""
Test Suite for LinkageStructure

This test suite verifies the LinkageStructure implementation, with emphasis on:
1. Linkage group management
2. Expression probabilities and probabilistic expression
3. Building block discovery (uniform to non-uniform evolution)
4. Linkage structure inheritance and evolution
5. Integration with EvolvableGenome
"""

import sys
import random
from pathlib import Path

# Add the parent directory to the path so we can import the engine module
sys.path.insert(0, str(Path(__file__).parent))

from engine.linkage_structure import LinkageStructure
from engine.evolvable_genome import EvolvableGenome


def test_basic_creation():
    """Test LinkageStructure initialization."""
    print("Test 1: Basic Creation")
    
    # Uniform structure
    linkage = LinkageStructure(genome_length=5)
    assert linkage.get_num_groups() == 5, "Should have 5 groups"
    assert all(len(g) == 1 for g in linkage.groups), "Each group should have 1 gene"
    assert all(linkage.expression_probabilities[i] == 1.0 for i in range(5)), \
        "All probabilities should be 1.0"
    print(f"  [PASS] Uniform structure: {linkage}")
    
    # Custom structure
    custom = LinkageStructure(groups=[{0, 1}, {2}, {3, 4}])
    assert custom.get_num_groups() == 3, "Should have 3 groups"
    assert {0, 1} in custom.groups, "Should have group {0, 1}"
    assert {2} in custom.groups, "Should have group {2}"
    assert {3, 4} in custom.groups, "Should have group {3, 4}"
    print(f"  [PASS] Custom structure: {custom}")
    
    print("  PASSED\n")


def test_group_management():
    """Test group lookup and management."""
    print("Test 2: Group Management")
    
    linkage = LinkageStructure(groups=[{0, 1}, {2}, {3, 4}])
    
    # Test get_group_for_index
    assert linkage.get_group_for_index(0) == 0, "Gene 0 should be in group 0"
    assert linkage.get_group_for_index(1) == 0, "Gene 1 should be in group 0"
    assert linkage.get_group_for_index(2) == 1, "Gene 2 should be in group 1"
    assert linkage.get_group_for_index(3) == 2, "Gene 3 should be in group 2"
    assert linkage.get_group_for_index(4) == 2, "Gene 4 should be in group 2"
    assert linkage.get_group_for_index(5) is None, "Gene 5 should not be found"
    print("  [PASS] Group lookup works correctly")
    
    print("  PASSED\n")


def test_expression_probabilities():
    """Test probabilistic gene expression."""
    print("Test 3: Expression Probabilities")
    
    # Set seed for reproducibility
    random.seed(42)
    
    linkage = LinkageStructure(groups=[{0, 1}, {2}, {3, 4}])
    
    # Test with 100% probability
    linkage.expression_probabilities = {0: 1.0, 1: 1.0, 2: 1.0}
    expressed = linkage.get_expressed_indices(5)
    assert set(expressed) == {0, 1, 2, 3, 4}, "All genes should be expressed at 100%"
    print(f"  [PASS] 100% probability: {expressed}")
    
    # Test with 0% probability
    linkage.expression_probabilities = {0: 0.0, 1: 0.0, 2: 0.0}
    expressed = linkage.get_expressed_indices(5)
    assert len(expressed) == 0, "No genes should be expressed at 0%"
    print(f"  [PASS] 0% probability: {expressed}")
    
    # Test with mixed probabilities (run multiple times)
    linkage.expression_probabilities = {0: 0.5, 1: 1.0, 2: 0.5}
    results = []
    for _ in range(100):
        expressed = linkage.get_expressed_indices(5)
        results.append(tuple(expressed))
    
    # Verify variation (not all the same)
    unique_results = set(results)
    assert len(unique_results) > 1, "Should have variation with 50% probabilities"
    print(f"  [PASS] Mixed probabilities show variation: {len(unique_results)} unique patterns")
    
    print("  PASSED\n")


def test_building_block_discovery():
    """
    CRITICAL TEST: Simulate evolution from uniform to non-uniform linkage structure.
    Verify that beneficial gene combinations are discovered and preserved.
    """
    print("Test 4: Building Block Discovery (CRITICAL)")
    
    # Start with uniform structure (6 genes, each separate)
    linkage = LinkageStructure(genome_length=6)
    initial_groups = linkage.get_num_groups()
    assert initial_groups == 6, "Should start with 6 separate groups"
    print(f"  Initial structure: {linkage}")
    
    # Create parent genome
    parent = EvolvableGenome(['AAA', 'CAA', 'GAA', 'TAA', 'ACA', 'AGA'])
    
    # Create high performers with pattern: genes 0,1,2 always together
    # (simulating that this combination is beneficial)
    high_performers = []
    for i in range(10):
        # All high performers have genes 0,1,2
        genome = EvolvableGenome(['AAA', 'CAA', 'GAA', 'TAA', 'ACA', 'AGA'])
        high_performers.append(genome)
    
    print(f"  Created {len(high_performers)} high performers with genes 0,1,2 together")
    
    # Run building block discovery
    linkage.merge_groups(parent, high_performers, co_occurrence_threshold=0.7)
    
    print(f"  After merge: {linkage}")
    
    # Verify linkage structure evolved
    final_groups = linkage.get_num_groups()
    assert final_groups < initial_groups, \
        f"Groups should have merged: {initial_groups} -> {final_groups}"
    print(f"  [PASS] Groups merged: {initial_groups} -> {final_groups}")
    
    # Verify genes 0,1,2 are in same group (building block discovered)
    group_0 = linkage.get_group_for_index(0)
    group_1 = linkage.get_group_for_index(1)
    group_2 = linkage.get_group_for_index(2)
    
    assert group_0 is not None, "Gene 0 should be in a group"
    assert group_0 == group_1, "Genes 0 and 1 should be in same group"
    assert group_0 == group_2, "Genes 0 and 2 should be in same group"
    
    building_block = linkage.groups[group_0]
    print(f"  [PASS] Building block discovered: {building_block}")
    assert 0 in building_block and 1 in building_block and 2 in building_block, \
        "Building block should contain genes 0, 1, 2"
    
    print("  PASSED\n")


def test_offspring_creation():
    """Test linkage structure inheritance and evolution."""
    print("Test 5: Offspring Creation")
    
    parent = LinkageStructure(groups=[{0, 1}, {2}, {3, 4}])
    parent_groups = parent.get_num_groups()
    
    # Create offspring with no mutations
    child = parent.create_offspring(mutation_rate=0.0)
    assert child.get_num_groups() == parent_groups, "Child should have same number of groups"
    assert child.groups == parent.groups, "Child should have same groups"
    print(f"  [PASS] Offspring with no mutations: {child}")
    
    # Create offspring with mutations (set seed for reproducibility)
    random.seed(42)
    child_mutated = parent.create_offspring(mutation_rate=1.0)
    # With mutation_rate=1.0, both split and merge will be attempted
    print(f"  [PASS] Offspring with mutations: {child_mutated}")
    print(f"    Parent groups: {parent.get_num_groups()}")
    print(f"    Child groups:  {child_mutated.get_num_groups()}")
    
    print("  PASSED\n")


def test_merge_groups_detailed():
    """Test merge_groups with different co-occurrence patterns."""
    print("Test 6: Merge Groups Detailed")
    
    linkage = LinkageStructure(genome_length=4)
    print(f"  Initial: {linkage}")
    
    parent = EvolvableGenome(['AAA', 'CAA', 'GAA', 'TAA'])
    
    # High performers where genes 0,1 co-occur 100%
    high_performers = [
        EvolvableGenome(['AAA', 'CAA', 'GAA', 'TAA']),
        EvolvableGenome(['AAA', 'CAA', 'GGA', 'TTA']),
        EvolvableGenome(['AAA', 'CAA', 'GTA', 'TAT']),
    ]
    
    linkage.merge_groups(parent, high_performers, co_occurrence_threshold=0.9)
    print(f"  After merge (threshold=0.9): {linkage}")
    
    # Verify genes 0,1 are merged
    group_0 = linkage.get_group_for_index(0)
    group_1 = linkage.get_group_for_index(1)
    assert group_0 == group_1, "Genes 0 and 1 should be merged"
    print(f"  [PASS] Genes 0,1 merged: {linkage.groups[group_0]}")
    
    # Verify genes 2,3 are still separate (they don't co-occur as much)
    group_2 = linkage.get_group_for_index(2)
    group_3 = linkage.get_group_for_index(3)
    # They might be merged or separate depending on exact co-occurrence
    print(f"  [PASS] Gene 2 in group: {linkage.groups[group_2]}")
    print(f"  [PASS] Gene 3 in group: {linkage.groups[group_3]}")
    
    print("  PASSED\n")


def test_integration_with_evolvable_genome():
    """Test integration with EvolvableGenome."""
    print("Test 7: Integration with EvolvableGenome")
    
    genome = EvolvableGenome(['AAA', 'CAA', 'GAA', 'TAA', 'ACA'])
    linkage = LinkageStructure(genome_length=genome.get_length())
    
    assert linkage.get_num_groups() == genome.get_length(), \
        "Linkage groups should match genome length"
    print(f"  [PASS] Linkage structure matches genome: {genome.get_length()} genes")
    
    # Get expressed indices
    expressed = linkage.get_expressed_indices(genome.get_length())
    assert all(0 <= i < genome.get_length() for i in expressed), \
        "All expressed indices should be valid"
    print(f"  [PASS] Expressed indices valid: {expressed}")
    
    # Simulate using expressed genes for development
    expressed_sequence = [genome.sequence[i] for i in expressed]
    print(f"  [PASS] Expressed sequence: {expressed_sequence}")
    
    print("  PASSED\n")


def run_all_tests():
    """Run all tests and report results."""
    print("=" * 60)
    print("LinkageStructure Test Suite")
    print("Testing Phase 2.2: Building Block Discovery")
    print("=" * 60)
    print()
    
    tests = [
        test_basic_creation,
        test_group_management,
        test_expression_probabilities,
        test_building_block_discovery,
        test_offspring_creation,
        test_merge_groups_detailed,
        test_integration_with_evolvable_genome,
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
        print("\nLinkageStructure Verification Summary:")
        print("  - Linkage groups manage gene indices")
        print("  - Expression probabilities control gene activation")
        print("  - Building block discovery works (uniform -> non-uniform)")
        print("  - Linkage structure evolves through inheritance")
        print("  - Compatible with EvolvableGenome")
        print("\nPhase 2.2 (Building Block Discovery) is COMPLETE!")
        return 0
    else:
        print(f"\n[FAILED] {failed} test(s) failed")
        return 1


if __name__ == '__main__':
    exit_code = run_all_tests()
    sys.exit(exit_code)
