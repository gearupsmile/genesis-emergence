"""
v6_behavioral_metrics.py - Cross-validation metrics for action entropy

Implements three metrics to distinguish meaningful behavioral complexity from noise:
  1. Trajectory Diversity (DTW-proxy): Are agents actually moving differently?
  2. Phenotype Diversity: Are behavioral outcomes different across the population?
  3. Entropy Verdict: Cross-validates action entropy against the above two.

Usage:
    from genesis_engine_v6.src.v6_behavioral_metrics import (
        compute_trajectory_diversity,
        compute_phenotype_diversity,
        entropy_verdict,
        BehavioralMetrics,
    )
"""

import math
import numpy as np
from typing import List, Tuple, Dict, Any, Optional


# ---------------------------------------------------------------------------
# Trajectory recording helpers
# ---------------------------------------------------------------------------

def record_trajectory(agent, substrate, n_steps: int = 20) -> List[Tuple[float, float]]:
    """
    Simulate `n_steps` of an agent on a substrate and record its (x, y) trajectory.
    Returns a list of (x, y) positions, length = n_steps + 1 (including start).
    Does NOT mutate the agent's action_history or energy permanently.

    Note: This clones relevant agent state for measurement without side effects.
    """
    # Snapshot position and energy
    orig_x, orig_y = agent.x, agent.y
    orig_energy = agent.energy
    orig_history = list(getattr(agent, 'action_history', []))

    traj = [(float(agent.x), float(agent.y))]

    try:
        for _ in range(n_steps):
            agent.step(substrate)
            traj.append((float(agent.x), float(agent.y)))
    except Exception:
        pass

    # Restore agent state
    agent.x = orig_x
    agent.y = orig_y
    agent.energy = orig_energy
    if hasattr(agent, 'action_history'):
        agent.action_history = orig_history

    return traj


# ---------------------------------------------------------------------------
# DTW-proxy distance (Manhattan, no external dependencies)
# ---------------------------------------------------------------------------

def _dtw_distance(seq_a: List[Tuple[float, float]], seq_b: List[Tuple[float, float]]) -> float:
    """
    Compute Dynamic Time Warping distance between two 2D trajectories
    using Manhattan distance as the local cost function.

    This is an O(n*m) implementation with no external dependencies.
    For trajectory lengths <= 25 this runs in microseconds.
    """
    n, m = len(seq_a), len(seq_b)
    if n == 0 or m == 0:
        return 0.0

    # Initialize DTW matrix
    dtw = np.full((n + 1, m + 1), np.inf)
    dtw[0, 0] = 0.0

    for i in range(1, n + 1):
        for j in range(1, m + 1):
            ax, ay = seq_a[i - 1]
            bx, by = seq_b[j - 1]
            cost = abs(ax - bx) + abs(ay - by)  # Manhattan local cost
            dtw[i, j] = cost + min(dtw[i - 1, j], dtw[i, j - 1], dtw[i - 1, j - 1])

    return float(dtw[n, m])


# ---------------------------------------------------------------------------
# Trajectory Diversity
# ---------------------------------------------------------------------------

def compute_trajectory_diversity(
    population: List[Any],
    substrate,
    n_steps: int = 20,
    sample_size: int = 8
) -> float:
    """
    Compute mean pairwise DTW distance across a sample of agent trajectories.

    A high value = agents are genuinely exploring different paths (meaningful behavior).
    A low value = agents are all doing the same thing (noise / thrashing in place).

    Args:
        population: List of V6Agent instances.
        substrate: Current environment substrate.
        n_steps: Steps to simulate per trajectory recording.
        sample_size: Number of agents to sample for pairwise comparison.

    Returns:
        Mean pairwise DTW distance (float). 0.0 if <2 agents.
    """
    if len(population) < 2:
        return 0.0

    # Sample agents
    sample = population[:sample_size] if len(population) >= sample_size else list(population)

    # Record trajectories
    trajectories = []
    for agent in sample:
        traj = record_trajectory(agent, substrate, n_steps=n_steps)
        trajectories.append(traj)

    # Pairwise DTW distances
    distances = []
    for i in range(len(trajectories)):
        for j in range(i + 1, len(trajectories)):
            d = _dtw_distance(trajectories[i], trajectories[j])
            distances.append(d)

    return float(np.mean(distances)) if distances else 0.0


# ---------------------------------------------------------------------------
# Phenotype Diversity
# ---------------------------------------------------------------------------

def _agent_phenotype(agent) -> np.ndarray:
    """
    Compute a behavioral phenotype vector for an agent.
    Phenotype = (final_energy, total_move_steps, secretion_count, idle_count, unique_positions_fraction)

    All values are normalized to [0, 1] range.
    """
    history = getattr(agent, 'action_history', [])
    total = len(history) if history else 1

    move_count = history.count('M') if history else 0
    secrete_count = history.count('S') if history else 0
    idle_count = history.count('I') if history else 0

    energy = float(np.clip(getattr(agent, 'energy', 0.0), 0.0, 10.0) / 10.0)

    return np.array([
        energy,
        move_count / total,
        secrete_count / total,
        idle_count / total,
    ], dtype=np.float32)


