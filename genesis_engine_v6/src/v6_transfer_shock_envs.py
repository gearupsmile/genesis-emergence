"""
v6_transfer_shock_envs.py - Reaction-diffusion transfer shock environments for Phase 2
"""

import math
import numpy as np
from typing import Dict, Any
from genesis_engine_v6.src.v6_substrate import V6Substrate

def generate_shock_env_A() -> Dict[str, Any]:
    """
    Shock A: High diffusion, low feed
    High spatial spread rate with low resource replenishment.
    """
    return {
        'id': 'Shock_A',
        'name': 'Shock A',
        'D_u': 0.32,
        'D_v': 0.16,
        'F': 0.02,
        'k': 0.065,
        'description': 'High diffusion, low feed'
    }

def generate_shock_env_B() -> Dict[str, Any]:
    """
    Shock B: Low diffusion, high kill
    Concentrated spatial patches with harsh decay rates.
    """
    return {
        'id': 'Shock_B',
        'name': 'Shock B',
        'D_u': 0.04,
        'D_v': 0.02,
        'F': 0.035,
        'k': 0.12,
        'description': 'Low diffusion, high kill'
    }

def generate_shock_env_C() -> Dict[str, Any]:
    """
    Shock C: Chaotic regime with temporal variation
    Oscillating feed and kill parameters simulating seasonal/chaotic shifts.
    """
    return {
        'id': 'Shock_C',
        'name': 'Shock C',
        'D_u': 0.12,
        'D_v': 0.06,
        'F': 0.018,
        'k': 0.050,
        'description': 'Chaotic regime with temporal variation'
    }

class TransferShockSubstrate(V6Substrate):
    """
    Substrate tailored for transfer shock environments.
    Supports fixed and temporally varying Gray-Scott parameters.
    """
    def __init__(self, shock_spec: Dict[str, Any], width: int = 50, height: int = 50):
        self.shock_spec = shock_spec
        self.step_count = 0
        
        base_f = shock_spec['F']
        base_k = shock_spec['k']
        diff_u_val = shock_spec['D_u']
        diff_v_val = shock_spec['D_v']

        f_map = np.full((height, width), base_f, dtype=np.float32)
        k_map = np.full((height, width), base_k, dtype=np.float32)
        diff_u_map = np.full((height, width), diff_u_val, dtype=np.float32)
        diff_v_map = np.full((height, width), diff_v_val, dtype=np.float32)

        super().__init__(
            width=width,
            height=height,
            f_map=f_map,
            k_map=k_map,
            diff_u_map=diff_u_map,
            diff_v_map=diff_v_map
        )

    def step(self):
        """
        Advances chemical diffusion/reaction.
        If Shock C (temporal variation), oscillates F and k parameters smoothly over time.
        """
        self.step_count += 1
        if self.shock_spec['id'] == 'Shock_C':
            # Temporal sine wave oscillation: period ~ 200 steps
            osc = 0.005 * math.sin(self.step_count * 0.0314)
            base_f = self.shock_spec['F'] + osc
            base_k = self.shock_spec['k'] + (osc * 0.5)
            self.f.fill(max(0.005, min(0.09, base_f)))
            self.k.fill(max(0.01, min(0.15, base_k)))

        super().step()

__all__ = [
    'generate_shock_env_A',
    'generate_shock_env_B',
    'generate_shock_env_C',
    'TransferShockSubstrate'
]
