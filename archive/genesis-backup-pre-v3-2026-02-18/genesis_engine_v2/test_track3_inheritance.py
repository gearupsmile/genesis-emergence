"""
Track 3 Phase 1: Species Inheritance Test

Tests that species is properly inherited by offspring.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from engine.evolvable_genome import EvolvableGenome
from engine.structurally_evolvable_agent import StructurallyEvolvableAgent
from engine.carp.species import Species


def test_species_inheritance():
    """Test species inheritance across generations."""
    print("=" * 70)
    print("TRACK 3 PHASE 1: SPECIES INHERITANCE TEST")
    print("=" * 70)
    print()
    
    # Test 1: Species assigned to parent
    print("Test 1: Species Assignment")
    genome = EvolvableGenome(['AAA', 'CAA', 'GAA'])
    parent = StructurallyEvolvableAgent(genome, species=Species.PREDATOR)
    print(f"  Parent species: {parent.species}")
    print(f"  Expected: {Species.PREDATOR}")
    
    if parent.species == Species.PREDATOR:
        print(f"  Result: PASS [OK]")
    else:
        print(f"  Result: FAIL [X]")
        return False
    print()
    
    # Test 2: Species inherited by offspring
    print("Test 2: Species Inheritance")
    child = parent.reproduce(mutation_rate=0.3)
    print(f"  Parent species: {parent.species}")
    print(f"  Child species: {child.species}")
    print(f"  Inherited: {child.species == parent.species}")
    
    if child.species == parent.species:
        print(f"  Result: PASS [OK]")
    else:
        print(f"  Result: FAIL [X]")
        return False
    print()
    
    # Test 3: Multi-generation inheritance
    print("Test 3: Multi-Generation Inheritance")
    lineage = [parent]
    for gen in range(5):
        child = lineage[-1].reproduce(mutation_rate=0.3)
        lineage.append(child)
    
    print(f"  Generation 0 (parent): {lineage[0].species}")
    for i in range(1, len(lineage)):
        print(f"  Generation {i}: {lineage[i].species}")
    
    all_same = all(agent.species == Species.PREDATOR for agent in lineage)
    print(f"  All generations same species: {all_same}")
    
    if all_same:
        print(f"  Result: PASS [OK]")
    else:
        print(f"  Result: FAIL [X]")
        return False
    print()
    
    # Test 4: Forager species inheritance
    print("Test 4: Forager Species Inheritance")
    forager_parent = StructurallyEvolvableAgent(genome, species=Species.FORAGER)
    forager_child = forager_parent.reproduce(mutation_rate=0.3)
    print(f"  Parent species: {forager_parent.species}")
    print(f"  Child species: {forager_child.species}")
    
    if forager_child.species == Species.FORAGER:
        print(f"  Result: PASS [OK]")
    else:
        print(f"  Result: FAIL [X]")
        return False
    print()
    
    # Test 5: Species traits inherited
    print("Test 5: Species Traits Inheritance")
    parent.species_traits = {'speed': 0.8, 'strength': 0.6}
    child_with_traits = parent.reproduce(mutation_rate=0.3)
    print(f"  Parent traits: {parent.species_traits}")
    print(f"  Child traits: {child_with_traits.species_traits}")
    print(f"  Traits inherited: {child_with_traits.species_traits == parent.species_traits}")
    
    if child_with_traits.species_traits == parent.species_traits:
        print(f"  Result: PASS [OK]")
    else:
        print(f"  Result: FAIL [X]")
        return False
    print()
    
    print("=" * 70)
    print("[SUCCESS] All species inheritance tests passed!")
    print("=" * 70)
    print()
    print("Summary:")
    print("  - Species assigned to agents")
    print("  - Species inherited by offspring")
    print("  - Multi-generation inheritance working")
    print("  - Both forager and predator species work")
    print("  - Species traits inherited")
    
    return True


if __name__ == '__main__':
    try:
        success = test_species_inheritance()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
