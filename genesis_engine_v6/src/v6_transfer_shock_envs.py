"""
v6_transfer_shock_envs.py - Phase 3 Transfer Shock Environments

Three QUALITATIVELY different environments that replace the Phase 2
Gray-Scott parameter-shift shocks. Each shock represents a different
functional physics basin, not just a parameter adjustment.

Shock A — Pressure Wave Substrate (Cross-Substrate Transfer)
    Replaces Gray-Scott reaction-diffusion with a sinusoidal pressure
    gradient field. Agents must navigate pressure maxima for energy.
    Cannot be solved by "pump legs faster" — the entire input semantics change.

Shock B — POET-Style Barrier Shock (Topological Shift)
    Hard impassable wall at x = width//2, with a single navigable gap
    at y ∈ [height//2 - GAP_HALF, height//2 + GAP_HALF]. Agents on the
    wrong side die unless they find the gap. 12-node walkers fail; complex
    spatially-aware agents can learn the gap.

Shock C — Sensor Blinding Shock (Dropout)
    Keeps Gray-Scott substrate but applies 70% per-step gradient input
    dropout, plus 50-step full-blind bursts every 200 steps. Complex agents
    with redundant pathways survive; sparse 12-node agents cannot.
"""

import math
import numpy as np
from typing import Dict, Any, Optional, Tuple

# ---------------------------------------------------------------------------
# Shock A — Pressure Wave Substrate
# ---------------------------------------------------------------------------

class PressureWaveSubstrate:
    """
    A 2D pressure gradient field that replaces Gray-Scott chemistry.

    Physics:
        P(x, y, t) = sin(2π·x/W) · cos(2π·y/H) · (0.5 + 0.5·sin(0.05·t))

    Agents gain energy by being at local pressure maxima (P > 0.5).
    They lose energy at pressure minima (P < -0.5).
    The wave oscillates over time, so optimal positions shift.

    Sensory inputs provided to agents (replaces U, V, S gradients):
        - Px gradient (∂P/∂x at agent location)
        - Py gradient (∂P/∂y at agent location)
        - P value at agent location
        (V and S fields are zeroed; agents must adapt to new input mapping)

    This is a genuine functional shift: the input semantics completely change.
    """
    env_type: str = 'pressure_wave'
    shock_id: str = 'Shock_A'

    def __init__(self, width: int = 50, height: int = 50):
        self.width = width
        self.height = height
        self.step_count = 0

        # Coordinate grids
        xs = np.linspace(0, 2 * math.pi, width, endpoint=False)
        ys = np.linspace(0, 2 * math.pi, height, endpoint=False)
        self.Xg, self.Yg = np.meshgrid(xs, ys)  # shape (H, W)

        # Initialize fields — agents use U as pressure, V and S as zero
        self.U = self._compute_pressure(0)
        self.V = np.zeros((height, width), dtype=np.float32)
        self.S = np.zeros((height, width), dtype=np.float32)

        # Substrate metadata used by AnnexTracker hashing
        self.F = 0.0    # not used; placeholder for substrate interface compat
        self.k = 0.0
        self.diff_u = 1.0
        self.diff_v = 0.0

    def _compute_pressure(self, t: int) -> np.ndarray:
        """Compute instantaneous pressure field."""
        temporal = 0.5 + 0.5 * math.sin(0.05 * t)
        P = np.sin(self.Xg) * np.cos(self.Yg) * temporal
        return P.astype(np.float32)

    def step(self):
        """Advance pressure wave by one time step."""
        self.step_count += 1
        self.U = self._compute_pressure(self.step_count)

    def get_energy_at(self, x: int, y: int) -> float:
        """
        Energy intake at position (x, y).
        Positive at pressure maxima, negative at minima.
        """
        p_val = float(self.U[int(y) % self.height, int(x) % self.width])
        if p_val > 0.5:
            return 0.4   # High pressure zone — energy reward
        elif p_val < -0.5:
            return -0.15  # Low pressure zone — energy penalty
        return 0.05       # Neutral zone — small passive intake

    def deposit_secretion(self, x: int, y: int, amount: float):
        """No-op for pressure substrate (secretion has no effect)."""
        pass


def generate_shock_env_A() -> Dict[str, Any]:
    """
    Shock A descriptor dict for use with AnnexTracker hashing.
    The actual substrate is PressureWaveSubstrate.
    """
    return {
        'id': 'Shock_A',
        'name': 'Shock A (Pressure Wave)',
        'env_type': 'pressure_wave',
        'F': 0.0,   # Not used in pressure wave — placeholder
        'k': 0.0,
        'D_u': 1.0,
        'D_v': 0.0,
        'description': 'Cross-substrate: sinusoidal pressure gradient field, not Gray-Scott',
        'substrate_class': 'PressureWaveSubstrate',
    }


# ---------------------------------------------------------------------------
# Shock B — POET-Style Barrier Substrate
# ---------------------------------------------------------------------------

