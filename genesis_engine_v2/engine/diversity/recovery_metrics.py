"""
Recovery Metrics

Tracks and analyzes population recovery after crisis events.
Main metric: Constraint Resolution Rate (time to restore energy efficiency).

Week 2 - Validation Metrics
"""

import numpy as np
from typing import List, Dict, Tuple


def calculate_energy_efficiency(population) -> float:
    """
    Calculate average energy efficiency of population.
    
    Energy efficiency = phenotype_complexity / metabolic_cost
    
    Args:
        population: List of agents
        
    Returns:
        Average energy efficiency
    """
    if len(population) == 0:
        return 0.0
    
    efficiencies = []
    for agent in population:
        # Use phenotype length as complexity measure
        if agent.phenotype is not None and len(agent.phenotype) > 0:
            complexity = len(agent.phenotype)
        else:
            complexity = agent.genome.get_length()
        
        cost = agent.genome.metabolic_cost
        efficiency = complexity / (cost + 0.01)
        efficiencies.append(efficiency)
    
    return np.mean(efficiencies)


def calculate_behavioral_diversity(population, translator=None) -> float:
    """
    Calculate behavioral diversity using signature variance.
    
    Args:
        population: List of agents
        translator: CodonTranslator (optional)
        
    Returns:
        Diversity score (variance of behavioral signatures)
    """
    if len(population) < 2:
        return 0.0
    
    from .active_diversity_manager import extract_behavioral_signature
    
    signatures = np.array([extract_behavioral_signature(agent, translator) 
                          for agent in population])
    
    # Calculate variance across all dimensions
    diversity = np.mean(np.var(signatures, axis=0))
    
    return float(diversity)


def track_recovery_trajectory(engine, pre_crisis_baseline: Dict, max_gens: int = 500,
                              translator=None) -> Dict:
    """
    Monitor recovery metrics over time.
    
    Args:
        engine: GenesisEngine instance
        pre_crisis_baseline: Pre-crisis metrics for comparison
        max_gens: Maximum generations to track (default: 500)
        translator: CodonTranslator (optional)
        
    Returns:
        Dictionary with time-series recovery data
    """
    trajectory = {
        'generations': [],
        'energy_efficiency': [],
        'population_size': [],
        'behavioral_diversity': [],
        'avg_genome_length': []
    }
    
    baseline_efficiency = pre_crisis_baseline.get('avg_energy_efficiency', 1.0)
    
    print(f"[TRACKING] Starting recovery tracking for {max_gens} generations")
    print(f"  Baseline efficiency: {baseline_efficiency:.3f}")
    
    for gen in range(max_gens):
        # Run one generation
        engine.run_cycle()
        
        # Calculate metrics
        efficiency = calculate_energy_efficiency(engine.population)
        diversity = calculate_behavioral_diversity(engine.population, translator)
        avg_length = np.mean([a.genome.get_length() for a in engine.population]) if engine.population else 0
        
        # Record
        trajectory['generations'].append(engine.generation)
        trajectory['energy_efficiency'].append(efficiency)
        trajectory['population_size'].append(len(engine.population))
        trajectory['behavioral_diversity'].append(diversity)
        trajectory['avg_genome_length'].append(avg_length)
        
        # Progress reporting
        if (gen + 1) % 100 == 0:
            recovery_pct = (efficiency / baseline_efficiency) * 100 if baseline_efficiency > 0 else 0
            print(f"  Gen {gen+1}/{max_gens}: Efficiency={efficiency:.3f} ({recovery_pct:.1f}% of baseline), Pop={len(engine.population)}")
    
    return trajectory


def find_recovery_time(trajectory: Dict, baseline_value: float, threshold: float = 0.9) -> int:
    """
    Find generation when metric recovers to threshold of baseline.
    
    Args:
        trajectory: Recovery trajectory data
        baseline_value: Pre-crisis baseline value
        threshold: Recovery threshold (default: 0.9 = 90%)
        
    Returns:
        Generation number when threshold reached, or -1 if not reached
    """
    target_value = baseline_value * threshold
    
    for i, value in enumerate(trajectory['energy_efficiency']):
        if value >= target_value:
            return trajectory['generations'][i]
    
    return -1  # Not recovered within tracking period


def compare_recovery_rates(adm_trajectory: Dict, control_trajectory: Dict,
                           baseline_efficiency: float) -> Dict:
    """
    Compare ADM vs control recovery rates.
    
    Args:
        adm_trajectory: ADM recovery trajectory
        control_trajectory: Control recovery trajectory
        baseline_efficiency: Pre-crisis baseline efficiency
        
    Returns:
        Dictionary with comparison metrics
    """
    # Find recovery times (90% threshold)
    adm_recovery_time = find_recovery_time(adm_trajectory, baseline_efficiency, threshold=0.9)
    control_recovery_time = find_recovery_time(control_trajectory, baseline_efficiency, threshold=0.9)
    
    # Calculate speedup
    if control_recovery_time > 0 and adm_recovery_time > 0:
        speedup = (control_recovery_time - adm_recovery_time) / control_recovery_time
    elif adm_recovery_time > 0 and control_recovery_time == -1:
        speedup = 1.0  # ADM recovered, control didn't
    elif adm_recovery_time == -1 and control_recovery_time > 0:
        speedup = -1.0  # Control recovered, ADM didn't
    else:
        speedup = 0.0  # Neither recovered
    
    # Final efficiency comparison
    adm_final_efficiency = adm_trajectory['energy_efficiency'][-1]
    control_final_efficiency = control_trajectory['energy_efficiency'][-1]
    
    return {
        'adm_recovery_time': adm_recovery_time,
        'control_recovery_time': control_recovery_time,
        'speedup': speedup,
        'speedup_percent': speedup * 100,
        'adm_final_efficiency': adm_final_efficiency,
        'control_final_efficiency': control_final_efficiency,
        'efficiency_advantage': adm_final_efficiency - control_final_efficiency
    }


def calculate_archive_distinctness(adm_archive, random_sample, translator=None) -> float:
    """
    Calculate behavioral distance between ADM archive and random sample.
    
    Args:
        adm_archive: List of archived agents
        random_sample: List of randomly sampled agents
        translator: CodonTranslator (optional)
        
    Returns:
        Mean behavioral distance (0-1 scale)
    """
    from .active_diversity_manager import extract_behavioral_signature
    
    if len(adm_archive) == 0 or len(random_sample) == 0:
        return 0.0
    
    # Extract signatures
    archive_sigs = np.array([extract_behavioral_signature(agent, translator) 
                            for agent in adm_archive])
    random_sigs = np.array([extract_behavioral_signature(agent, translator) 
                           for agent in random_sample])
    
    # Calculate mean signature for each group
    archive_mean = np.mean(archive_sigs, axis=0)
    random_mean = np.mean(random_sigs, axis=0)
    
    # Calculate Euclidean distance between means
    distance = np.linalg.norm(archive_mean - random_mean)
    
    # Normalize to [0, 1] (max distance in 5D unit cube is sqrt(5))
    normalized_distance = distance / np.sqrt(5)
    
    return float(normalized_distance)
