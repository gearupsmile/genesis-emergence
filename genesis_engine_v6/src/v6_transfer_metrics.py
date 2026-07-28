"""
v6_transfer_metrics.py - Evaluation metrics for Phase 2 Transfer Shock Experiment
"""

import math
import numpy as np
from typing import List, Dict, Any

def adaptation_speed(performance_curve: List[float], threshold: float = 0.8) -> int:
    """
    Calculate generations to reach 80% (or specified threshold) of final performance.
    
    Args:
        performance_curve: List of performance values ordered by generation.
        threshold: Target fraction of final performance (default 0.8).
        
    Returns:
        Generation index (0-indexed) where performance first reaches target threshold.
        If never reached, returns total number of generations.
    """
    if not performance_curve:
        return 0
    final_perf = performance_curve[-1]
    if final_perf <= 0:
        return len(performance_curve)
        
    target = final_perf * threshold
    for gen, perf in enumerate(performance_curve):
        if perf >= target:
            return gen
    return len(performance_curve)

def survival_rate(population: List[Any], min_energy: float = 0.01) -> float:
    """
    Calculate survival rate across a population.
    Proportion of agents with energy >= min_energy.
    """
    if not population:
        return 0.0
    survivors = sum(1 for agent in population if getattr(agent, 'energy', 0.0) >= min_energy)
    return survivors / len(population)

def action_entropy(action_history: List[str]) -> float:
    """
    Calculate Shannon entropy of agent action distribution ('S', 'M', 'I').
    """
    if not action_history:
        return 0.0
    total = len(action_history)
    counts = {}
    for act in action_history:
        counts[act] = counts.get(act, 0) + 1
        
    entropy = 0.0
    for count in counts.values():
        p = count / total
        if p > 0:
            entropy -= p * math.log2(p)
    return entropy

def energy_efficiency(energy_gained: float, energy_cost: float) -> float:
    """
    Calculate energy efficiency ratio: energy_gained / max(1e-5, energy_cost).
    """
    return float(energy_gained) / max(1e-5, float(energy_cost))

def ANNEX(all_agents: List[Any], current_generation: int, innovation_birth: Dict[int, int], persistence_threshold: int = 500) -> float:
    """
    Accumulated Novelty / Network Expansion Index (ANNEX).
    Measures count of active innovations that have persisted >= persistence_threshold generations.
    """
    if not all_agents:
        return 0.0
    active_innovations = set()
    for agent in all_agents:
        if hasattr(agent, 'genome') and hasattr(agent.genome, 'connections'):
            for conn in agent.genome.connections.values():
                if getattr(conn, 'enabled', True):
                    active_innovations.add(conn.innovation_id)
                    
    persisted_count = 0
    for inn_id in active_innovations:
        birth_gen = innovation_birth.get(inn_id, current_generation)
        if (current_generation - birth_gen) >= persistence_threshold:
            persisted_count += 1
    return float(persisted_count)

__all__ = [
    'adaptation_speed',
    'survival_rate',
    'action_entropy',
    'energy_efficiency',
    'ANNEX'
]
