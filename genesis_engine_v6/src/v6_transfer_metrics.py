"""
v6_transfer_metrics.py - Evaluation metrics for Phase 2/3 Transfer Shock Experiment

ANNEX is now decoupled from edge/node count.
It tracks unique ENVIRONMENTAL signatures, not agent architecture.
"""

import math
import hashlib
import datetime
import numpy as np
from typing import List, Dict, Any, Optional, Tuple


# ---------------------------------------------------------------------------
# Basic scalar metrics (unchanged)
# ---------------------------------------------------------------------------

def adaptation_speed(performance_curve: List[float], threshold: float = 0.8) -> int:
    """
    Generations to reach 80% of final performance.
    Returns total gens if threshold never reached.
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
    """Proportion of agents with energy >= min_energy."""
    if not population:
        return 0.0
    survivors = sum(1 for a in population if getattr(a, 'energy', 0.0) >= min_energy)
    return survivors / len(population)


def action_entropy(action_history: List[str]) -> float:
    """Shannon entropy of agent action distribution ('S', 'M', 'I')."""
    if not action_history:
        return 0.0
    total = len(action_history)
    counts: Dict[str, int] = {}
    for act in action_history:
        counts[act] = counts.get(act, 0) + 1
    entropy = 0.0
    for count in counts.values():
        p = count / total
        if p > 0:
            entropy -= p * math.log2(p)
    return entropy


def energy_efficiency(energy_gained: float, energy_cost: float) -> float:
    """Energy efficiency ratio: energy_gained / max(1e-5, energy_cost)."""
    return float(energy_gained) / max(1e-5, float(energy_cost))


# ---------------------------------------------------------------------------
# AnnexTracker — environment-hash-based novelty tracker
# ---------------------------------------------------------------------------

class AnnexTracker:
    """
    Accumulated Novel Environments eXplored (ANNEX) — corrected implementation.

    DESIGN PRINCIPLES:
    - Tracks unique ENVIRONMENTAL hashes, not agent architecture.
    - Completely blind to agent edge count, node count, or innovation IDs.
    - Goldilocks filter: accepts an environment only if survival variance > 0
      AND mean survival is between GOLDILOCKS_MIN and GOLDILOCKS_MAX.
      (Rejects trivially easy environments where all agents survive,
       and impossible environments where all agents die.)
    - Produces a step function over generations (increments when a novel
      environment is first successfully solved under Goldilocks conditions).
    - Every increment is logged with timestamp, env hash, and condition name.

    Usage:
        tracker = AnnexTracker(condition_name="Condition B (V6 Constrained 52 nodes)")
        is_novel = tracker.record(substrate, population, generation)
        print(tracker.count)       # step-function count
        print(tracker.get_log())   # full increment log
    """

    GOLDILOCKS_MIN: float = 0.05   # Reject if all-dead (too hard)
    GOLDILOCKS_MAX: float = 0.95   # Reject if all-survive (too easy)

    def __init__(self, condition_name: str = "Unknown", persistence_threshold: int = 500):
        self.condition_name = condition_name
        self.persistence_threshold = persistence_threshold
        self.count: int = 0
        self._seen_hashes: set = set()
        self._increment_log: List[Dict[str, Any]] = []

    # ------------------------------------------------------------------
    # Environment fingerprinting — based purely on physics, not agents
    # ------------------------------------------------------------------

    @staticmethod
    def _env_hash(substrate) -> str:
        """
        Compute a deterministic SHA256 hash of the environment's physics parameters.
        Rounded to 4 decimal places to allow small floating-point drift.
        Completely independent of agent internal state.
        """
        # Support both dict-based shock specs and substrate objects
        if isinstance(substrate, dict):
            f_val = round(float(substrate.get('F', 0.0)), 4)
            k_val = round(float(substrate.get('k', 0.0)), 4)
            du_val = round(float(substrate.get('D_u', 0.0)), 4)
            dv_val = round(float(substrate.get('D_v', 0.0)), 4)
            shock_id = substrate.get('id', 'unknown')
        else:
            # Substrate object: read field arrays
            f_arr = getattr(substrate, 'f', None)
            k_arr = getattr(substrate, 'k', None)
            du_arr = getattr(substrate, 'diff_u', None)
            dv_arr = getattr(substrate, 'diff_v', None)
            f_val = round(float(np.mean(f_arr)) if f_arr is not None else 0.0, 4)
            k_val = round(float(np.mean(k_arr)) if k_arr is not None else 0.0, 4)
            du_val = round(float(np.mean(du_arr)) if du_arr is not None else 0.0, 4)
            dv_val = round(float(np.mean(dv_arr)) if dv_arr is not None else 0.0, 4)
            shock_id = getattr(substrate, 'shock_id', 'substrate')

        # Include shock type identifier so structurally identical but
        # semantically different environments (e.g. pressure wave vs GS)
        # get distinct hashes.
        env_type = getattr(substrate, 'env_type', shock_id if isinstance(substrate, dict) else 'gs')
        signature = f"{env_type}|f={f_val}|k={k_val}|du={du_val}|dv={dv_val}"
        return hashlib.sha256(signature.encode()).hexdigest()[:16]

    # ------------------------------------------------------------------
    # Goldilocks filter
    # ------------------------------------------------------------------

    @staticmethod
    def _goldilocks_status(population: List[Any]) -> Tuple[str, float, float]:
        """
        Evaluate whether the environment is in the Goldilocks zone.

        Returns:
            (status, mean_survival, survival_variance)
            status: 'ACCEPT' | 'REJECT_TOO_EASY' | 'REJECT_TOO_HARD'
        """
        if not population:
            return 'REJECT_TOO_HARD', 0.0, 0.0

        alive = [1.0 if getattr(a, 'energy', 0.0) >= 0.01 else 0.0 for a in population]
        mean_surv = float(np.mean(alive))
        surv_var = float(np.var(alive))

        if mean_surv <= AnnexTracker.GOLDILOCKS_MIN:
            return 'REJECT_TOO_HARD', mean_surv, surv_var
        if mean_surv >= AnnexTracker.GOLDILOCKS_MAX:
            return 'REJECT_TOO_EASY', mean_surv, surv_var
        return 'ACCEPT', mean_surv, surv_var

    # ------------------------------------------------------------------
    # Main recording method
    # ------------------------------------------------------------------

    def record(
        self,
        substrate,
        population: List[Any],
        generation: int,
        agent_id: Optional[str] = None
    ) -> Tuple[bool, str, str]:
        """
        Attempt to record this environment as a novel solved environment.

        Args:
            substrate: Environment substrate object or dict spec.
            population: Current agent population.
            generation: Current generation number.
            agent_id: Optional agent/condition identifier for logging.

        Returns:
            (is_novel, goldilocks_status, env_hash)
        """
        env_hash = self._env_hash(substrate)
        goldilocks, mean_surv, surv_var = self._goldilocks_status(population)

        is_novel = False
        annex_increment = False

        if goldilocks == 'ACCEPT' and env_hash not in self._seen_hashes:
            self._seen_hashes.add(env_hash)
            self.count += 1
            is_novel = True
            annex_increment = True

        # Log every evaluation (accept or reject) for debugging
        self._increment_log.append({
            'timestamp': datetime.datetime.utcnow().isoformat(),
            'generation': generation,
            'condition': self.condition_name,
            'agent_id': agent_id or 'population',
            'env_hash': env_hash,
            'goldilocks_status': goldilocks,
            'mean_survival': round(mean_surv, 4),
            'survival_variance': round(surv_var, 4),
            'is_novel_env': is_novel,
            'annex_increment': annex_increment,
            'annex_count_after': self.count,
        })

        return is_novel, goldilocks, env_hash

    def get_log(self) -> List[Dict[str, Any]]:
        """Return the full increment/evaluation log."""
        return list(self._increment_log)

    def get_increments_only(self) -> List[Dict[str, Any]]:
        """Return only the log entries where ANNEX actually incremented."""
        return [e for e in self._increment_log if e['annex_increment']]

    def __repr__(self) -> str:
        return (f"AnnexTracker(condition={self.condition_name!r}, "
                f"count={self.count}, seen_envs={len(self._seen_hashes)})")


# ---------------------------------------------------------------------------
# Legacy functional wrapper — DEPRECATED, kept for backward compat only
# ---------------------------------------------------------------------------

def ANNEX(all_agents: List[Any], current_generation: int,
          innovation_birth: Dict[int, int], persistence_threshold: int = 500) -> float:
    """
    DEPRECATED: This function counts agent innovation IDs, NOT environmental novelty.
    It is retained for backward compatibility with old experiment runners only.
    Use AnnexTracker.record() for all new experiments.

    Returns 0.0 to force callers to migrate.
    """
    import warnings
    warnings.warn(
        "ANNEX() functional form is deprecated and returns 0.0. "
        "Use AnnexTracker for correct environmental novelty tracking.",
        DeprecationWarning,
        stacklevel=2
    )
    return 0.0


__all__ = [
    'adaptation_speed',
    'survival_rate',
    'action_entropy',
    'energy_efficiency',
    'AnnexTracker',
    'ANNEX',  # deprecated
]
