"""
Interaction Handler - Minimal CARP Implementation

Handles predator-prey interactions: detection, chase, evade, capture.
"""

import random
from typing import List, Tuple, Optional
from .species import Species, SpeciesTraits


class InteractionHandler:
    """
    Manages predator-prey interactions.
    
    Simple mechanics:
    - Predators detect and chase nearest forager
    - Foragers detect and evade nearest predator
    - Capture occurs if predator within capture distance
    """
    
    def __init__(self, capture_distance: float = 0.1, 
                 capture_efficiency: float = 0.6,
                 energy_transfer_rate: float = 0.4):
        """
        Initialize interaction handler.
        
        Args:
            capture_distance: Distance for successful capture
            capture_efficiency: Probability of successful capture
            energy_transfer_rate: Fraction of forager energy transferred
        """
        self.capture_distance = capture_distance
        self.capture_efficiency = capture_efficiency
        self.energy_transfer_rate = energy_transfer_rate
        
        # Statistics
        self.total_encounters = 0
        self.successful_captures = 0
        self.successful_evasions = 0
    
    def detect_nearby_agents(self, agent, population, detection_range: float) -> List[Tuple]:
        """
        Detect agents within detection range.
        
        Args:
            agent: Agent doing the detecting
            population: All agents
            detection_range: Maximum detection distance
            
        Returns:
            List of (other_agent, distance) tuples
        """
        nearby = []
        
        for other in population:
            if other.id == agent.id:
                continue
            
            # Simple distance calculation (agents have no position yet)
            # For minimal implementation, use random distance as proxy
            distance = random.random()  # Placeholder
            
            if distance < detection_range:
                nearby.append((other, distance))
        
        return nearby
    
    def handle_predator_behavior(self, predator, population) -> Optional[float]:
        """
        Handle predator behavior: detect and chase foragers.
        
        Args:
            predator: Predator agent
            population: All agents
            
        Returns:
            Energy gained from successful capture, or None
        """
        if not hasattr(predator, 'species_traits'):
            return None
        
        traits = predator.species_traits
        
        # Detect nearby foragers
        nearby = self.detect_nearby_agents(predator, population, traits.detection_range)
        foragers_nearby = [(a, d) for a, d in nearby 
                          if hasattr(a, 'species') and a.species == Species.FORAGER]
        
        if not foragers_nearby:
            return None
        
        # Chase nearest forager
        nearest_forager, distance = min(foragers_nearby, key=lambda x: x[1])
        
        # Attempt capture if close enough
        if distance < self.capture_distance:
            self.total_encounters += 1
            
            # Capture attempt
            if random.random() < self.capture_efficiency:
                # Successful capture
                self.successful_captures += 1
                
                # Transfer energy from forager
                if hasattr(nearest_forager, 'resource_energy'):
                    energy_gained = nearest_forager.resource_energy * self.energy_transfer_rate
                    nearest_forager.resource_energy *= (1 - self.energy_transfer_rate)
                    return energy_gained
        
        return None
    
    def handle_forager_behavior(self, forager, population) -> bool:
        """
        Handle forager behavior: detect and evade predators.
        
        Args:
            forager: Forager agent
            population: All agents
            
        Returns:
            True if successfully evaded, False otherwise
        """
        if not hasattr(forager, 'species_traits'):
            return False
        
        traits = forager.species_traits
        
        # Detect nearby predators
        nearby = self.detect_nearby_agents(forager, population, traits.detection_range)
        predators_nearby = [(a, d) for a, d in nearby 
                           if hasattr(a, 'species') and a.species == Species.PREDATOR]
        
        if not predators_nearby:
            return False
        
        # Evade nearest predator
        nearest_predator, distance = min(predators_nearby, key=lambda x: x[1])
        
        if distance < self.capture_distance * 1.5:  # Danger zone
            # Evasion attempt
            evasion_chance = 0.4  # Base evasion chance
            if random.random() < evasion_chance:
                self.successful_evasions += 1
                return True
        
        return False
    
    def get_statistics(self) -> dict:
        """Get interaction statistics."""
        return {
            'total_encounters': self.total_encounters,
            'successful_captures': self.successful_captures,
            'successful_evasions': self.successful_evasions,
            'capture_rate': self.successful_captures / max(self.total_encounters, 1)
        }
