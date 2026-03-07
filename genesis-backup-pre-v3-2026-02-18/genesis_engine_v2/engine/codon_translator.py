"""
CodonTranslator - Track 2: Codon-Based Genetic System

Maps gene sequences (codons) to behavioral traits.
Provides structured genetic encoding for evolvable behaviors.
"""

from typing import Dict, List
import random


class CodonTranslator:
    """
    Translates gene sequences into behavioral trait values.
    
    Track 2 Enhancement:
    - Comprehensive codon table (48 codons)
    - 5 behavioral traits
    - Codon block structure (3 genes per block)
    """
    
    # Comprehensive codon table: 3-letter gene sequences → trait modifiers
    # Each codon affects one of 5 behavioral traits
    CODON_TABLE = {
        # Aggression trait (8 codons)
        'AAA': {'trait': 'aggression', 'modifier': +0.15},
        'AAC': {'trait': 'aggression', 'modifier': +0.10},
        'AAG': {'trait': 'aggression', 'modifier': +0.08},
        'AAT': {'trait': 'aggression', 'modifier': +0.05},
        'ACA': {'trait': 'aggression', 'modifier': -0.05},
        'ACC': {'trait': 'aggression', 'modifier': -0.08},
        'ACG': {'trait': 'aggression', 'modifier': -0.10},
        'ACT': {'trait': 'aggression', 'modifier': -0.15},
        
        # Exploration trait (8 codons)
        'CAA': {'trait': 'exploration', 'modifier': +0.15},
        'CAC': {'trait': 'exploration', 'modifier': +0.10},
        'CAG': {'trait': 'exploration', 'modifier': +0.08},
        'CAT': {'trait': 'exploration', 'modifier': +0.05},
        'CCA': {'trait': 'exploration', 'modifier': -0.05},
        'CCC': {'trait': 'exploration', 'modifier': -0.08},
        'CCG': {'trait': 'exploration', 'modifier': -0.10},
        'CCT': {'trait': 'exploration', 'modifier': -0.15},
        
        # Social tendency trait (8 codons)
        'GAA': {'trait': 'social_tendency', 'modifier': +0.15},
        'GAC': {'trait': 'social_tendency', 'modifier': +0.10},
        'GAG': {'trait': 'social_tendency', 'modifier': +0.08},
        'GAT': {'trait': 'social_tendency', 'modifier': +0.05},
        'GCA': {'trait': 'social_tendency', 'modifier': -0.05},
        'GCC': {'trait': 'social_tendency', 'modifier': -0.08},
        'GCG': {'trait': 'social_tendency', 'modifier': -0.10},
        'GCT': {'trait': 'social_tendency', 'modifier': -0.15},
        
        # Risk taking trait (8 codons)
        'TAA': {'trait': 'risk_taking', 'modifier': +0.15},
        'TAC': {'trait': 'risk_taking', 'modifier': +0.10},
        'TAG': {'trait': 'risk_taking', 'modifier': +0.08},
        'TAT': {'trait': 'risk_taking', 'modifier': +0.05},
        'TCA': {'trait': 'risk_taking', 'modifier': -0.05},
        'TCC': {'trait': 'risk_taking', 'modifier': -0.08},
        'TCG': {'trait': 'risk_taking', 'modifier': -0.10},
        'TCT': {'trait': 'risk_taking', 'modifier': -0.15},
        
        # Learning rate trait (16 codons)
        'AGA': {'trait': 'learning_rate', 'modifier': +0.12},
        'AGC': {'trait': 'learning_rate', 'modifier': +0.08},
        'AGG': {'trait': 'learning_rate', 'modifier': +0.06},
        'AGT': {'trait': 'learning_rate', 'modifier': +0.04},
        'CGA': {'trait': 'learning_rate', 'modifier': -0.04},
        'CGC': {'trait': 'learning_rate', 'modifier': -0.06},
        'CGG': {'trait': 'learning_rate', 'modifier': -0.08},
        'CGT': {'trait': 'learning_rate', 'modifier': -0.12},
        'GGA': {'trait': 'learning_rate', 'modifier': +0.10},
        'GGC': {'trait': 'learning_rate', 'modifier': +0.05},
        'GGG': {'trait': 'learning_rate', 'modifier': +0.03},
        'GGT': {'trait': 'learning_rate', 'modifier': +0.02},
        'TGA': {'trait': 'learning_rate', 'modifier': -0.02},
        'TGC': {'trait': 'learning_rate', 'modifier': -0.03},
        'TGG': {'trait': 'learning_rate', 'modifier': -0.05},
        'TGT': {'trait': 'learning_rate', 'modifier': -0.10},
    }
    
    # Base trait values (neutral starting point)
    BASE_TRAITS = {
        'aggression': 0.5,
        'exploration': 0.5,
        'social_tendency': 0.5,
        'risk_taking': 0.5,
        'learning_rate': 0.5
    }
    
    def translate_genome_to_traits(self, genome) -> Dict[str, float]:
        """
        Translate genome into behavioral trait values.
        
        Each gene in the genome is a 3-letter codon.
        Each codon modifies one behavioral trait.
        
        Args:
            genome: EvolvableGenome instance
            
        Returns:
            Dict mapping trait_name -> value in [0, 1]
        """
        # Start with base values
        traits = self.BASE_TRAITS.copy()
        
        # Get genes from genome (each gene is already a 3-letter codon)
        genes = genome.sequence if hasattr(genome, 'sequence') else []
        
        # Process each gene as a codon
        for gene in genes:
            if gene in self.CODON_TABLE:
                codon_info = self.CODON_TABLE[gene]
                trait_name = codon_info['trait']
                modifier = codon_info['modifier']
                
                # Apply modifier
                traits[trait_name] += modifier
        
        # Clamp all traits to [0, 1]
        for trait in traits:
            traits[trait] = max(0.0, min(1.0, traits[trait]))
        
        return traits
    
    def get_codon_count(self, genome) -> int:
        """Get number of codons in genome."""
        genes = genome.sequence if hasattr(genome, 'sequence') else []
        return len(genes)
    
    def get_trait_summary(self, traits: Dict[str, float]) -> str:
        """Get human-readable summary of traits."""
        return (f"Aggression: {traits['aggression']:.2f}, "
                f"Exploration: {traits['exploration']:.2f}, "
                f"Social: {traits['social_tendency']:.2f}, "
                f"Risk: {traits['risk_taking']:.2f}, "
                f"Learning: {traits['learning_rate']:.2f}")


# Singleton instance for easy access
_translator = CodonTranslator()


def translate_genome(genome) -> Dict[str, float]:
    """Convenience function to translate genome to traits."""
    return _translator.translate_genome_to_traits(genome)


def get_trait_summary(traits: Dict[str, float]) -> str:
    """Convenience function to get trait summary."""
    return _translator.get_trait_summary(traits)
