"""
v6_metrics.py - Metrics for Genesis V6
Includes:
- action_entropy(agent): Shannon entropy of agent action distribution
- gac(population, generation, birth_registry): Genetic Activity Coefficient
- ANNEX: Accumulated Novel Environments Explored tracking
"""

import math
import numpy as np
from typing import List, Dict, Set, Optional

def action_entropy(agent) -> float:
    """
    Computes the Shannon entropy of an agent's action distribution ('S', 'M', 'I').
    H = - sum(p_i * log2(p_i))
    """
    history = getattr(agent, 'action_history', [])
    if not history:
        return 0.0

    counts = {}
    for act in history:
        counts[act] = counts.get(act, 0) + 1

    total = len(history)
    if total == 0:
        return 0.0

    entropy = 0.0
    for cnt in counts.values():
        p = cnt / total
        if p > 0:
            entropy -= p * math.log2(p)

    return float(entropy)


def gac(population: List, generation: int, birth_registry: Optional[Dict[int, int]] = None,
        persistence_threshold: int = 500) -> float:
    """
    Genetic Activity Coefficient (GAC).
    Calculates the fraction of active genome edits (innovations/connections) in the population
    that have persisted for greater than persistence_threshold generations.

    Args:
        population: List of V6Agent instances
        generation: Current generation index
        birth_registry: Optional dict mapping innovation_id -> generation created
        persistence_threshold: Default 500 generations
    """
    if not population:
        return 0.0

    total_connections = 0
    persistent_connections = 0

    for agent in population:
        for conn in agent.genome.connections.values():
            if not conn.enabled:
                continue
            total_connections += 1
            birth = conn.innovation_id  # Default fallback if registry not passed
            if birth_registry and conn.innovation_id in birth_registry:
                birth = birth_registry[conn.innovation_id]

            if (generation - birth) >= persistence_threshold:
                persistent_connections += 1

    if total_connections == 0:
        return 0.0

    return float(persistent_connections / total_connections)


class ANNEX:
    """
    Accumulated Novel Environments Explored (ANNEX).
    Tracks unique environmental configurations solved/explored by agents.
    """
    def __init__(self, sim_threshold: float = 0.85):
        self.sim_threshold = sim_threshold
        self.explored_environments: List[Dict[str, np.ndarray]] = []
        self.count = 0

    def _env_signature(self, env_substrate) -> np.ndarray:
        # Combine mean property maps of Gray-Scott substrate as environmental signature
        f_mean = np.mean(getattr(env_substrate, 'f', np.zeros((1,1))))
        k_mean = np.mean(getattr(env_substrate, 'k', np.zeros((1,1))))
        u_mean = np.mean(getattr(env_substrate, 'diff_u', np.zeros((1,1))))
        v_mean = np.mean(getattr(env_substrate, 'diff_v', np.zeros((1,1))))
        return np.array([f_mean, k_mean, u_mean, v_mean], dtype=np.float32)

    def record_environment(self, env_substrate, agents_solved: bool = True) -> bool:
        if not agents_solved:
            return False

        sig = self._env_signature(env_substrate)
        is_novel = True
        for existing in self.explored_environments:
            dist = np.linalg.norm(sig - existing)
            if dist < (1.0 - self.sim_threshold):
                is_novel = False
                break

        if is_novel:
            self.explored_environments.append(sig)
            self.count += 1
            return True

        return False


def annex(environments_solved: int) -> int:
    """Convenience functional wrapper for ANNEX count."""
    return int(environments_solved)
