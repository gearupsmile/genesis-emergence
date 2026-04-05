"""
Gatekeeper Logger - Enhanced Logging for Physics Gatekeeper

Tracks rejection rates, genetic diversity, and boundary agents.
Part of Track 1: Physics Gatekeeper v2
"""

from typing import List, Dict, Optional
import numpy as np
from collections import deque


class GatekeeperLogger:
    """
    Comprehensive logging system for Physics Gatekeeper.
    
    Tracks:
    - Rejection rate per generation
    - Parent vs offspring rejections
    - Genetic diversity of boundary agents
    - Cumulative statistics
    """
    
    def __init__(self, window_size: int = 100):
        """
        Initialize logger.
        
        Args:
            window_size: Number of generations to track in rolling window
        """
        self.window_size = window_size
        
        # Per-generation logs
        self.generation_logs = []
        
        # Rolling window for recent statistics
        self.recent_rejection_rates = deque(maxlen=window_size)
        
        # Cumulative counters
        self.total_parent_checks = 0
        self.total_parent_rejections = 0
        self.total_offspring_checks = 0
        self.total_offspring_rejections = 0
    
    def log_generation(self, generation: int, 
                      parent_checked: int, parent_rejected: int,
                      offspring_checked: int, offspring_rejected: int,
                      boundary_agents: List[Dict],
                      genetic_diversity_score: float):
        """
        Log statistics for a generation.
        
        Args:
            generation: Generation number
            parent_checked: Number of parents checked
            parent_rejected: Number of parents rejected
            offspring_checked: Number of offspring checked
            offspring_rejected: Number of offspring rejected
            boundary_agents: List of agents near viability boundary
            genetic_diversity_score: Genetic diversity metric
        """
        total_checked = parent_checked + offspring_checked
        total_rejected = parent_rejected + offspring_rejected
        rejection_rate = total_rejected / total_checked if total_checked > 0 else 0.0
        
        log_entry = {
            'generation': generation,
            'total_checked': total_checked,
            'total_rejected': total_rejected,
            'rejection_rate': rejection_rate,
            'parent_checks': parent_checked,
            'parent_rejections': parent_rejected,
            'parent_rejection_rate': parent_rejected / parent_checked if parent_checked > 0 else 0.0,
            'offspring_checks': offspring_checked,
            'offspring_rejections': offspring_rejected,
            'offspring_rejection_rate': offspring_rejected / offspring_checked if offspring_checked > 0 else 0.0,
            'boundary_agent_count': len(boundary_agents),
            'boundary_agents': boundary_agents,
            'genetic_diversity_score': genetic_diversity_score
        }
        
        self.generation_logs.append(log_entry)
        self.recent_rejection_rates.append(rejection_rate)
        
        # Update cumulative counters
        self.total_parent_checks += parent_checked
        self.total_parent_rejections += parent_rejected
        self.total_offspring_checks += offspring_checked
        self.total_offspring_rejections += offspring_rejected
    
    def get_current_rejection_rate(self) -> float:
        """Get most recent rejection rate."""
        if self.generation_logs:
            return self.generation_logs[-1]['rejection_rate']
        return 0.0
    
    def get_average_rejection_rate(self, window: Optional[int] = None) -> float:
        """
        Get average rejection rate over window.
        
        Args:
            window: Number of recent generations (None = all time)
        """
        if window is None:
            # All-time average
            total_checks = self.total_parent_checks + self.total_offspring_checks
            total_rejections = self.total_parent_rejections + self.total_offspring_rejections
            return total_rejections / total_checks if total_checks > 0 else 0.0
        else:
            # Windowed average
            recent_logs = self.generation_logs[-window:] if len(self.generation_logs) >= window else self.generation_logs
            if not recent_logs:
                return 0.0
            return np.mean([log['rejection_rate'] for log in recent_logs])
    
    def get_rejection_rate_stability(self) -> float:
        """
        Calculate stability of rejection rate (lower = more stable).
        
        Returns:
            Standard deviation of recent rejection rates
        """
        if len(self.recent_rejection_rates) < 2:
            return 0.0
        return np.std(list(self.recent_rejection_rates))
    
    def get_summary_statistics(self) -> Dict:
        """Get comprehensive summary statistics."""
        return {
            'total_generations_logged': len(self.generation_logs),
            'total_parent_checks': self.total_parent_checks,
            'total_parent_rejections': self.total_parent_rejections,
            'parent_rejection_rate': self.total_parent_rejections / self.total_parent_checks if self.total_parent_checks > 0 else 0.0,
            'total_offspring_checks': self.total_offspring_checks,
            'total_offspring_rejections': self.total_offspring_rejections,
            'offspring_rejection_rate': self.total_offspring_rejections / self.total_offspring_checks if self.total_offspring_checks > 0 else 0.0,
            'overall_rejection_rate': self.get_average_rejection_rate(),
            'recent_rejection_rate': self.get_average_rejection_rate(window=10),
            'rejection_rate_stability': self.get_rejection_rate_stability()
        }
    
    def get_generation_log(self, generation: int) -> Optional[Dict]:
        """Get log entry for specific generation."""
        for log in self.generation_logs:
            if log['generation'] == generation:
                return log
        return None
    
    def get_recent_logs(self, count: int = 10) -> List[Dict]:
        """Get most recent log entries."""
        return self.generation_logs[-count:] if self.generation_logs else []
    
    def reset(self):
        """Reset all logs and statistics."""
        self.generation_logs = []
        self.recent_rejection_rates.clear()
        self.total_parent_checks = 0
        self.total_parent_rejections = 0
        self.total_offspring_checks = 0
        self.total_offspring_rejections = 0
