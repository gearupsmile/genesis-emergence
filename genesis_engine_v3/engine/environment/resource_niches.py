"""
Resource Niche System - Week 3 Phase 1

Implements multiple resource types with different acquisition costs to drive
functional specialization and behavioral diversity.

Design:
- 3 resource types: High-risk (A), Balanced (B), Opportunist (C)
- Agents develop specialization based on genome
- Resource efficiency contributes to fitness
"""

import random
from typing import Dict, List, Tuple
from dataclasses import dataclass


@dataclass
class ResourceType:
    """
    Defines a resource type with specific characteristics.
    
    Attributes:
        name: Resource identifier (e.g., "ResourceA")
        base_energy: Energy provided when consumed
        acquisition_cost: Metabolic cost to acquire
        abundance: Availability in environment (0-1)
        regeneration_rate: How quickly resource replenishes
    """
    name: str
    base_energy: float
    acquisition_cost: float
    abundance: float
    regeneration_rate: float
    
    def get_net_energy(self, agent_efficiency: float = 1.0) -> float:
        """
        Calculate net energy gain for an agent.
        
        Args:
            agent_efficiency: Agent's efficiency multiplier for this resource (0-2)
            
        Returns:
            Net energy = (base_energy * efficiency) - acquisition_cost
        """
        gross_energy = self.base_energy * agent_efficiency
        net_energy = gross_energy - self.acquisition_cost
        return max(0.0, net_energy)  # Can't be negative