def compute_phenotype_diversity(population: List[Any]) -> float:
    """
    Compute mean pairwise Euclidean distance between agent phenotype vectors.

    High value = agents are behaviorally diverse (different energy, movement strategies).
    Low value = all agents behave the same way (collapsed population, noise attractor).

    Returns:
        Mean pairwise phenotype distance (float).
    """
    if len(population) < 2:
        return 0.0

    phenotypes = [_agent_phenotype(a) for a in population]

    distances = []
    for i in range(len(phenotypes)):
        for j in range(i + 1, len(phenotypes)):
            d = float(np.linalg.norm(phenotypes[i] - phenotypes[j]))
            distances.append(d)

    return float(np.mean(distances)) if distances else 0.0


# ---------------------------------------------------------------------------
# Entropy Cross-Validation Verdict
# ---------------------------------------------------------------------------

def entropy_verdict(
    action_entropy_val: float,
    trajectory_diversity: float,
    phenotype_diversity: float,
    entropy_threshold: float = 1.0,
    traj_threshold: float = 1.5,
    pheno_threshold: float = 0.05,
) -> str:
    """
    Cross-validate action entropy against trajectory and phenotype diversity.

    Rules:
      - HIGH entropy + LOW trajectory diversity + LOW phenotype diversity → "NOISE"
        (Agent is thrashing: lots of S/M/I switching, but going nowhere different)
      - HIGH entropy + HIGH trajectory OR phenotype diversity → "GENUINE"
        (Agent is genuinely exploring: high switching reflects diverse strategies)
      - LOW entropy → "LOW_COMPLEXITY"
        (Agent is behaving consistently — may be specialized or stuck)

    Args:
        action_entropy_val: Shannon entropy of S/M/I actions.
        trajectory_diversity: Mean pairwise DTW distance.
        phenotype_diversity: Mean pairwise phenotype distance.
        entropy_threshold: Entropy above this is considered "high."
        traj_threshold: Trajectory diversity above this = meaningful exploration.
        pheno_threshold: Phenotype diversity above this = meaningful outcome variation.

    Returns:
        'NOISE' | 'GENUINE' | 'LOW_COMPLEXITY'
    """
    high_entropy = action_entropy_val >= entropy_threshold
    high_traj = trajectory_diversity >= traj_threshold
    high_pheno = phenotype_diversity >= pheno_threshold

    if not high_entropy:
        return 'LOW_COMPLEXITY'
    if high_entropy and not high_traj and not high_pheno:
        return 'NOISE'
    return 'GENUINE'


# ---------------------------------------------------------------------------
# Combined metrics bundle
# ---------------------------------------------------------------------------

class BehavioralMetrics:
    """
    Convenience class that computes all behavioral cross-validation metrics at once.

    Usage:
        bm = BehavioralMetrics()
        result = bm.evaluate(population, substrate, action_entropy_val)
        print(result['EntropyVerdict'])  # 'NOISE' | 'GENUINE' | 'LOW_COMPLEXITY'
    """

    def __init__(
        self,
        traj_steps: int = 20,
        traj_sample: int = 8,
        entropy_threshold: float = 1.0,
        traj_threshold: float = 1.5,
        pheno_threshold: float = 0.05,
    ):
        self.traj_steps = traj_steps
        self.traj_sample = traj_sample
        self.entropy_threshold = entropy_threshold
        self.traj_threshold = traj_threshold
        self.pheno_threshold = pheno_threshold

    def evaluate(
        self,
        population: List[Any],
        substrate,
        action_entropy_val: float,
    ) -> Dict[str, Any]:
        """
        Evaluate all behavioral metrics for a population.

        Returns a dict with:
            TrajDiversity    - float: mean pairwise DTW distance
            PhenotypeDiversity - float: mean pairwise phenotype distance
            EntropyVerdict   - str: 'NOISE' | 'GENUINE' | 'LOW_COMPLEXITY'
        """
        traj_div = compute_trajectory_diversity(
            population, substrate,
            n_steps=self.traj_steps,
            sample_size=self.traj_sample
        )
        pheno_div = compute_phenotype_diversity(population)
        verdict = entropy_verdict(
            action_entropy_val, traj_div, pheno_div,
            entropy_threshold=self.entropy_threshold,
            traj_threshold=self.traj_threshold,
            pheno_threshold=self.pheno_threshold,
        )

        return {
            'TrajDiversity': round(traj_div, 4),
            'PhenotypeDiversity': round(pheno_div, 4),
            'EntropyVerdict': verdict,
        }


__all__ = [
    'record_trajectory',
    'compute_trajectory_diversity',
    'compute_phenotype_diversity',
    'entropy_verdict',
    'BehavioralMetrics',
]