class BarrierSubstrate:
    """
    Gray-Scott substrate with a HARD impassable vertical barrier at x = width//2.
    A single navigable gap exists at y ∈ [gap_center - gap_half, gap_center + gap_half].

    Agents on the resource-poor side (x < wall_x) face 10× faster energy decay.
    Agents must learn to find the gap to reach the resource-rich side (x >= wall_x).

    The 12-node naive agent uses a simple gradient-following strategy that
    cannot discover the gap — it will hit the wall and starve.
    Complex agents (52+ nodes) with spatial representation can learn gap location.

    Wall mechanics:
        - Any move that would cross x = wall_x is blocked (agent stays put).
        - Exception: y ∈ [gap_center - gap_half, gap_center + gap_half] — gap is open.
        - Gray-Scott V-field energy is concentrated on the rich side (x >= wall_x).
    """
    env_type: str = 'barrier_gs'
    shock_id: str = 'Shock_B'

    GAP_HALF: int = 3        # Gap width = 2*GAP_HALF + 1 = 7 cells
    WALL_PENALTY: float = 0.05  # Additional energy cost per step on wrong side

    def __init__(
        self,
        width: int = 50,
        height: int = 50,
        gap_half: int = 3,
    ):
        from genesis_engine_v6.src.v6_substrate import V6Substrate

        self.width = width
        self.height = height
        self.wall_x = width // 2
        self.gap_center = height // 2
        self.gap_half = gap_half

        # Standard Gray-Scott parameters (moderate challenge)
        base_f = 0.037
        base_k = 0.060
        f_map = np.full((height, width), base_f, dtype=np.float32)
        k_map = np.full((height, width), base_k, dtype=np.float32)
        diff_u_map = np.full((height, width), 0.16, dtype=np.float32)
        diff_v_map = np.full((height, width), 0.08, dtype=np.float32)

        # Boost V-field resources on the rich side (x >= wall_x)
        self._gs = V6Substrate(
            width=width, height=height,
            f_map=f_map, k_map=k_map,
            diff_u_map=diff_u_map, diff_v_map=diff_v_map
        )
        # Seed higher V concentration on rich side
        self._gs.V[:, self.wall_x:] *= 2.0
        self._gs.V[:, :self.wall_x] *= 0.1

        # For AnnexTracker hashing
        self.f = f_map
        self.k = k_map
        self.diff_u = diff_u_map
        self.diff_v = diff_v_map

        self.step_count = 0

    @property
    def U(self) -> np.ndarray:
        return self._gs.U

    @property
    def V(self) -> np.ndarray:
        return self._gs.V

    @property
    def S(self) -> np.ndarray:
        return self._gs.S

    def is_in_gap(self, y: int) -> bool:
        """True if y position is within the navigable gap."""
        return abs(int(y) - self.gap_center) <= self.gap_half

    def apply_wall(self, agent, new_x: int, new_y: int) -> Tuple[int, int]:
        """
        Apply wall mechanics to a proposed move.
        Blocks crossing the wall except through the gap.
        Returns the (effective_x, effective_y) after wall check.
        """
        cur_x = int(agent.x) % self.width
        new_x_mod = int(new_x) % self.width

        # Detect wall crossing (moving from one side to the other)
        cur_side = cur_x >= self.wall_x
        new_side = new_x_mod >= self.wall_x

        if cur_side != new_side:
            # Crossing attempted — only allow if in gap
            if not self.is_in_gap(int(agent.y)):
                return cur_x, int(agent.y) % self.height  # Block move

        return new_x_mod, int(new_y) % self.height

    def step(self):
        """Advance Gray-Scott chemistry."""
        self.step_count += 1
        self._gs.step()

        # Maintain resource asymmetry: boost V on rich side every 10 steps
        if self.step_count % 10 == 0:
            self._gs.V[:, self.wall_x:] = np.clip(
                self._gs.V[:, self.wall_x:] * 1.02, 0, 0.9
            )

    def get_energy_at(self, x: int, y: int) -> float:
        """Standard V-field energy intake."""
        return float(self.V[int(y) % self.height, int(x) % self.width]) * 0.5

    def get_penalty_at(self, x: int) -> float:
        """Extra energy penalty on resource-poor side."""
        if int(x) % self.width < self.wall_x:
            return self.WALL_PENALTY
        return 0.0

    def deposit_secretion(self, x: int, y: int, amount: float):
        self._gs.deposit_secretion(x, y, amount)


def generate_shock_env_B(gap_half: int = 3) -> Dict[str, Any]:
    """
    Shock B descriptor dict.
    gap_half controls the navigable gap width (default 7 cells = width 3+3+1).
    """
    return {
        'id': 'Shock_B',
        'name': 'Shock B (Barrier + Gap)',
        'env_type': 'barrier_gs',
        'F': 0.037,
        'k': 0.060,
        'D_u': 0.16,
        'D_v': 0.08,
        'gap_half': gap_half,
        'description': (
            f'POET-style barrier: hard wall at x=25, single gap of width {2*gap_half+1} '
            f'at center. Wrong-side energy penalty. 12-node agents fail; '
            f'spatially-aware agents find gap.'
        ),
        'substrate_class': 'BarrierSubstrate',
    }


