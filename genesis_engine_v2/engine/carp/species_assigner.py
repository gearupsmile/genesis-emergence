"""
Species Assigner - CARP Minimal Implementation

Assigns species to agents maintaining 70/30 forager/predator ratio.
"""

import random
from typing import List, Dict
from .species import Species, SpeciesTraits


class SpeciesAssigner:
    """
    Manages species assignment to maintain population balance.
    
    Ensures 70% foragers, 30% predators across generations.
    """
    
    def __init__(self, forager_ratio: float = 0.7):
        """
        Initialize species assigner.
        
        Args:
            forager_ratio: Fraction of population that should be foragers
        """
        self.forager_ratio = forager_ratio
        self.predator_ratio = 1.0 - forager_ratio
        
        # Pre-load species traits for efficiency
        self.species_traits = {
            Species.FORAGER: SpeciesTraits.get_forager_traits(),
            Species.PREDATOR: SpeciesTraits.get_predator_traits()
        }
        
        # Track assignments
        self.assignments = {}  # agent_id -> species
    
    def assign_species_to_population(self, population: List) -> Dict[str, int]:
        """
        Assign species to population maintaining target ratio.
        
        Track 3 Fix: Properly sets agent.species attribute
        
        Args:
            population: List of agents
            
        Returns:
            Dict with species counts
        """
        if not population:
            return {'forager': 0, 'predator': 0}
        
        # Calculate target counts
        total = len(population)
        target_foragers = int(total * self.forager_ratio)
        target_predators = total - target_foragers
        
        # Shuffle population for random assignment
        shuffled = population.copy()
        random.shuffle(shuffled)
        
        # Assign species
        forager_count = 0
        predator_count = 0
        
        for i, agent in enumerate(shuffled):
            if i < target_foragers:
                # Assign as forager
                agent.species = Species.FORAGER
                agent.species_traits = self.species_traits[Species.FORAGER].copy()
                forager_count += 1
            else:
                # Assign as predator
                agent.species = Species.PREDATOR
                agent.species_traits = self.species_traits[Species.PREDATOR].copy()
                predator_count += 1
        
        return {
            'forager': forager_count,
            'predator': predator_count
        }
    
    def assign_species_to_offspring(self, parent):
        """
        Assign species to offspring based on parent.
        
        Args:
            parent: Parent agent
            
        Returns:
            Species for offspring
        """
        # Offspring inherit parent's species
        if hasattr(parent, 'species'):
            return parent.species
        
        # Fallback: random assignment
        return Species.FORAGER if random.random() < self.forager_ratio else Species.PREDATOR
    
    def get_species_counts(self, population):
        """Get current species distribution."""
        foragers = sum(1 for a in population 
                      if hasattr(a, 'species') and a.species == Species.FORAGER)
        predators = sum(1 for a in population 
                       if hasattr(a, 'species') and a.species == Species.PREDATOR)
        
        return {
            'foragers': foragers,
            'predators': predators,
            'total': len(population)
        }
