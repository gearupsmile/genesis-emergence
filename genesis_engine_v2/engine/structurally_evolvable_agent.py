"""
StructurallyEvolvableAgent - Agent with evolvable genome structure

Track 2: Enhanced with behavioral traits from codon translation
"""

import uuid
from typing import Dict
from .evolvable_genome import EvolvableGenome
from .codon_translator import translate_genome, get_trait_summary


class StructurallyEvolvableAgent:
    """
    Agent with structurally evolvable genome.
    
    Track 2 Enhancement:
    - Behavioral traits derived from genome via codon translation
    - Traits: aggression, exploration, social_tendency, risk_taking, learning_rate
    """
    
    def __init__(self, genome: EvolvableGenome):
        """
        Initialize agent with genome.
        
        Args:
            genome: EvolvableGenome instance
        """
        self.genome = genome
        self.id = str(uuid.uuid4())
        self.age = 0
        
        # TRACK 2: Translate genome to behavioral traits
        self.behavioral_traits = translate_genome(genome)
        
        # Cache trait summary for logging
        self._trait_summary = get_trait_summary(self.behavioral_traits)
    
    def reproduce(self, mutation_rate: float = 0.1) -> 'StructurallyEvolvableAgent':
        """
        Create offspring with mutations.
        
        Args:
            mutation_rate: Probability of mutations
            
        Returns:
            New StructurallyEvolvableAgent with mutated genome
        """
        # Create offspring genome (structural mutations)
        child_genome = self.genome.create_offspring(mutation_rate)
        
        # Create child agent
        child = StructurallyEvolvableAgent(genome=child_genome)
        
        return child
    
    def to_dict(self) -> Dict:
        """Convert agent to dictionary for AIS integration."""
        return {
            'id': self.id,
            'relevance_score': 1.0,
            'age': self.age
        }
    
    def update_from_dict(self, data: Dict) -> None:
        """Update agent's AIS state from dictionary (in-place)."""
        if 'age' in data:
            self.age = data['age']
    
    def __repr__(self) -> str:
        """String representation for debugging."""
        return (f"StructurallyEvolvableAgent(id={self.id[:8]}..., "
                f"genome_length={self.genome.get_length()}, "
                f"age={self.age})")
