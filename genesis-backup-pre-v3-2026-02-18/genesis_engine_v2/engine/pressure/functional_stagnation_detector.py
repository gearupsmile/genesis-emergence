"""
Functional Stagnation Detector - Week 3 Phase 4

Detects when evolutionary innovation stalls and applies intelligent
pressure to break convergence and maintain exploration.

Design:
- Tracks novel events (resource exploitations, constraint resolutions)
- 100-generation sliding window
- Applies 10% constraint tightening when stagnation detected
- Releases pressure when innovation resumes
"""

from typing import List, Dict, Set, Tuple
from collections import deque


class InnovationTracker:
    """
    Tracks novel evolutionary events.
    
    Innovation types:
    - Novel resource exploitation (agent achieves >0.8 efficiency)
    - Constraint resolution (population achieves >90% compliance)
    - Behavioral novelty (new cluster in signature space)
    """
    
    def __init__(self):
        """Initialize innovation tracker."""
        # Track which innovations have been achieved
        self.resource_exploitations: Set[Tuple[str, str]] = set()  # (agent_id, resource_type)
        self.constraint_resolutions: Set[str] = set()  # region_name
        self.behavioral_clusters: Set[int] = set()  # cluster_id
        
        # Track innovation events per generation
        self.innovation_log: List[Dict] = []
    
    def detect_resource_exploitation(self, agent, resource_type: str, efficiency: float) -> bool:
        """
        Detect if agent achieved novel resource exploitation.
        
        Args:
            agent: Agent instance
            resource_type: Resource type ('A', 'B', or 'C')
            efficiency: Agent's efficiency with this resource
            
        Returns:
            True if this is a novel exploitation
        """
        if efficiency > 0.8:
            key = (agent.id, resource_type)
            if key not in self.resource_exploitations:
                self.resource_exploitations.add(key)
                return True
        return False
    
    def detect_constraint_resolution(self, region_name: str, compliance_rate: float) -> bool:
        """
        Detect if population achieved novel constraint resolution.
        
        Args:
            region_name: Name of region
            compliance_rate: Fraction of agents complying with constraint
            
        Returns:
            True if this is a novel resolution
        """
        if compliance_rate > 0.9:
            if region_name not in self.constraint_resolutions:
                self.constraint_resolutions.add(region_name)
                return True
        return False
    
    def count_innovations(self, generation: int, innovation_events: List[str]) -> int:
        """
        Count and log innovations for a generation.
        
        Args:
            generation: Current generation number
            innovation_events: List of innovation descriptions
            
        Returns:
            Number of innovations this generation
        """
        count = len(innovation_events)
        
        if count > 0:
            self.innovation_log.append({
                'generation': generation,
                'count': count,
                'events': innovation_events
            })
        
        return count


