"""
Temporal Cycles - Week 3 Phase 3

Implements environmental variation over time through cyclical phases.
Prevents stagnation and drives temporal adaptation.

Design:
- 500-generation cycle with 3 phases
- Abundance (200 gens): Resources abundant, constraints relaxed
- Scarcity (200 gens): Resources scarce, constraints tight
- Shift (100 gens): Resource dominance swaps
"""

from typing import Dict, List
from dataclasses import dataclass


@dataclass
class EnvironmentalPhase:
    """
    Defines a phase in the temporal cycle.
    
    Attributes:
        name: Phase identifier
        duration: Length in generations
        resource_modifiers: Multipliers for each resource type
        constraint_modifier: Multiplier for energy constant
        color_code: Visual indicator for logs
    """
    name: str
    duration: int
    resource_modifiers: Dict[str, float]
    constraint_modifier: float
    color_code: str
    
    def get_log_prefix(self) -> str:
        """Get colored log prefix for this phase."""
        return f"[{self.name.upper()}]"


class TemporalEnvironment:
    """
    Manages temporal cycles and phase transitions.
    
    Creates environmental variation over time to prevent stagnation
    and drive temporal adaptation strategies.
    """
    
    def __init__(self, cycle_length: int = 500):
        """
        Initialize temporal environment with 3-phase cycle.
        
        Args:
            cycle_length: Total generations per cycle (default: 500)
        """
        self.cycle_length = cycle_length
        
        # Define 3 phases
        self.abundance_phase = EnvironmentalPhase(
            name="Abundance",
            duration=200,
            resource_modifiers={'A': 1.5, 'B': 1.5, 'C': 1.5},  # All resources abundant
            constraint_modifier=-0.1,  # Constraints relaxed by 10%
            color_code="GREEN"
        )
        
        self.scarcity_phase = EnvironmentalPhase(
            name="Scarcity",
            duration=200,
            resource_modifiers={'A': 0.5, 'B': 0.5, 'C': 0.5},  # All resources scarce
            constraint_modifier=0.1,  # Constraints tightened by 10%
            color_code="RED"
        )
        
        self.shift_phase = EnvironmentalPhase(
            name="Shift",
            duration=100,
            resource_modifiers={'A': 0.3, 'B': 1.0, 'C': 1.7},  # A↔C swap (A down, C up)
            constraint_modifier=0.0,  # Normal constraints
            color_code="YELLOW"
        )
        
        self.phases = [
            self.abundance_phase,
            self.scarcity_phase,
            self.shift_phase
        ]
        
        # State tracking
        self.current_phase_index = 0
        self.generations_in_phase = 0
        self.total_generations = 0
        self.phase_transition_count = 0
        
        # Track phase history
        self.phase_history: List[Dict] = []
    
    def update_phase(self, generation: int) -> bool:
        """
        Update phase based on current generation.
        
        Args:
            generation: Current generation number
            
        Returns:
            True if phase transition occurred, False otherwise
        """
        self.total_generations = generation
        self.generations_in_phase += 1
        
        current_phase = self.phases[self.current_phase_index]
        
        # Check if phase should transition
        if self.generations_in_phase >= current_phase.duration:
            # Transition to next phase
            self.current_phase_index = (self.current_phase_index + 1) % len(self.phases)
            self.generations_in_phase = 0
            self.phase_transition_count += 1
            
            # Log transition
            new_phase = self.phases[self.current_phase_index]
            self.phase_history.append({
                'generation': generation,
                'phase': new_phase.name,
                'transition_count': self.phase_transition_count
            })
            
            return True
        
        return False
    
    def get_current_phase(self) -> EnvironmentalPhase:
        """Get the current environmental phase."""
        return self.phases[self.current_phase_index]
    
    def get_phase_progress(self) -> float:
        """
        Get progress through current phase.
        
        Returns:
            Progress as fraction (0.0 to 1.0)
        """
        current_phase = self.get_current_phase()
        return self.generations_in_phase / current_phase.duration
    
    def get_cycle_progress(self) -> float:
        """
        Get progress through full cycle.
        
        Returns:
            Progress as fraction (0.0 to 1.0)
        """
        position_in_cycle = self.total_generations % self.cycle_length
        return position_in_cycle / self.cycle_length
    
    def apply_resource_modifiers(self, resource_system):
        """
        Apply current phase's resource modifiers.
        
        Args:
            resource_system: ResourceNicheSystem instance
        """
        current_phase = self.get_current_phase()
        
        # Apply modifiers to resource abundance
        for resource_type, multiplier in current_phase.resource_modifiers.items():
            if resource_type in resource_system.resources:
                resource = resource_system.resources[resource_type]
                # Modify current availability (not base abundance)
                base_abundance = resource.abundance
                resource_system.current_availability[resource_type] = base_abundance * multiplier
    
    def get_constraint_modifier(self) -> float:
        """
        Get current phase's constraint modifier.
        
        Returns:
            Modifier value (e.g., -0.1 for 10% relaxation, +0.1 for 10% tightening)
        """
        current_phase = self.get_current_phase()
        return current_phase.constraint_modifier
    
    def get_statistics(self) -> Dict:
        """Get temporal environment statistics."""
        current_phase = self.get_current_phase()
        
        return {
            'current_phase': current_phase.name,
            'generations_in_phase': self.generations_in_phase,
            'phase_progress': self.get_phase_progress(),
            'cycle_progress': self.get_cycle_progress(),
            'transition_count': self.phase_transition_count,
            'total_generations': self.total_generations
        }
    
    def __repr__(self) -> str:
        """String representation."""
        current_phase = self.get_current_phase()
        return (f"TemporalEnvironment(phase={current_phase.name}, "
                f"gen_in_phase={self.generations_in_phase}/{current_phase.duration}, "
                f"transitions={self.phase_transition_count})")