class ResourceNicheSystem:
    """
    Manages multiple resource types and agent specialization.
    
    Creates environmental pressure for functional specialization by
    providing resources with different risk/reward profiles.
    """
    
    def __init__(self):
        """Initialize resource niche system with 3 resource types."""
        # Resource Type A: High-risk, high-reward
        # Specialists can thrive, generalists struggle
        self.resource_a = ResourceType(
            name="ResourceA",
            base_energy=1.0,
            acquisition_cost=0.8,
            abundance=0.2,
            regeneration_rate=0.1
        )
        
        # Resource Type B: Balanced
        # Moderate risk, moderate reward
        self.resource_b = ResourceType(
            name="ResourceB",
            base_energy=0.6,
            acquisition_cost=0.4,
            abundance=0.5,
            regeneration_rate=0.3
        )
        
        # Resource Type C: Opportunist
        # Low-risk, low-reward
        self.resource_c = ResourceType(
            name="ResourceC",
            base_energy=0.3,
            acquisition_cost=0.1,
            abundance=0.8,
            regeneration_rate=0.5
        )
        
        self.resources = {
            'A': self.resource_a,
            'B': self.resource_b,
            'C': self.resource_c
        }
        
        # Track current availability (modified by consumption and regeneration)
        self.current_availability = {
            'A': self.resource_a.abundance,
            'B': self.resource_b.abundance,
            'C': self.resource_c.abundance
        }
        
        # Track agent specializations for analysis
        self.agent_specializations: Dict[str, str] = {}  # agent_id -> preferred_resource
    
    def calculate_agent_efficiency(self, agent, resource_type: str) -> float:
        """
        Calculate agent's efficiency for a specific resource type.
        
        Based on genome characteristics. Agents can specialize.
        
        Args:
            agent: Agent instance
            resource_type: 'A', 'B', or 'C'
            
        Returns:
            Efficiency multiplier (0.5 to 2.0)
        """
        # Use genome length as specialization indicator
        genome_length = agent.genome.get_length()
        
        # Simple specialization heuristic based on genome length
        # This creates pressure for different genome sizes to prefer different resources
        if resource_type == 'A':
            # High-risk resource favors larger genomes (more capacity)
            efficiency = 0.5 + (genome_length / 30.0) * 1.5
        elif resource_type == 'B':
            # Balanced resource favors medium genomes
            optimal_length = 15
            distance = abs(genome_length - optimal_length)
            efficiency = 2.0 - (distance / 15.0)
        else:  # resource_type == 'C'
            # Opportunist resource favors smaller genomes (efficiency)
            efficiency = 2.0 - (genome_length / 30.0) * 1.5
        
        # Clamp to reasonable range
        return max(0.5, min(2.0, efficiency))
    
    def get_best_resource_for_agent(self, agent) -> Tuple[str, float]:
        """
        Determine which resource type is best for an agent.
        
        Args:
            agent: Agent instance
            
        Returns:
            Tuple of (resource_type, net_energy)
        """
        best_resource = None
        best_net_energy = -float('inf')
        
        for res_type, resource in self.resources.items():
            # Check availability
            if self.current_availability[res_type] < 0.01:
                continue  # Resource depleted
            
            # Calculate efficiency
            efficiency = self.calculate_agent_efficiency(agent, res_type)
            net_energy = resource.get_net_energy(efficiency)
            
            # Weight by availability (harder to get rare resources)
            weighted_energy = net_energy * self.current_availability[res_type]
            
            if weighted_energy > best_net_energy:
                best_net_energy = weighted_energy
                best_resource = res_type
        
        return best_resource, best_net_energy
    
    def agent_consumes_resource(self, agent, resource_type: str = None) -> float:
        """
        Agent attempts to consume a resource.
        
        Args:
            agent: Agent instance
            resource_type: Specific resource to consume, or None for best choice
            
        Returns:
            Net energy gained
        """
        # Auto-select best resource if not specified
        if resource_type is None:
            resource_type, _ = self.get_best_resource_for_agent(agent)
        
        if resource_type is None:
            return 0.0  # No resources available
        
        resource = self.resources[resource_type]
        
        # Check availability
        if self.current_availability[resource_type] < 0.01:
            return 0.0  # Resource depleted
        
        # Calculate efficiency and net energy
        efficiency = self.calculate_agent_efficiency(agent, resource_type)
        net_energy = resource.get_net_energy(efficiency)
        
        # Consume resource (reduce availability)
        consumption = 0.01  # Each agent consumes 1% of resource
        self.current_availability[resource_type] = max(
            0.0,
            self.current_availability[resource_type] - consumption
        )
        
        # Track specialization
        self.agent_specializations[agent.id] = resource_type
        
        return net_energy
    
    def regenerate_resources(self):
        """
        Regenerate resources based on regeneration rates.
        
        Called once per generation.
        """
        for res_type, resource in self.resources.items():
            current = self.current_availability[res_type]
            max_abundance = resource.abundance
            regeneration = resource.regeneration_rate
            
            # Regenerate toward max abundance
            new_availability = current + (max_abundance - current) * regeneration
            self.current_availability[res_type] = min(max_abundance, new_availability)
    
    def get_specialization_distribution(self) -> Dict[str, int]:
        """
        Get distribution of agent specializations.
        
        Returns:
            Dictionary of resource_type -> count
        """
        distribution = {'A': 0, 'B': 0, 'C': 0}
        for resource_type in self.agent_specializations.values():
            distribution[resource_type] += 1
        return distribution
    
    def get_specialization_entropy(self) -> float:
        """
        Calculate Shannon entropy of specialization distribution.
        
        Higher entropy = more diverse specializations.
        Target: > 0.6 for clear niche partitioning.
        
        Returns:
            Entropy value (0 to ~1.1)
        """
        import math
        
        distribution = self.get_specialization_distribution()
        total = sum(distribution.values())
        
        if total == 0:
            return 0.0
        
        entropy = 0.0
        for count in distribution.values():
            if count > 0:
                p = count / total
                entropy -= p * math.log2(p)
        
        # Normalize to 0-1 range (max entropy for 3 categories is log2(3) ≈ 1.585)
        return entropy / 1.585
    
    def get_statistics(self) -> Dict:
        """Get resource system statistics."""
        return {
            'availability': dict(self.current_availability),
            'specialization_distribution': self.get_specialization_distribution(),
            'specialization_entropy': self.get_specialization_entropy(),
            'total_specialists': len(self.agent_specializations)
        }
    
    def __repr__(self) -> str:
        """String representation."""
        dist = self.get_specialization_distribution()
        return (f"ResourceNicheSystem(A:{dist['A']}, B:{dist['B']}, C:{dist['C']}, "
                f"entropy={self.get_specialization_entropy():.3f})")