class FunctionalStagnationDetector:
    """
    Detects evolutionary stagnation and applies pressure.
    
    Monitors innovation rate over sliding window and tightens
    constraints when innovation falls below threshold.
    """
    
    def __init__(self, window_size: int = 100, innovation_threshold: int = 2,
                 pressure_magnitude: float = 0.1, pressure_duration: int = 100):
        """
        Initialize Functional Stagnation Detector.
        
        Args:
            window_size: Generations to track for stagnation (default: 100)
            innovation_threshold: Min innovations per window (default: 2)
            pressure_magnitude: Constraint tightening fraction (default: 0.1 = 10%)
            pressure_duration: Minimum generations under pressure (default: 100)
        """
        self.window_size = window_size
        self.innovation_threshold = innovation_threshold
        self.pressure_magnitude = pressure_magnitude
        self.pressure_duration = pressure_duration
        
        # Innovation tracking
        self.innovation_tracker = InnovationTracker()
        self.innovation_history: deque = deque(maxlen=window_size)  # (generation, count)
        
        # Pressure state
        self.pressure_active = False
        self.pressure_start_gen: int = 0
        self.pressure_count = 0
        
        # Statistics
        self.stagnation_events: List[Dict] = []
        self.pressure_releases: List[Dict] = []
    
    def track_innovation(self, generation: int, population, resource_system, spatial_env) -> int:
        """
        Track innovations for current generation.
        
        Args:
            generation: Current generation number
            population: List of agents
            resource_system: ResourceNicheSystem instance
            spatial_env: SpatialEnvironment instance
            
        Returns:
            Number of innovations detected
        """
        innovation_events = []
        
        # Check for resource exploitations
        for agent in population:
            for resource_type in ['A', 'B', 'C']:
                efficiency = resource_system.calculate_agent_efficiency(agent, resource_type)
                if self.innovation_tracker.detect_resource_exploitation(agent, resource_type, efficiency):
                    innovation_events.append(f"Resource {resource_type} exploitation by agent {agent.id}")
        
        # Check for constraint resolutions (regional compliance)
        for region_name, region in spatial_env.regions.items():
            # Count agents in region that comply with constraint
            agents_in_region = [a for a in population 
                              if spatial_env.get_region_name_for_agent(a.id) == region_name]
            
            if len(agents_in_region) > 0:
                compliant = sum(1 for a in agents_in_region 
                              if a.genome.metabolic_cost <= region.energy_constant)
                compliance_rate = compliant / len(agents_in_region)
                
                if self.innovation_tracker.detect_constraint_resolution(region_name, compliance_rate):
                    innovation_events.append(f"Constraint resolution in {region_name} region")
        
        # Count innovations
        innovation_count = self.innovation_tracker.count_innovations(generation, innovation_events)
        
        # Add to history
        self.innovation_history.append((generation, innovation_count))
        
        return innovation_count
    
    def detect_stagnation(self, generation: int) -> bool:
        """
        Check if innovation rate has fallen below threshold.
        
        Args:
            generation: Current generation number
            
        Returns:
            True if stagnation detected
        """
        # Need full window to detect
        if len(self.innovation_history) < self.window_size:
            return False
        
        # Already under pressure
        if self.pressure_active:
            return False
        
        # Count recent innovations
        recent_innovations = sum(count for _, count in self.innovation_history)
        
        if recent_innovations < self.innovation_threshold:
            # Stagnation detected
            self.stagnation_events.append({
                'generation': generation,
                'innovation_count': recent_innovations,
                'threshold': self.innovation_threshold
            })
            return True
        
        return False
    
    def apply_pressure(self, generation: int, base_energy_constant: float) -> float:
        """
        Apply pressure by tightening constraints.
        
        Args:
            generation: Current generation number
            base_energy_constant: Base energy constant value
            
        Returns:
            Modified energy constant (tightened)
        """
        self.pressure_active = True
        self.pressure_start_gen = generation
        self.pressure_count += 1
        
        # Tighten constraint
        modified_constant = base_energy_constant * (1 - self.pressure_magnitude)
        
        print(f"  [FSD] Pressure applied at gen {generation} "
              f"(constant: {base_energy_constant:.3f} → {modified_constant:.3f})")
        
        return modified_constant
    
    def check_pressure_release(self, generation: int, base_energy_constant: float) -> Tuple[bool, float]:
        """
        Check if pressure should be released.
        
        Releases pressure if:
        - Minimum duration passed AND
        - Innovation has resumed (>= threshold in last 50 gens)
        
        Args:
            generation: Current generation number
            base_energy_constant: Base energy constant value
            
        Returns:
            Tuple of (should_release, energy_constant)
        """
        if not self.pressure_active:
            return False, base_energy_constant
        
        # Check minimum duration
        duration = generation - self.pressure_start_gen
        if duration < self.pressure_duration:
            return False, base_energy_constant * (1 - self.pressure_magnitude)
        
        # Check if innovation resumed (last 50 gens)
        recent_window = min(50, len(self.innovation_history))
        if recent_window > 0:
            recent_innovations = sum(count for _, count in list(self.innovation_history)[-recent_window:])
            
            if recent_innovations >= self.innovation_threshold / 2:  # Half threshold for release
                # Release pressure
                self.pressure_active = False
                
                self.pressure_releases.append({
                    'generation': generation,
                    'duration': duration,
                    'innovation_count': recent_innovations
                })
                
                print(f"  [FSD] Pressure released at gen {generation} "
                      f"(duration: {duration} gens, innovations: {recent_innovations})")
                
                return True, base_energy_constant
        
        # Keep pressure active
        return False, base_energy_constant * (1 - self.pressure_magnitude)
    
    def get_statistics(self) -> Dict:
        """Get FSD statistics."""
        return {
            'pressure_active': self.pressure_active,
            'pressure_count': self.pressure_count,
            'stagnation_events': len(self.stagnation_events),
            'pressure_releases': len(self.pressure_releases),
            'total_innovations': len(self.innovation_tracker.innovation_log),
            'resource_exploitations': len(self.innovation_tracker.resource_exploitations),
            'constraint_resolutions': len(self.innovation_tracker.constraint_resolutions)
        }
    
    def __repr__(self) -> str:
        """String representation."""
        status = "ACTIVE" if self.pressure_active else "INACTIVE"
        return (f"FunctionalStagnationDetector(pressure={status}, "
                f"events={len(self.stagnation_events)}, "
                f"innovations={len(self.innovation_tracker.innovation_log)})")
