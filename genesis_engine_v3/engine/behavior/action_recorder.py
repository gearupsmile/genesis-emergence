"""
Action Recorder - Tracks agent actions over time

Records behavioral events in rolling window for signature calculation.
"""

from collections import deque
from typing import Dict, List, Any
import numpy as np


class ActionHistory:
    """Stores action history for a single agent."""
    
    def __init__(self, window_size: int = 100):
        """
        Initialize action history.
        
        Args:
            window_size: Number of generations to track
        """
        self.window_size = window_size
        
        # Action buffers (rolling windows)
        self.resource_acquisitions = deque(maxlen=window_size)  # (gen, resource_type)
        self.energy_intakes = deque(maxlen=window_size)  # (gen, energy_amount)
        self.phase_responses = deque(maxlen=window_size)  # (gen, phase_name, response_time)
        self.constraint_violations = deque(maxlen=window_size)  # (gen, violation_margin)
        self.action_trace = deque(maxlen=10000)      # (gen, action_code) — large window for LZ
        
        # Derived metrics
        self.total_distance_traveled = 0.0
        self.last_position = None
    
    def record_resource_acquisition(self, generation: int, resource_type: str):
        """Record resource acquisition event."""
        self.resource_acquisitions.append((generation, resource_type))
    
    def record_energy_intake(self, generation: int, energy: float):
        """Record energy intake event."""
        self.energy_intakes.append((generation, energy))
    
    def record_phase_response(self, generation: int, phase_name: str, response_time: int):
        """Record response to phase change."""
        self.phase_responses.append((generation, phase_name, response_time))
    
    def record_constraint_check(self, generation: int, cost: float, limit: float):
        """Record constraint pressure."""
        margin = limit - cost
        self.constraint_violations.append((generation, margin))
    
    def record_action(self, generation: int, action_code: str):
        """Record generic action code (e.g., 'M', 'S', 'E')."""
        self.action_trace.append((generation, action_code))


class ActionRecorder:
    """
    Records actions for all agents in the population.
    
    Maintains rolling history windows for behavioral signature calculation.
    """
    
    def __init__(self, window_size: int = 100):
        """
        Initialize action recorder.
        
        Args:
            window_size: Number of generations to track
        """
        self.window_size = window_size
        self.agent_histories: Dict[str, ActionHistory] = {}
        self.current_generation = 0
    
    def get_or_create_history(self, agent_id: str) -> ActionHistory:
        """Get or create history for agent."""
        if agent_id not in self.agent_histories:
            self.agent_histories[agent_id] = ActionHistory(self.window_size)
        return self.agent_histories[agent_id]
    
    def record_resource_acquisition(self, agent_id: str, resource_type: str):
        """Record that agent acquired a resource."""
        history = self.get_or_create_history(agent_id)
        history.record_resource_acquisition(self.current_generation, resource_type)
    
    def record_energy_intake(self, agent_id: str, energy: float):
        """Record agent's energy intake."""
        history = self.get_or_create_history(agent_id)
        history.record_energy_intake(self.current_generation, energy)
    
    def record_phase_change(self, agent_id: str, phase_name: str, generations_since_change: int):
        """Record agent's response to phase change."""
        history = self.get_or_create_history(agent_id)
        history.record_phase_response(self.current_generation, phase_name, generations_since_change)
    
    def record_constraint_check(self, agent_id: str, metabolic_cost: float, energy_limit: float):
        """Record agent's constraint pressure."""
        history = self.get_or_create_history(agent_id)
        history.record_constraint_check(self.current_generation, metabolic_cost, energy_limit)

    def record_action(self, agent_id: str, action_code: str):
        """Record raw action code for LZ complexity."""
        history = self.get_or_create_history(agent_id)
        history.record_action(self.current_generation, action_code)
    
    def advance_generation(self):
        """Advance to next generation."""
        self.current_generation += 1
    
    def get_history(self, agent_id: str) -> ActionHistory:
        """Get history for agent."""
        return self.get_or_create_history(agent_id)
