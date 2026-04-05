"""
CARP (Co-Evolutionary Arms Race) Module - Minimal Implementation

Implements basic predator-prey dynamics to test if co-evolution
creates behavioral diversity where environmental pressures failed.

Step 1: Minimal validation (4 days)
"""

__all__ = ['Species', 'SpeciesTraits', 'InteractionHandler', 'SpeciesAssigner']

from .species import Species, SpeciesTraits
from .interactions import InteractionHandler
from .species_assigner import SpeciesAssigner
