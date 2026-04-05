"""
Behavioral Variance Measurement Utility

Calculates behavioral variance from population using enhanced behavioral signatures.
This is the PRIMARY Week 3 success metric (target: > 0.1).
"""

import numpy as np
from typing import List


def extract_behavioral_signature_enhanced(agent, resource_system, spatial_env) -> np.ndarray:
    """
    Extract enhanced 5D behavioral signature from agent.
    
    Dimensions (behavioral, not structural):
    1. Resource specialization: Efficiency with best resource
    2. Regional adaptation: Fitness modifier in current region
    3. Genome efficiency: Phenotype length / genome length
    4. Energy efficiency: Phenotype length / metabolic cost
    5. Spatial preference: Region energy constant / agent cost
    
    Args:
        agent: Agent instance
        resource_system: ResourceNicheSystem
        spatial_env: SpatialEnvironment
        
    Returns:
        5D numpy array, normalized to [0, 1]
    """
    genome = agent.genome
    
    # Dimension 1: Resource specialization (best resource efficiency)
    best_efficiency = 0.0
    for resource_type in ['A', 'B', 'C']:
        eff = resource_system.calculate_agent_efficiency(agent, resource_type)
        best_efficiency = max(best_efficiency, eff)
    resource_spec = best_efficiency / 2.0  # Normalize (max is 2.0)
    
    # Dimension 2: Regional adaptation
    region = spatial_env.get_region_for_agent(agent.id)
    regional_modifier = region.calculate_fitness_modifier(agent)
    regional_adapt = (regional_modifier - 0.5) / 1.0  # Normalize from [0.5, 1.5] to [0, 1]
    
    # Dimension 3: Genome efficiency (phenotype/genome ratio)
    if agent.phenotype is not None and len(agent.phenotype) > 0:
        phenotype_len = len(agent.phenotype)
    else:
        phenotype_len = genome.get_length()
    genome_eff = phenotype_len / max(genome.get_length(), 1)
    
    # Dimension 4: Energy efficiency
    energy_eff = phenotype_len / (genome.metabolic_cost + 0.01)
    energy_eff = min(energy_eff / 50.0, 1.0)  # Normalize
    
    # Dimension 5: Spatial preference (how well agent fits region)
    spatial_pref = region.energy_constant / (genome.metabolic_cost + 0.01)
    spatial_pref = min(spatial_pref / 2.0, 1.0)  # Normalize
    
    # Create signature vector
    signature = np.array([
        resource_spec,
        regional_adapt,
        genome_eff,
        energy_eff,
        spatial_pref
    ])
    
    # Clip to [0, 1]
    signature = np.clip(signature, 0, 1)
    
    return signature


def calculate_behavioral_variance(population, resource_system, spatial_env) -> float:
    """
    Calculate behavioral variance of population.
    
    This is the PRIMARY Week 3 success metric.
    Target: > 0.1 (20x improvement from baseline 0.005)
    
    Args:
        population: List of agents
        resource_system: ResourceNicheSystem
        spatial_env: SpatialEnvironment
        
    Returns:
        Variance score (mean variance across all dimensions)
    """
    if len(population) < 2:
        return 0.0
    
    # Extract signatures for all agents
    signatures = np.array([
        extract_behavioral_signature_enhanced(agent, resource_system, spatial_env)
        for agent in population
    ])
    
    # Calculate variance across all dimensions
    variance_per_dimension = np.var(signatures, axis=0)
    mean_variance = np.mean(variance_per_dimension)
    
    return float(mean_variance)
