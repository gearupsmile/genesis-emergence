"""
Test Suite for CodonTranslator

This test suite verifies the core functionality of the CodonTranslator,
with special emphasis on testing degeneracy - the critical feature that
ensures mutational robustness by having multiple codons map to the same
phenotypic instruction.
"""

import sys
from pathlib import Path

# Add the parent directory to the path so we can import the engine module
sys.path.insert(0, str(Path(__file__).parent))

from engine.codon_translator import CodonTranslator


def test_basic_translation():
    """Test basic codon translation functionality."""
    print("Test 1: Basic Translation")
    translator = CodonTranslator()
    
    # Test agent table translation
    result = translator.translate_agent('AAA')
    assert result == 'move_forward', f"Expected 'move_forward', got {result}"
    print("  [PASS] Agent translation works")
    
    # Test world table translation
    result = translator.translate_world('GAA')
    assert result == 'increase_resources', f"Expected 'increase_resources', got {result}"
    print("  [PASS] World translation works")
    
    print("  PASSED\n")


def test_degeneracy():
    """
    Test degeneracy - the CRITICAL feature.
    
    Verify that multiple different codons produce the same output,
    ensuring mutational robustness.
    """
    print("Test 2: Degeneracy Verification (CRITICAL)")
    translator = CodonTranslator()
    
    # Test agent table degeneracy
    degenerate_pairs = [
        ('AAA', 'AAT', 'move_forward'),
        ('ACA', 'ACT', 'turn_left'),
        ('AGA', 'AGT', 'consume_energy'),
        ('ATA', 'ATT', 'store_energy'),
        ('CAA', 'CAT', 'reproduce'),
        ('CCA', 'CCT', 'sense_environment'),
    ]
    
    print("  Agent Table Degeneracy:")
    for codon1, codon2, expected in degenerate_pairs:
        result1 = translator.translate_agent(codon1)
        result2 = translator.translate_agent(codon2)
        assert result1 == result2 == expected, \
            f"Degeneracy failed: {codon1}={result1}, {codon2}={result2}, expected={expected}"
        print(f"    [PASS] '{codon1}' and '{codon2}' both produce '{expected}'")
    
    # Test world table degeneracy
    degenerate_pairs = [
        ('GAA', 'GAT', 'increase_resources'),
        ('GCA', 'GCT', 'decrease_resources'),
        ('GGA', 'GGT', 'raise_temperature'),
        ('GTA', 'GTT', 'lower_temperature'),
        ('TAA', 'TAT', 'expand_space'),
        ('TCA', 'TCT', 'increase_mutation'),
    ]
    
    print("\n  World Table Degeneracy:")
    for codon1, codon2, expected in degenerate_pairs:
        result1 = translator.translate_world(codon1)
        result2 = translator.translate_world(codon2)
        assert result1 == result2 == expected, \
            f"Degeneracy failed: {codon1}={result1}, {codon2}={result2}, expected={expected}"
        print(f"    [PASS] '{codon1}' and '{codon2}' both produce '{expected}'")
    
    print("  PASSED\n")


def test_sequence_translation():
    """Test translation of codon sequences."""
    print("Test 3: Sequence Translation")
    translator = CodonTranslator()
    
    # Test with agent sequence
    sequence = 'AAAAATACA'
    result = translator.translate_sequence(sequence, 'agent')
    expected = ['move_forward', 'move_forward', 'turn_left']
    assert result == expected, f"Expected {expected}, got {result}"
    print(f"  [PASS] Sequence '{sequence}' correctly translated to {result}")
    
    # Test with world sequence
    sequence = 'GAAGCTGGA'
    result = translator.translate_sequence(sequence, 'world')
    expected = ['increase_resources', 'decrease_resources', 'raise_temperature']
    assert result == expected, f"Expected {expected}, got {result}"
    print(f"  [PASS] Sequence '{sequence}' correctly translated to {result}")
    
    print("  PASSED\n")


