"""
CARP Interaction Handler - Track 3 Enhanced

Trait-based predator-prey interactions using behavioral traits from Track 2.
"""

import random
import math
from typing import List, Tuple, Optional


class InteractionHandler:
    """
    Handles predator-prey interactions with trait-based mechanics.
    
    Track 3 Enhancement:
    - Capture probability based on behavioral traits
    - Energy transfer efficiency based on traits
    - Co-evolutionary pressure between strategies
    """
    
    def __init__(self, 
                 capture_distance: float = 0.1,
                 base_capture_prob: float = 0.3,
                 base_energy_transfer: float = 0.4):
        """
        Initialize interaction handler.
        
        Args:
            capture_distance: Max distance for capture attempt
            base_capture_prob: Base probability of successful capture
            base_energy_transfer: Base energy transfer rate (0-1)
        """
        self.capture_distance = capture_distance
        self.base_capture_prob = base_capture_prob
        self.base_energy_transfer = base_energy_transfer
        
        # Track statistics
        self.total_encounters = 0
        self.successful_captures = 0
        self.total_energy_transferred = 0.0
    
    def calculate_capture_probability(self, predator, forager) -> float:
        """
        Calculate capture probability based on behavioral traits.
        
        Predator advantages:
        - High aggression → +capture chance
        - High risk_taking → +engagement willingness
        
        Forager advantages:
        - High exploration → +evasion ability
        - Low risk_taking → +flee success
        
        Args:
            predator: Predator agent
            forager: Forager agent
            
        Returns:
            Capture probability [0, 1]
        """
        prob = self.base_capture_prob
        
        # Predator modifiers (increase capture chance)
        if hasattr(predator, 'behavioral_traits'):
            aggression_bonus = predator.behavioral_traits.get('aggression', 0.5) * 0.3
            risk_bonus = predator.behavioral_traits.get('risk_taking', 0.5) * 0.2
            prob += aggression_bonus + risk_bonus
        
        # Forager modifiers (decrease capture chance)
        if hasattr(forager, 'behavioral_traits'):
            evasion_penalty = forager.behavioral_traits.get('exploration', 0.5) * 0.25
            flee_penalty = (1.0 - forager.behavioral_traits.get('risk_taking', 0.5)) * 0.15
            prob -= (evasion_penalty + flee_penalty)
        
        # Clamp to [0, 1]
        return max(0.0, min(1.0, prob))
    
    def calculate_energy_transfer(self, predator, forager) -> float:
        """
        Calculate energy transfer efficiency based on traits.
        
        Predator advantages:
        - High learning_rate → better energy extraction
        
        Forager advantages:
        - High social_tendency → group defense reduces transfer
        
        Args:
            predator: Predator agent
            forager: Forager agent
            
        Returns:
            Energy transfer rate [0.2, 0.6]
        """
        transfer_rate = self.base_energy_transfer
        
        # Predator modifiers (increase transfer)
        if hasattr(predator, 'behavioral_traits'):
            learning_bonus = predator.behavioral_traits.get('learning_rate', 0.5) * 0.2
            transfer_rate += learning_bonus
        
        # Forager modifiers (decrease transfer)
        if hasattr(forager, 'behavioral_traits'):
            social_penalty = forager.behavioral_traits.get('social_tendency', 0.5) * 0.15
            transfer_rate -= social_penalty
        
        # Clamp to reasonable range
        return max(0.2, min(0.6, transfer_rate))
    
    def handle_predator_behavior(self, predator, population: List) -> Optional[Tuple[str, float]]:
        """
        Handle predator hunting behavior.
        
        Args:
            predator: Predator agent
            population: All agents in population
            
        Returns:
            Tuple of (forager_id, energy_gained) if capture successful, None otherwise
        """
        from .species import Species
        
        # Find nearby foragers
        foragers = [a for a in population 
                   if hasattr(a, 'species') and a.species == Species.FORAGER 
                   and a.id != predator.id]
        
        if not foragers:
            return None
        
        # Pick random nearby forager
        target = random.choice(foragers)
        
        # Calculate capture probability
        capture_prob = self.calculate_capture_probability(predator, target)
        
        self.total_encounters += 1
        
        # Attempt capture
        if random.random() < capture_prob:
            # Successful capture!
            transfer_rate = self.calculate_energy_transfer(predator, target)
            energy_transferred = target.energy * transfer_rate
            
            # Transfer energy
            target.energy -= energy_transferred
            predator.energy += energy_transferred
            
            # Track statistics
            self.successful_captures += 1
            self.total_energy_transferred += energy_transferred
            
            return (target.id, energy_transferred)
        
        return None
    
    def handle_forager_behavior(self, forager, population: List) -> bool:
        """
        Handle forager evasion behavior.
        
        Currently passive - foragers rely on their traits for evasion.
        Future: Could add active evasion strategies.
        
        Args:
            forager: Forager agent
            population: All agents in population
            
        Returns:
            True if forager took evasive action
        """
        # Passive evasion - traits handle it in capture probability
        return False
    
    def get_statistics(self) -> dict:
        """Get interaction statistics."""
        capture_rate = (self.successful_captures / self.total_encounters 
                       if self.total_encounters > 0 else 0.0)
        
        return {
            'total_encounters': self.total_encounters,
            'successful_captures': self.successful_captures,
            'capture_rate': capture_rate,
            'total_energy_transferred': self.total_energy_transferred,
            'avg_energy_per_capture': (self.total_energy_transferred / self.successful_captures
                                      if self.successful_captures > 0 else 0.0)
        }
    
    def reset_statistics(self):
        """Reset interaction statistics."""
        self.total_encounters = 0
        self.successful_captures = 0
        self.total_energy_transferred = 0.0
