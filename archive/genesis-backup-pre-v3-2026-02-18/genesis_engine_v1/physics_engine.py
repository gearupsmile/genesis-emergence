"""
Numerically stable Gray-Scott reaction-diffusion physics engine.

This module implements the Gray-Scott model with extensive numerical stability
features to ensure reliable long-running simulations (10,000+ cycles).
"""

import numpy as np
from typing import Tuple, Optional, Dict
from parameters import GrayScottParams
import warnings


class GrayScottEngine:
    """Numerically stable Gray-Scott reaction-diffusion engine.
    
    The Gray-Scott model describes two chemicals U and V that react and diffuse:
        ∂U/∂t = Du∇²U - UV² + F(1-U)
        ∂V/∂t = Dv∇²V + UV² - (F+k)V
    
    This implementation includes:
    - Overflow/underflow protection
    - NaN/Infinity detection
    - Mass conservation tracking
    - Adaptive stability checks
    """
    
    def __init__(
        self,
        params: GrayScottParams,
        grid_size: Tuple[int, int],
        enable_checks: bool = True
    ):
        """Initialize the physics engine.
        
        Args:
            params: Gray-Scott parameters
            grid_size: (height, width) of the simulation grid
            enable_checks: Enable numerical stability checks (recommended)
        """
        self.params = params
        self.height, self.width = grid_size
        self.enable_checks = enable_checks
        
        # State arrays (double precision for stability)
        self.U = np.ones((self.height, self.width), dtype=np.float64)
        self.V = np.zeros((self.height, self.width), dtype=np.float64)
        
        # Temporary arrays for computation (avoid reallocation)
        self._U_new = np.zeros_like(self.U)
        self._V_new = np.zeros_like(self.V)
        
        # Laplacian kernel for diffusion (5-point stencil)
        self._laplacian_kernel = np.array([
            [0.0, 1.0, 0.0],
            [1.0, -4.0, 1.0],
            [0.0, 1.0, 0.0]
        ], dtype=np.float64)
        
        # Statistics tracking
        self.cycle_count = 0
        self.total_mass_initial = 0.0
        self.stability_warnings = 0
        
    def set_initial_conditions(self, U: np.ndarray, V: np.ndarray) -> None:
        """Set initial chemical concentrations.
        
        Args:
            U: Initial U concentration (height x width)
            V: Initial V concentration (height x width)
        """
        if U.shape != (self.height, self.width):
            raise ValueError(f"U shape {U.shape} doesn't match grid {(self.height, self.width)}")
        if V.shape != (self.height, self.width):
            raise ValueError(f"V shape {V.shape} doesn't match grid {(self.height, self.width)}")
        
        # Copy and ensure valid range
        self.U = np.clip(U.astype(np.float64), 0.0, 1.0)
        self.V = np.clip(V.astype(np.float64), 0.0, 1.0)
        
        # Track initial mass for conservation checks
        self.total_mass_initial = np.sum(self.U) + np.sum(self.V)
        self.cycle_count = 0
        self.stability_warnings = 0
        
    def _compute_laplacian(self, field: np.ndarray) -> np.ndarray:
        """Compute Laplacian with periodic boundary conditions.
        
        Args:
            field: 2D array to compute Laplacian of
            
        Returns:
            Laplacian of the field
        """
        # Use scipy's convolve for efficiency with periodic boundaries
        from scipy.ndimage import convolve
        return convolve(field, self._laplacian_kernel, mode='wrap')
    
    def _check_stability(self) -> bool:
        """Check for numerical instabilities.
        
        Returns:
            True if stable, False if instabilities detected
        """
        if not self.enable_checks:
            return True
        
        # Check for NaN or Infinity
        if np.any(~np.isfinite(self.U)) or np.any(~np.isfinite(self.V)):
            warnings.warn(f"NaN/Inf detected at cycle {self.cycle_count}")
            self.stability_warnings += 1
            return False
        
        # Check for negative values (shouldn't happen with clamping)
        if np.any(self.U < 0) or np.any(self.V < 0):
            warnings.warn(f"Negative values detected at cycle {self.cycle_count}")
            self.stability_warnings += 1
            return False
        
        # Check for extreme values
        if np.any(self.U > 2.0) or np.any(self.V > 2.0):
            warnings.warn(f"Extreme values detected at cycle {self.cycle_count}")
            self.stability_warnings += 1
            return False
        
        return True
    
    def _clamp_values(self) -> None:
        """Clamp values to physically valid range."""
        # Clamp to [0, 1] range (concentrations can't be negative or > 1)
        np.clip(self.U, 0.0, 1.0, out=self.U)
        np.clip(self.V, 0.0, 1.0, out=self.V)
        
        # Additional safety: ensure U + V <= 1.0 (conservation constraint)
        total = self.U + self.V
        overflow_mask = total > 1.0
        if np.any(overflow_mask):
            # Normalize to maintain ratio but satisfy constraint
            self.U[overflow_mask] /= total[overflow_mask]
            self.V[overflow_mask] /= total[overflow_mask]
    
    def step(self) -> bool:
        """Advance simulation by one time step.
        
        Returns:
            True if step completed successfully, False if instability detected
        """
        # Compute Laplacians for diffusion
        laplacian_U = self._compute_laplacian(self.U)
        laplacian_V = self._compute_laplacian(self.V)
        
        # Compute reaction term UV² with overflow protection
        # Clamp V before squaring to prevent overflow
        V_clamped = np.clip(self.V, 0.0, 1.0)
        V_squared = V_clamped * V_clamped
        
        # Clamp U to prevent overflow in multiplication
        U_clamped = np.clip(self.U, 0.0, 1.0)
        reaction = U_clamped * V_squared
        
        # Additional safety: clamp reaction term
        reaction = np.clip(reaction, 0.0, 1.0)
        
        # Gray-Scott equations
        # dU/dt = Du∇²U - UV² + F(1-U)
        # dV/dt = Dv∇²V + UV² - (F+k)V
        
        dU = (
            self.params.Du * laplacian_U
            - reaction
            + self.params.F * (1.0 - U_clamped)
        )
        
        dV = (
            self.params.Dv * laplacian_V
            + reaction
            - (self.params.F + self.params.k) * V_clamped
        )
        
        # Update with forward Euler (explicit time stepping)
        self._U_new[:] = U_clamped + self.params.dt * dU
        self._V_new[:] = V_clamped + self.params.dt * dV
        
        # Swap arrays (avoid copying)
        self.U, self._U_new = self._U_new, self.U
        self.V, self._V_new = self._V_new, self.V
        
        # Clamp to valid range
        self._clamp_values()
        
        # Increment cycle counter
        self.cycle_count += 1
        
        # Check stability periodically
        if self.cycle_count % 100 == 0:
            if not self._check_stability():
                return False
        
        return True
    
    def run(self, num_cycles: int, callback: Optional[callable] = None) -> bool:
        """Run simulation for multiple cycles.
        
        Args:
            num_cycles: Number of cycles to run
            callback: Optional function called after each cycle with (cycle, U, V)
            
        Returns:
            True if completed successfully, False if instability detected
        """
        for i in range(num_cycles):
            if not self.step():
                return False
            
            if callback is not None:
                callback(self.cycle_count, self.U, self.V)
        
        return True
    
    def get_statistics(self) -> Dict[str, float]:
        """Get current simulation statistics.
        
        Returns:
            Dictionary with statistics about the current state
        """
        total_mass = np.sum(self.U) + np.sum(self.V)
        mass_conservation_error = 0.0
        if self.total_mass_initial > 0:
            mass_conservation_error = abs(
                total_mass - self.total_mass_initial
            ) / self.total_mass_initial
        
        return {
            'cycle': self.cycle_count,
            'U_min': float(np.min(self.U)),
            'U_max': float(np.max(self.U)),
            'U_mean': float(np.mean(self.U)),
            'U_std': float(np.std(self.U)),
            'V_min': float(np.min(self.V)),
            'V_max': float(np.max(self.V)),
            'V_mean': float(np.mean(self.V)),
            'V_std': float(np.std(self.V)),
            'total_mass': float(total_mass),
            'mass_conservation_error': float(mass_conservation_error),
            'stability_warnings': self.stability_warnings,
        }
    
    def get_state(self) -> Tuple[np.ndarray, np.ndarray]:
        """Get current state arrays.
        
        Returns:
            Tuple of (U, V) arrays (copies)
        """
        return self.U.copy(), self.V.copy()
    
    def save_state(self, filepath: str) -> None:
        """Save current state to file.
        
        Args:
            filepath: Path to save state (NPZ format)
        """
        np.savez_compressed(
            filepath,
            U=self.U,
            V=self.V,
            cycle=self.cycle_count,
            params_F=self.params.F,
            params_k=self.params.k,
            params_Du=self.params.Du,
            params_Dv=self.params.Dv,
        )
    
    def load_state(self, filepath: str) -> None:
        """Load state from file.
        
        Args:
            filepath: Path to load state from (NPZ format)
        """
        data = np.load(filepath)
        self.U = data['U']
        self.V = data['V']
        self.cycle_count = int(data['cycle'])
        
        # Verify grid size matches
        if self.U.shape != (self.height, self.width):
            raise ValueError(
                f"Loaded state shape {self.U.shape} doesn't match "
                f"engine grid {(self.height, self.width)}"
            )