# ---------------------------------------------------------------------------
# Shock C — Sensor Blinding Substrate
# ---------------------------------------------------------------------------

class SensorBlindingSubstrate:
    """
    Gray-Scott substrate with aggressive sensory dropout applied at the
    agent decision level.

    Dropout mechanics:
        - Per-step: each of the 6 gradient inputs (gu_x, gu_y, gv_x, gv_y,
          gs_x, gs_y) is independently zeroed with probability DROPOUT_RATE.
        - Burst mode: every BURST_INTERVAL steps, a full 50-step blind burst
          applies 95% dropout (all inputs near-zeroed simultaneously).

    Agents with redundant latent pathways (many nodes, dense edges) can still
    navigate using the few unblinded inputs or by relying on position/energy.
    12-node agents with a single direct input→output path collapse immediately
    when their primary gradient channel is blinded.
    """
    env_type: str = 'sensor_blind_gs'
    shock_id: str = 'Shock_C'

    DROPOUT_RATE: float = 0.70      # Per-input dropout probability
    BURST_INTERVAL: int = 200       # Steps between blind burst onset
    BURST_DURATION: int = 50        # Duration of each blind burst
    BURST_DROPOUT: float = 0.95     # Dropout rate during bursts

    def __init__(self, width: int = 50, height: int = 50, rng_seed: int = 42):
        from genesis_engine_v6.src.v6_substrate import V6Substrate

        self.width = width
        self.height = height
        self._rng = np.random.RandomState(rng_seed)
        self.step_count = 0
        self._in_burst = False

        base_f = 0.037
        base_k = 0.060
        f_map = np.full((height, width), base_f, dtype=np.float32)
        k_map = np.full((height, width), base_k, dtype=np.float32)
        diff_u_map = np.full((height, width), 0.16, dtype=np.float32)
        diff_v_map = np.full((height, width), 0.08, dtype=np.float32)

        self._gs = V6Substrate(
            width=width, height=height,
            f_map=f_map, k_map=k_map,
            diff_u_map=diff_u_map, diff_v_map=diff_v_map
        )

        # For AnnexTracker hashing
        self.f = f_map
        self.k = k_map
        self.diff_u = diff_u_map
        self.diff_v = diff_v_map

    @property
    def U(self) -> np.ndarray:
        return self._gs.U

    @property
    def V(self) -> np.ndarray:
        return self._gs.V

    @property
    def S(self) -> np.ndarray:
        return self._gs.S

    def step(self):
        """Advance chemistry and update burst state."""
        self.step_count += 1
        self._gs.step()

        # Update burst mode
        cycle_pos = self.step_count % self.BURST_INTERVAL
        self._in_burst = (cycle_pos < self.BURST_DURATION)

    def apply_sensory_dropout(self, gradients: tuple) -> tuple:
        """
        Apply dropout to a tuple of 6 gradient inputs.
        Returns masked gradients (zeroed inputs = blinded sensors).

        Args:
            gradients: (gu_x, gu_y, gv_x, gv_y, gs_x, gs_y)

        Returns:
            Masked tuple of same length.
        """
        dropout_rate = self.BURST_DROPOUT if self._in_burst else self.DROPOUT_RATE
        result = []
        for val in gradients:
            if self._rng.random() < dropout_rate:
                result.append(0.0)  # Sensor blinded
            else:
                result.append(val)
        return tuple(result)

    def get_energy_at(self, x: int, y: int) -> float:
        return float(self.V[int(y) % self.height, int(x) % self.width]) * 0.5

    def deposit_secretion(self, x: int, y: int, amount: float):
        self._gs.deposit_secretion(x, y, amount)

    def is_in_burst(self) -> bool:
        return self._in_burst


def generate_shock_env_C() -> Dict[str, Any]:
    """Shock C descriptor dict."""
    return {
        'id': 'Shock_C',
        'name': 'Shock C (Sensor Blinding)',
        'env_type': 'sensor_blind_gs',
        'F': 0.037,
        'k': 0.060,
        'D_u': 0.16,
        'D_v': 0.08,
        'dropout_rate': SensorBlindingSubstrate.DROPOUT_RATE,
        'burst_interval': SensorBlindingSubstrate.BURST_INTERVAL,
        'description': (
            '70% per-step gradient dropout + 50-step 95%-dropout bursts every 200 steps. '
            'Forces agents to rely on redundant latent pathways.'
        ),
        'substrate_class': 'SensorBlindingSubstrate',
    }


__all__ = [
    # Shock A
    'PressureWaveSubstrate',
    'generate_shock_env_A',
    # Shock B
    'BarrierSubstrate',
    'generate_shock_env_B',
    # Shock C
    'SensorBlindingSubstrate',
    'generate_shock_env_C',
]
