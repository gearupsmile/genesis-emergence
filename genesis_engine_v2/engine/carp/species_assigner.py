"""
Species Assigner - CARP Minimal Implementation

Assigns species to agents maintaining 70/30 forager/predator ratio.
"""

import random
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
        
        # Track assignments
        self.assignments = {}  # agent_id -> species
    
    def assign_species_to_population(self, population):
        """
        Assign species to entire population.
        
        Args:
            population: List of agents
        """
        total = len(population)
        num_foragers = int(total * self.forager_ratio)
        
        # Shuffle population for random assignment
        shuffled = list(population)
        random.shuffle(shuffled)
        
        # Assign species
        for i, agent in enumerate(shuffled):
            if i < num_foragers:
                agent.species = Species.FORAGER
                agent.species_traits = SpeciesTraits.get_forager_traits()
            else:
                agent.species = Species.PREDATOR
                agent.species_traits = SpeciesTraits.get_predator_traits()
            
            self.assignments[agent.id] = agent.species
    
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
