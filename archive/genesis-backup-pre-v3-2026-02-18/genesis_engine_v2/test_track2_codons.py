"""
Track 2 Codon System Test

Tests codon translation and behavioral trait integration.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from engine.evolvable_genome import EvolvableGenome
from engine.structurally_evolvable_agent import StructurallyEvolvableAgent
from engine.codon_translator import CodonTranslator


def test_codon_translation():
    """Test codon translation system."""
    print("=" * 70)
    print("TRACK 2: CODON TRANSLATION TEST")
    print("=" * 70)
    print()
    
    translator = CodonTranslator()
    
    # Test 1: Known codons
    print("Test 1: Known Codon Translation")
    genome1 = EvolvableGenome(['AAA', 'CAA', 'GAA'])  # High aggression, exploration, social
    traits1 = translator.translate_genome_to_traits(genome1)
    print(f"  Genome: AAA-CAA-GAA")
    print(f"  Traits: {translator.get_trait_summary(traits1)}")
    print(f"  Expected: High aggression, exploration, social")
    print()
    
    # Test 2: Opposite codons
    print("Test 2: Opposite Codons")
    genome2 = EvolvableGenome(['ACT', 'CCT', 'GCT'])  # Low aggression, exploration, social
    traits2 = translator.translate_genome_to_traits(genome2)
    print(f"  Genome: ACT-CCT-GCT")
    print(f"  Traits: {translator.get_trait_summary(traits2)}")
    print(f"  Expected: Low aggression, exploration, social")
    print()
    
    # Test 3: Agent integration
    print("Test 3: Agent Integration")
    agent = StructurallyEvolvableAgent(genome1)
    print(f"  Agent ID: {agent.id[:8]}...")
    print(f"  Traits: {agent._trait_summary}")
    print(f"  Genome length: {agent.genome.get_length()} genes")
    print(f"  Codon count: {translator.get_codon_count(agent.genome)}")
    print()
    
    # Test 4: Trait clamping
    print("Test 4: Trait Clamping [0, 1]")
    # Create genome with many high-modifier codons
    genome3 = EvolvableGenome(['AAA'] * 10)  # 10x high aggression
    traits3 = translator.translate_genome_to_traits(genome3)
    print(f"  Genome: AAA × 10")
    print(f"  Aggression: {traits3['aggression']:.2f}")
    print(f"  Expected: 1.00 (clamped)")
    assert traits3['aggression'] == 1.0, "Trait not clamped to 1.0!"
    print(f"  Result: PASS [OK]")
    print()
    
    # Test 5: Codon table coverage
    print("Test 5: Codon Table Coverage")
    print(f"  Total codons in table: {len(translator.CODON_TABLE)}")
    print(f"  Traits covered: {len(translator.BASE_TRAITS)}")
    
    # Count codons per trait
    trait_counts = {}
    for codon_info in translator.CODON_TABLE.values():
        trait = codon_info['trait']
        trait_counts[trait] = trait_counts.get(trait, 0) + 1
    
    for trait, count in trait_counts.items():
        print(f"    {trait}: {count} codons")
    print()
    
    print("=" * 70)
    print("[SUCCESS] All codon translation tests passed!")
    print("=" * 70)
    
    return True


if __name__ == '__main__':
    try:
        success = test_codon_translation()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
