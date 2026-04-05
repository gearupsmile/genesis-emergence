"""
Spatial Regions - Week 3 Phase 2

Implements environmental heterogeneity through spatial regions with
different constraint profiles and resource distributions.

Design:
- 3 regions: Harsh (tight constraints), Moderate (balanced), Permissive (loose)
- Each region has unique energy constant and resource multipliers
- Agents can migrate between regions based on fitness
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import random


@dataclass
class EnvironmentalRegion:
    """
    Defines a spatial region with local environmental conditions.
    
    Attributes:
        name: Region identifier
        energy_constant: Local physics constraint (metabolic cost limit)
        resource_multipliers: Multipliers for each resource type in this region
        position: Spatial coordinates (for visualization)
        capacity: Maximum agents this region can support
    """
    name: str
    energy_constant: float
    resource_multipliers: Dict[str, float]  # {'A': 2.0, 'B': 0.5, 'C': 0.1}
    position: Tuple[float, float]
    capacity: int
    
    def get_local_constraints(self) -> Dict:
        """Get constraint values for this region."""
        return {
            'energy_constant': self.energy_constant,
            'resource_multipliers': self.resource_multipliers
        }
    
    def calculate_fitness_modifier(self, agent) -> float:
        """
        Calculate fitness modifier based on agent's adaptation to region.
        
        Agents that match region characteristics get bonus.
        
        Args:
            agent: Agent instance
            
        Returns:
            Fitness multiplier (0.5 to 1.5)
        """
        # Check if agent's metabolic cost fits region constraint
        cost = agent.genome.metabolic_cost
        
        if cost <= self.energy_constant:
            # Agent fits constraint - bonus based on how well
            headroom = self.energy_constant - cost
            modifier = 1.0 + (headroom * 0.5)  # Up to 1.5x for perfect fit
        else:
            # Agent violates constraint - penalty
            overage = cost - self.energy_constant
            modifier = max(0.5, 1.0 - overage)  # Down to 0.5x
        
        return min(1.5, max(0.5, modifier))


class SpatialEnvironment:
    """
    Manages spatial regions and agent distribution.
    
    Creates environmental heterogeneity to drive spatial specialization.
    """
    
    def __init__(self, migration_rate: float = 0.1):
        """
        Initialize spatial environment with 3 regions.
        
        Args:
            migration_rate: Probability of migration per agent per opportunity
        """
        self.migration_rate = migration_rate
        
        # Create 3 regions with distinct profiles
        self.harsh_region = EnvironmentalRegion(
            name="Harsh",
            energy_constant=0.35,  # Tight constraint (adjusted from 0.3 to avoid crashes)
            resource_multipliers={'A': 2.0, 'B': 0.5, 'C': 0.1},  # Favors Resource A
            position=(0.0, 0.0),
            capacity=30
        )
        
        self.moderate_region = EnvironmentalRegion(
            name="Moderate",
            energy_constant=0.5,  # Normal constraint
            resource_multipliers={'A': 1.0, 'B': 1.0, 'C': 1.0},  # Balanced
            position=(1.0, 0.0),
            capacity=40
        )
        
        self.permissive_region = EnvironmentalRegion(
            name="Permissive",
            energy_constant=0.7,  # Loose constraint
            resource_multipliers={'A': 0.1, 'B': 0.5, 'C': 2.0},  # Favors Resource C
            position=(0.5, 1.0),
            capacity=30
        )
        
        self.regions = {
            'Harsh': self.harsh_region,
            'Moderate': self.moderate_region,
            'Permissive': self.permissive_region
        }
        
        # Track agent assignments
        self.agent_assignments: Dict[str, str] = {}  # agent_id -> region_name
        
        # Track migration statistics
        self.migration_count = 0
        self.migration_history: List[Dict] = []
    
    def initialize_agents(self, population):
        """
        Assign agents to regions initially (uniform distribution).
        
        Args:
            population: List of agents
        """
        region_names = list(self.regions.keys())
        
        for i, agent in enumerate(population):
            # Distribute evenly across regions
            region_name = region_names[i % len(region_names)]
            self.agent_assignments[agent.id] = region_name
    
    def get_region_for_agent(self, agent_id: str) -> EnvironmentalRegion:
        """
        Get the region an agent is currently in.
        
        Args:
            agent_id: Agent identifier
            
        Returns:
            EnvironmentalRegion instance
        """
        region_name = self.agent_assignments.get(agent_id, 'Moderate')
        return self.regions[region_name]
    
    def get_region_name_for_agent(self, agent_id: str) -> str:
        """Get region name for agent."""
        return self.agent_assignments.get(agent_id, 'Moderate')
    
    def get_adjacent_regions(self, current_region_name: str) -> List[EnvironmentalRegion]:
        """
        Get regions adjacent to current region.
        
        For simplicity, all regions are considered adjacent.
        
        Args:
            current_region_name: Name of current region
            
        Returns:
            List of adjacent regions
        """
        return [region for name, region in self.regions.items() 
                if name != current_region_name]
    
    def move_agent(self, agent_id: str, target_region: EnvironmentalRegion):
        """
        Move agent to a new region.
        
        Args:
            agent_id: Agent identifier
            target_region: Target EnvironmentalRegion
        """
        old_region = self.agent_assignments.get(agent_id, 'Moderate')
        self.agent_assignments[agent_id] = target_region.name
        
        self.migration_count += 1
        self.migration_history.append({
            'agent_id': agent_id,
            'from': old_region,
            'to': target_region.name
        })
    
    def allow_migration(self, population, generation: int):
        """
        Allow agents to migrate between regions based on fitness.
        
        Migration occurs every 100 generations.
        
        Args:
            population: List of agents
            generation: Current generation number
        """
        if generation % 100 != 0:
            return  # Only migrate every 100 gens
        
        for agent in population:
            # Migration probability
            if random.random() > self.migration_rate:
                continue
            
            current_region = self.get_region_for_agent(agent.id)
            current_fitness = getattr(agent, 'fitness', 0.0)
            
            # Consider adjacent regions
            adjacent_regions = self.get_adjacent_regions(current_region.name)
            
            best_region = current_region
            best_estimated_fitness = current_fitness
            
            for region in adjacent_regions:
                # Estimate fitness in new region
                modifier = region.calculate_fitness_modifier(agent)
                estimated_fitness = current_fitness * modifier
                
                if estimated_fitness > best_estimated_fitness * 1.1:  # 10% improvement threshold
                    best_region = region
                    best_estimated_fitness = estimated_fitness
            
            # Move if better region found
            if best_region != current_region:
                self.move_agent(agent.id, best_region)
    
    def get_region_distribution(self) -> Dict[str, int]:
        """
        Get distribution of agents across regions.
        
        Returns:
            Dictionary of region_name -> agent_count
        """
        distribution = {name: 0 for name in self.regions.keys()}
        for region_name in self.agent_assignments.values():
            distribution[region_name] += 1
        return distribution
    
    def get_distribution_uniformity(self) -> float:
        """
        Calculate uniformity of agent distribution.
        
        Returns:
            Uniformity score (0 to 1, where 1 = perfectly uniform)
        """
        distribution = self.get_region_distribution()
        total = sum(distribution.values())
        
        if total == 0:
            return 1.0
        
        # Calculate coefficient of variation
        values = list(distribution.values())
        mean = sum(values) / len(values)
        
        if mean == 0:
            return 1.0
        
        variance = sum((v - mean) ** 2 for v in values) / len(values)
        std_dev = variance ** 0.5
        cv = std_dev / mean
        
        # Convert to uniformity (lower CV = higher uniformity)
        uniformity = 1.0 / (1.0 + cv)
        
        return uniformity
    
    def get_statistics(self) -> Dict:
        """Get spatial environment statistics."""
        distribution = self.get_region_distribution()
        uniformity = self.get_distribution_uniformity()
        
        return {
            'distribution': distribution,
            'uniformity': uniformity,
            'migration_count': self.migration_count,
            'total_agents': sum(distribution.values())
        }
    
    def __repr__(self) -> str:
        """String representation."""
        dist = self.get_region_distribution()
        return (f"SpatialEnvironment(Harsh:{dist['Harsh']}, "
                f"Moderate:{dist['Moderate']}, Permissive:{dist['Permissive']}, "
                f"migrations={self.migration_count})")
