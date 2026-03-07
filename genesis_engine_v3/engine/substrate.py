"""
Substrate - Environment Grid for Secretion Physics

Feature 1: Secretion Physics
- 3x3 Neighborhood Secretion
- Diffusion and Decay
- S Field (Secretion)
"""

import numpy as np
import random
from numba import njit
from scipy.ndimage import laplace

@njit
def _compute_diffusion_and_decay(field, width, height, diffusion_rate, decay_rate, dt):
    # This function implements a 4-neighbor diffusion and decay,
    # which is different from the laplacian-based diffusion.
    # It's assumed the user wants to switch to this Numba-optimized method.

    # First, apply decay
    field *= (1.0 - decay_rate * dt)

    # Then, apply diffusion
    new_field = np.copy(field)
    for x in range(width):
        for y in range(height):
            val = field[y, x] # Note: numpy arrays are typically (rows, cols) i.e., (height, width)
            if val > 0:
                # Simple 4-neighbor diffusion
                diff_amount = val * diffusion_rate * dt # Scale by dt
                
                # Ensure we don't diffuse more than available
                diff_amount = min(diff_amount, val)

                new_field[y, x] -= diff_amount
                share = diff_amount / 4.0
                
                # Apply to neighbors with wrap-around
                new_field[y, (x + 1) % width] += share
                new_field[y, (x - 1 + width) % width] += share # Ensure positive modulo
                new_field[(y + 1) % height, x] += share
                new_field[(y - 1 + height) % height, x] += share # Ensure positive modulo
    
    # Clamp to 0-1 range
    np.clip(new_field, 0.0, 1.0, out=new_field)
    return new_field


class Substrate:
    """
    2D Grid Substrate for chemical fields.
    
    Attributes:
        width (int): Grid width
        height (int): Grid height
        S (np.ndarray): Secretion field
        diff_S (float): Diffusion rate for S
        decay_S (float): Decay rate for S
    """
    
    def __init__(self, width: int = 100, height: int = 100, 
                 diff_S: float = 0.1, decay_S: float = 0.003,
                 enable_secretion: bool = True):
        """
        Initialize substrate with dimensions and physics parameters.
        
        Args:
            enable_secretion: If False, secretion has no effect (Sham Control)
        """
        self.width = width
        self.height = height
        self.enable_secretion = enable_secretion
        
        # Feature 1.1: Add Secretion Field S
        self.S = np.zeros((height, width), dtype=np.float32)
        
        # Placeholder for U/V if needed later (keeping consistent with user request)
        self.U = np.ones((height, width), dtype=np.float32)
        self.V = np.zeros((height, width), dtype=np.float32)
        
        self.diff_S = diff_S
        self.decay_S = decay_S
        
    def deposit_secretion(self, x: int, y: int, amount: float):
        """
        Deposit secretion at x,y with 3x3 diffusion.
        Respects enable_secretion flag (Feature 4).
        """
        if not self.enable_secretion:
            return

        # 3x3 Neighborhood
        for dy in [-1, 0, 1]:
            for dx in [-1, 0, 1]:
                nx = (x + dx) % self.width
                ny = (y + dy) % self.height
                self.S[ny, nx] += amount
        
    def diffuse_secretion(self, dt: float = 1.0):
        """
        Feature 1.2: Apply diffusion and decay to Secretion field S.
        
        dS/dt = diff_S * laplacian(S) - decay_S * S
        """
        # Calculate Laplacian for diffusion
        # mode='wrap' handles periodic boundary conditions
        lap_S = laplace(self.S, mode='wrap')
        
        # Apply Diffusion: S += diff_S * laplacian(S) * dt
        self.S += self.diff_S * lap_S * dt
        
        # Apply Decay: S *= (1 - decay_rate * dt)
        self.S *= (1.0 - self.decay_S * dt)
        
        # Clamp to 0-1 range to prevent runaway
        np.clip(self.S, 0.0, 1.0, out=self.S)

    def get_snapshot(self, x: int, y: int, radius: int = 5) -> np.ndarray:
        """
        Get local snapshot of environment around x,y.
        Handles periodic boundaries.
        """
        # This will be used in Feature 2
        # For now return S snapshot
        # Implementation of rolling/slicing for periodic boundaries involves numpy roll
        # Simplified version:
        
        padded_S = np.pad(self.S, radius, mode='wrap')
        # Adjust coordinates because of padding
        px, py = x + radius, y + radius
        return padded_S[py-radius:py+radius+1, px-radius:px+radius+1]
