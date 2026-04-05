"""
Species System - Minimal CARP Implementation

Defines two co-evolving species: Foragers and Predators.
"""

from enum import Enum
from dataclasses import dataclass


class Species(Enum):
    """Agent species types."""
    FORAGER = "forager"
    PREDATOR = "predator"


@dataclass
class SpeciesTraits:
    """
    Species-specific attributes.
    
    Foragers: Acquire resources, evade predators
    Predators: Hunt foragers for energy
    """
    
    species: Species
    energy_from_resources: float
    energy_from_predation: float
    detection_range: float
    base_speed: float
    
    @staticmethod
    def get_forager_traits():
        """Get default forager traits."""
        return SpeciesTraits(
            species=Species.FORAGER,
            energy_from_resources=1.0,  # Full benefit from resources
            energy_from_predation=0.0,  # Can't hunt
            detection_range=0.2,  # Shorter detection
            base_speed=1.0  # Standard speed
        )
    
    @staticmethod
    def get_predator_traits():
        """Get default predator traits."""
        return SpeciesTraits(
            species=Species.PREDATOR,
            energy_from_resources=0.3,  # Reduced benefit from resources
            energy_from_predation=1.0,  # Full benefit from hunting
            detection_range=0.4,  # Longer detection
            base_speed=1.2  # Faster than foragers
        )
