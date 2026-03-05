"""
StructurallyEvolvableAgent - Agent with evolvable genome structure

Track 2: Enhanced with behavioral traits from codon translation
Track 3: Enhanced with species identity and inheritance
"""

import uuid
import random
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
    
    def __init__(self, genome: EvolvableGenome, species: Optional[str] = None,
                 lineage_id: Optional[str] = None):
        """
        Initialize agent with genome and optional species.

        Args:
            genome: EvolvableGenome instance
            species: Optional species identifier ('forager' or 'predator')
            lineage_id: Stable identifier shared across all descendants of a lineage.
                        If None, this agent is a founder and gets a fresh UUID.
        """
        self.genome = genome
        self.id = str(uuid.uuid4())          # Unique per-agent UUID
        self.age = 0

        # LINEAGE TRACKING: shared ID across parent → offspring chains
        # Enables continuous action-history accumulation across generations.
        self.lineage_id = lineage_id if lineage_id is not None else str(uuid.uuid4())

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

        Track 3: Species is INHERITED by offspring.
        Lineage Tracking: lineage_id is INHERITED so action history is continuous.

        Args:
            mutation_rate: Probability of mutations

        Returns:
            New StructurallyEvolvableAgent with mutated genome, SAME species, SAME lineage.
        """
        child_genome = self.genome.create_offspring(mutation_rate)

        child = StructurallyEvolvableAgent(
            genome=child_genome,
            species=self.species,         # Inherit species
            lineage_id=self.lineage_id    # INHERIT lineage_id for continuous history
        )

        child.species_traits = self.species_traits
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
    
    # Secretion Constants (Feature 1.3)
    SECRETION_COST = 0.05
    SECRETION_AMOUNT = 0.5
    
    def secrete(self, substrate, amount: Optional[float] = None) -> None:
        """
        Feature 1.3: Agent secretes chemical into local environment (3x3).
        
        Args:
            substrate: Substrate instance
            amount: Amount to secrete (default: SECRETION_AMOUNT)
        """
        amount = amount if amount is not None else self.SECRETION_AMOUNT
        
        # Deduct metabolic cost
        self.energy -= self.SECRETION_COST
        
        # Get position (assuming agent has x, y or needs to be passed)
        # Note: StructurallyEvolvableAgent doesn't store x,y directly in __init__
        # x,y are managed by SpatialEnvironment or KernelWorld?
        # Let's assume x,y are attributes set by the environment or passed in.
        # Since this method is called from loop, we might need x,y as args if not stored.
        # But for now, let's assume self.x and self.y exist (they should for spatial simulation)
        
        if not hasattr(self, 'x') or not hasattr(self, 'y'):
            # If position not stored on agent, we can't secrete spatially
            # Fallback or error?
            # Let's assume they ARE stored for now, and check where they are set.
            return

        x, y = int(self.x), int(self.y)
        
        # Feature 4: Use substrate method to respect Sham Mode
        substrate.deposit_secretion(x, y, amount)
        
        # Clamping handled in substrate update? Or here?
        # Let's clamp here too just in case
        # substrate.S[ny, nx] = min(1.0, substrate.S[ny, nx]) 
        # (Actually, better to clamp in loop or just let diffusion clamp)
        
    def step(self, substrate) -> str:
        """
        Feature 1.4: Main agent decision loop.
        Current implementation: Random movement and probabilistic secretion.
        
        Returns:
            Action code ('S', 'M', 'I')
        """
        action = 'I'
        
        # 1. Secretion (Probability 0.1 as per request)
        if random.random() < 0.1:
            self.secrete(substrate)
            action = 'S'
            
        # 2. Movement (Random for now)
        # Ensure we have x,y
        if hasattr(self, 'x') and hasattr(self, 'y'):
            # Random walk
            dx = random.choice([-1, 0, 1])
            dy = random.choice([-1, 0, 1])
            
            if dx != 0 or dy != 0:
                self.x = (self.x + dx) % substrate.width
                self.y = (self.y + dy) % substrate.height
                if action == 'I': action = 'M' # S overrides M for now in trace, or combined?
                # Let's prioritize Secretion as typically more significant, or generic 'A'
                # Simple priority: S > M > I
        else:
            # Initialize position if missing
            self.x = random.randint(0, substrate.width - 1)
            self.y = random.randint(0, substrate.height - 1)
            
        return action

    def __repr__(self) -> str:
        """String representation for debugging."""
        species_str = f", species={self.species}" if self.species else ""
        return (f"StructurallyEvolvableAgent(id={self.id[:8]}..., "
                f"genome_length={self.genome.get_length()}, "
                f"age={self.age}{species_str})")