def test_invalid_codons():
    """Test handling of invalid codons."""
    print("Test 4: Invalid Codon Handling")
    translator = CodonTranslator()
    
    # Test invalid length
    result = translator.translate_agent('AA')
    assert result is None, "Should return None for invalid length"
    print("  [PASS] Correctly handles too-short codon")
    
    # Test invalid characters
    result = translator.translate_agent('AXZ')
    assert result is None, "Should return None for invalid characters"
    print("  [PASS] Correctly handles invalid characters")
    
    # Test unknown codon (valid format but not in table)
    result = translator.translate_agent('TTT')
    assert result is None, "Should return None for unknown codon"
    print("  [PASS] Correctly handles unknown codon")
    
    # Test invalid sequence (not multiple of 3)
    result = translator.translate_sequence('AAAA', 'agent')
    assert result is None, "Should return None for invalid sequence length"
    print("  [PASS] Correctly handles invalid sequence length")
    
    print("  PASSED\n")


def test_get_degenerate_codons():
    """Test retrieval of all degenerate codons for an instruction."""
    print("Test 5: Degenerate Codon Retrieval")
    translator = CodonTranslator()
    
    # Test agent instruction
    codons = translator.get_degenerate_codons('move_forward', 'agent')
    assert set(codons) == {'AAA', 'AAT'}, f"Expected {{'AAA', 'AAT'}}, got {set(codons)}"
    print(f"  [PASS] 'move_forward' has degenerate codons: {codons}")
    
    # Test world instruction
    codons = translator.get_degenerate_codons('increase_resources', 'world')
    assert set(codons) == {'GAA', 'GAT'}, f"Expected {{'GAA', 'GAT'}}, got {set(codons)}"
    print(f"  [PASS] 'increase_resources' has degenerate codons: {codons}")
    
    print("  PASSED\n")


def test_degeneracy_stats():
    """Test degeneracy statistics calculation."""
    print("Test 6: Degeneracy Statistics")
    translator = CodonTranslator()
    
    stats = translator.get_degeneracy_stats()
    
    # Check agent table stats
    agent_stats = stats['agent_table']
    assert agent_stats['total_codons'] == 12, "Agent table should have 12 codons"
    assert agent_stats['unique_instructions'] == 6, "Agent table should have 6 unique instructions"
    assert agent_stats['average_degeneracy'] == 2.0, "Average degeneracy should be 2.0"
    print(f"  [PASS] Agent table: {agent_stats['total_codons']} codons, "
          f"{agent_stats['unique_instructions']} instructions, "
          f"avg degeneracy {agent_stats['average_degeneracy']:.1f}")
    
    # Check world table stats
    world_stats = stats['world_table']
    assert world_stats['total_codons'] == 12, "World table should have 12 codons"
    assert world_stats['unique_instructions'] == 6, "World table should have 6 unique instructions"
    assert world_stats['average_degeneracy'] == 2.0, "Average degeneracy should be 2.0"
    print(f"  [PASS] World table: {world_stats['total_codons']} codons, "
          f"{world_stats['unique_instructions']} instructions, "
          f"avg degeneracy {world_stats['average_degeneracy']:.1f}")
    
    print("  PASSED\n")


def test_case_insensitivity():
    """Test that translation is case-insensitive."""
    print("Test 7: Case Insensitivity")
    translator = CodonTranslator()
    
    # Test lowercase
    result1 = translator.translate_agent('aaa')
    result2 = translator.translate_agent('AAA')
    assert result1 == result2 == 'move_forward', "Should handle lowercase"
    print("  [PASS] Lowercase codons work correctly")
    
    # Test mixed case
    result = translator.translate_agent('AaA')
    assert result == 'move_forward', "Should handle mixed case"
    print("  [PASS] Mixed case codons work correctly")
    
    print("  PASSED\n")


def run_all_tests():
    """Run all tests and report results."""
    print("=" * 60)
    print("CodonTranslator Test Suite")
    print("Testing Phase 1.1: Foundational Genetic Architecture")
    print("=" * 60)
    print()
    
    tests = [
        test_basic_translation,
        test_degeneracy,
        test_sequence_translation,
        test_invalid_codons,
        test_get_degenerate_codons,
        test_degeneracy_stats,
        test_case_insensitivity,
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
        print("\nDegeneracy Verification Summary:")
        print("  - Multiple codons successfully map to the same instructions")
        print("  - Mutational robustness is implemented correctly")
        print("  - Both agent_table and world_table exhibit degeneracy")
        print("\nPhase 1.1 (Foundational Genetic Architecture) is COMPLETE!")
        return 0
    else:
        print(f"\n[FAILED] {failed} test(s) failed")
        return 1


if __name__ == '__main__':
    exit_code = run_all_tests()
    sys.exit(exit_code)
