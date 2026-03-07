"""
Behavioral Tracker - Action-Based Behavioral Signatures

Calculates 5D behavioral signatures from action history.
This replaces the structural signature approach.

Emergency Fix for Week 3: Measures BEHAVIOR not STRUCTURE
"""

import numpy as np
from typing import Dict
from .action_recorder import ActionRecorder, ActionHistory


class BehavioralTracker:
    """
    Tracks and analyzes agent behaviors over time.
    
    Computes action-based 5D behavioral signatures:
    1. Exploration aggressiveness
    2. Resource switching rate
    3. Risk-taking profile
    4. Environmental response time
    5. Constraint pressure tolerance
    """
    
    def __init__(self, window_size: int = 100):
        """
        Initialize behavioral tracker.
        
        Args:
            window_size: Number of generations for rolling window
        """
        self.action_recorder = ActionRecorder(window_size)
        self.window_size = window_size
    
    def calculate_behavioral_signature(self, agent_id: str) -> np.ndarray:
        """
        Calculate 5D action-based behavioral signature.
        
        Args:
            agent_id: Agent identifier
            
        Returns:
            5D numpy array, normalized to [0, 1]
        """
        history = self.action_recorder.get_history(agent_id)
        
        # Dimension 1: Exploration aggressiveness
        # (Currently simplified - would need actual movement tracking)
        exploration = self._calculate_exploration_aggressiveness(history)
        
        # Dimension 2: Resource switching rate
        switching = self._calculate_resource_switching_rate(history)
        
        # Dimension 3: Risk-taking profile
        risk = self._calculate_risk_taking_profile(history)
        
        # Dimension 4: Environmental response time
        response = self._calculate_response_time(history)
        
        # Dimension 5: Constraint pressure tolerance
        pressure = self._calculate_pressure_tolerance(history)
        
        signature = np.array([exploration, switching, risk, response, pressure])
        
        # Clip to [0, 1]
        signature = np.clip(signature, 0, 1)
        
        return signature
    
    def _calculate_exploration_aggressiveness(self, history: ActionHistory) -> float:
        """
        Calculate exploration aggressiveness.
        
        Simplified: Use energy variance as proxy for exploration
        (High variance = aggressive exploration)
        
        Args:
            history: Agent's action history
            
        Returns:
            Normalized score [0, 1]
        """
        if len(history.energy_intakes) < 2:
            return 0.5  # Default
        
        energies = [e for _, e in history.energy_intakes]
        variance = np.var(energies)
        
        # Normalize (assume max variance ~1.0)
        return min(variance, 1.0)
    
    def _calculate_resource_switching_rate(self, history: ActionHistory) -> float:
        """
        Calculate resource switching rate.
        
        Measures how often agent changes resource types.
        
        Args:
            history: Agent's action history
            
        Returns:
            Normalized score [0, 1]
        """
        if len(history.resource_acquisitions) < 2:
            return 0.0
        
        # Count resource type changes
        switches = 0
        prev_resource = None
        
        for _, resource_type in history.resource_acquisitions:
            if prev_resource is not None and resource_type != prev_resource:
                switches += 1
            prev_resource = resource_type
        
        # Normalize by total acquisitions
        switch_rate = switches / len(history.resource_acquisitions)
        
        return min(switch_rate, 1.0)
    
    def _calculate_risk_taking_profile(self, history: ActionHistory) -> float:
        """
        Calculate risk-taking profile.
        
        Measures variance in energy intake (high variance = high risk).
        
        Args:
            history: Agent's action history
            
        Returns:
            Normalized score [0, 1]
        """
        if len(history.energy_intakes) < 2:
            return 0.5
        
        energies = [e for _, e in history.energy_intakes]
        mean_energy = np.mean(energies)
        
        if mean_energy == 0:
            return 0.5
        
        # Coefficient of variation
        cv = np.std(energies) / mean_energy
        
        # Normalize (assume max CV ~2.0)
        return min(cv / 2.0, 1.0)
    
    def _calculate_response_time(self, history: ActionHistory) -> float:
        """
        Calculate environmental response time.
        
        Measures how quickly agent adapts to phase changes.
        
        Args:
            history: Agent's action history
            
        Returns:
            Normalized score [0, 1] (0 = slow, 1 = fast)
        """
        if len(history.phase_responses) == 0:
            return 0.5
        
        # Average response time
        response_times = [rt for _, _, rt in history.phase_responses]
        avg_response = np.mean(response_times)
        
        # Normalize (assume max response time ~50 gens)
        # Invert so fast response = high score
        normalized = 1.0 - min(avg_response / 50.0, 1.0)
        
        return normalized
    
    def _calculate_pressure_tolerance(self, history: ActionHistory) -> float:
        """
        Calculate constraint pressure tolerance.
        
        Measures how close to limits agent operates.
        
        Args:
            history: Agent's action history
            
        Returns:
            Normalized score [0, 1] (0 = safe, 1 = risky)
        """
        if len(history.constraint_violations) == 0:
            return 0.5
        
        # Average margin from constraint
        margins = [margin for _, margin in history.constraint_violations]
        avg_margin = np.mean(margins)
        
        # Normalize (assume max margin ~0.5)
        # Invert so small margin = high pressure tolerance
        if avg_margin > 0:
            tolerance = 1.0 - min(avg_margin / 0.5, 1.0)
        else:
            tolerance = 1.0  # Operating beyond limits
        
        return tolerance
    
    def calculate_population_variance(self, agent_ids: list) -> float:
        """
        Calculate behavioral variance across population.
        
        This is the PRIMARY Week 3 metric.
        
        Args:
            agent_ids: List of agent identifiers
            
        Returns:
            Mean variance across all dimensions
        """
        if len(agent_ids) < 2:
            return 0.0
        
        # Extract signatures for all agents
        signatures = np.array([
            self.calculate_behavioral_signature(agent_id)
            for agent_id in agent_ids
        ])
        
        # Calculate variance across all dimensions
        variance_per_dimension = np.var(signatures, axis=0)
        mean_variance = np.mean(variance_per_dimension)
        
        return float(mean_variance)
    
    def advance_generation(self):
        """Advance to next generation."""
        self.action_recorder.advance_generation()
