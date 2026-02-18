"""
StructurallyEvolvableAgent - Agent with evolvable genome structure

Track 2: Enhanced with behavioral traits from codon translation
Track 3: Enhanced with species identity and inheritance
"""

import uuid
from typing import Dict, Optional
from .evolvable_genome import EvolvableGenome
from .linkage_structure import LinkageStructure
from .codon_translator import translate_genome, get_trait_summary


class StructurallyEvolvableAgent:
    """
    Agent with structurally evolvable genome.
    
    Track 2 Enhancement:
    - Behavioral traits derived from genome via codon translation
    - Traits: aggression, exploration, social_tendency, risk_taking, learning_rate
    
    Track 3 Enhancement:
    - Species identity (forager/predator)
    - Species inherited by offspring
    """
    
    def __init__(self, genome: EvolvableGenome, species: Optional[str] = None):
        """
        Initialize agent with genome and optional species.
        
        Args:
            genome: EvolvableGenome instance
            species: Optional species identifier ('forager' or 'predator')
        """
        self.genome = genome
        self.id = str(uuid.uuid4())
        self.age = 0
        
        # TRACK 2: Translate genome to behavioral traits
        self.behavioral_traits = translate_genome(genome)
        
        # Cache trait summary for logging
        self._trait_summary = get_trait_summary(self.behavioral_traits)
        
        # TRACK 3: Species identity
        self.species = species
        self.species_traits = {}  # Will be set by SpeciesAssigner
        
        # Energy for CARP interactions
        self.energy = 1.0
        
        # TRACK 2.2: Linkage Structure for building block discovery
        self.linkage_structure = LinkageStructure(genome_length=genome.get_length())
    
    def reproduce(self, mutation_rate: float = 0.1) -> 'StructurallyEvolvableAgent':
        """
        Create offspring with mutations.
        
        Track 3: Species is INHERITED by offspring (critical fix!)
        
        Args:
            mutation_rate: Probability of mutations
            
        Returns:
            New StructurallyEvolvableAgent with mutated genome and SAME species
        """
        # Create offspring genome (structural mutations)
        child_genome = self.genome.create_offspring(mutation_rate)
        
        # Create child agent with INHERITED SPECIES
        child = StructurallyEvolvableAgent(
            genome=child_genome,
            species=self.species  # CRITICAL: Inherit species from parent
        )
        
        # Inherit species traits (dataclass, just assign reference)
        child.species_traits = self.species_traits
        
        # Evolve linkage structure
        child.linkage_structure = self.linkage_structure.create_offspring(mutation_rate)
        
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
        species_str = f", species={self.species}" if self.species else ""
        return (f"StructurallyEvolvableAgent(id={self.id[:8]}..., "
                f"genome_length={self.genome.get_length()}, "
                f"age={self.age}{species_str})")
