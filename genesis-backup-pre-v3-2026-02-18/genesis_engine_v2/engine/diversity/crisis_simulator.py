"""
Crisis Simulator

Implements controlled crisis scenarios for testing ADM recovery capability.
Uses reproducible random seed for consistent crisis application.

Week 2 - Decoupled Validation
"""

import random
import copy
from typing import List, Tuple, Dict


def simulate_crisis(engine, removal_rate: float = 0.8, seed: int = 42) -> Tuple[List, Dict]:
    """
    Simulate population crisis by removing random fraction of agents.
    
    Args:
        engine: GenesisEngine instance
        removal_rate: Fraction of population to remove (default: 0.8 = 80%)
        seed: Random seed for reproducibility (default: 42)
        
    Returns:
        Tuple of (removed_agents, pre_crisis_state)
    """
    # Set random seed for reproducibility
    random.seed(seed)
    
    # Save pre-crisis state
    pre_crisis_state = {
        'population_size': len(engine.population),
        'generation': engine.generation,
        'avg_metabolic_cost': sum(a.genome.metabolic_cost for a in engine.population) / len(engine.population),
        'avg_genome_length': sum(a.genome.get_length() for a in engine.population) / len(engine.population)
    }
    
    # Calculate number to remove
    n_remove = int(len(engine.population) * removal_rate)
    n_survive = len(engine.population) - n_remove
    
    # Randomly select agents to remove
    all_agents = list(engine.population)
    random.shuffle(all_agents)
    
    removed_agents = all_agents[:n_remove]
    survivors = all_agents[n_remove:]
    
    # Update engine population
    engine.population = survivors
    
    print(f"[CRISIS] Removed {n_remove} agents ({removal_rate*100:.0f}%), {n_survive} survivors")
    
    return removed_agents, pre_crisis_state


def repopulate_from_archive(engine, adm, mutation_rate: float = 0.05, target_size: int = None):
    """
    Repopulate from ADM archive.
    
    Clones archived agents with slight mutations to restore diversity.
    
    Args:
        engine: GenesisEngine instance
        adm: ActiveDiversityManager instance
        mutation_rate: Mutation rate for cloned agents (default: 0.05)
        target_size: Target population size (default: engine.population_size)
    """
    if target_size is None:
        target_size = engine.population_size
    
    if len(adm.archive) == 0:
        raise ValueError("ADM archive is empty - cannot repopulate")
    
    # Clone agents from archive
    new_population = []
    archive_size = len(adm.archive)
    
    for i in range(target_size):
        # Select agent from archive (cycle through if needed)
        source_agent = adm.archive[i % archive_size]
        
        # Clone and mutate
        cloned_agent = copy.deepcopy(source_agent)
        if mutation_rate > 0:
            cloned_agent = cloned_agent.reproduce(mutation_rate)
        
        new_population.append(cloned_agent)
    
    engine.population = new_population
    
    print(f"[RECOVERY] Repopulated to {len(new_population)} agents from ADM archive ({archive_size} unique)")


def repopulate_from_random(engine, pre_crisis_agents: List, mutation_rate: float = 0.05, 
                           target_size: int = None, seed: int = 42):
    """
    Repopulate from random pre-crisis sample (control condition).
    
    Args:
        engine: GenesisEngine instance
        pre_crisis_agents: List of agents from before crisis
        mutation_rate: Mutation rate for cloned agents (default: 0.05)
        target_size: Target population size (default: engine.population_size)
        seed: Random seed for reproducibility (default: 42)
    """
    if target_size is None:
        target_size = engine.population_size
    
    random.seed(seed)
    
    # Randomly sample from pre-crisis agents
    sample_size = min(50, len(pre_crisis_agents))  # Match ADM archive size
    sampled_agents = random.sample(pre_crisis_agents, sample_size)
    
    # Clone and mutate to reach target size
    new_population = []
    for i in range(target_size):
        source_agent = sampled_agents[i % sample_size]
        cloned_agent = copy.deepcopy(source_agent)
        if mutation_rate > 0:
            cloned_agent = cloned_agent.reproduce(mutation_rate)
        new_population.append(cloned_agent)
    
    engine.population = new_population
    
    print(f"[CONTROL] Repopulated to {len(new_population)} agents from random sample ({sample_size} unique)")


def save_pre_crisis_snapshot(engine, filename: str):
    """Save complete pre-crisis state for later restoration."""
    import pickle
    
    snapshot = {
        'population': copy.deepcopy(engine.population),
        'generation': engine.generation,
        'statistics': copy.deepcopy(engine.statistics) if hasattr(engine, 'statistics') else []
    }
    
    with open(filename, 'wb') as f:
        pickle.dump(snapshot, f)
    
    print(f"[SNAPSHOT] Saved pre-crisis state to {filename}")


def restore_pre_crisis_snapshot(engine, filename: str):
    """Restore engine to pre-crisis state."""
    import pickle
    
    with open(filename, 'rb') as f:
        snapshot = pickle.load(f)
    
    engine.population = snapshot['population']
    engine.generation = snapshot['generation']
    if hasattr(engine, 'statistics'):
        engine.statistics = snapshot['statistics']
    
    print(f"[RESTORE] Restored pre-crisis state from {filename}")
