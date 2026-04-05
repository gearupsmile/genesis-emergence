"""
Parameter management for Gray-Scott reaction-diffusion system.

This module provides stable parameter presets for different pattern types
and validation functions to ensure numerical stability.
"""

from dataclasses import dataclass
from typing import Dict, Tuple
import numpy as np


@dataclass
class GrayScottParams:
    """Parameters for Gray-Scott reaction-diffusion system.
    
    Attributes:
        F: Feed rate (typically 0.01 - 0.08)
        k: Kill rate (typically 0.045 - 0.07)
        Du: Diffusion rate for chemical U (typically 0.16 - 0.21)
        Dv: Diffusion rate for chemical V (typically 0.08 - 0.11)
        dt: Time step (typically 1.0, adjusted for stability)
        dx: Spatial step (typically 1.0)
    """
    F: float
    k: float
    Du: float
    Dv: float
    dt: float = 1.0
    dx: float = 1.0
    
    def __post_init__(self):
        """Validate parameters after initialization."""
        self.validate()
    
    def validate(self) -> None:
        """Validate parameters for physical and numerical stability.
        
        Raises:
            ValueError: If parameters are outside valid ranges.
        """
        if self.F <= 0 or self.F > 0.2:
            raise ValueError(f"Feed rate F={self.F} outside valid range (0, 0.2]")
        if self.k <= 0 or self.k > 0.2:
            raise ValueError(f"Kill rate k={self.k} outside valid range (0, 0.2]")
        if self.Du <= 0 or self.Du > 0.5:
            raise ValueError(f"Diffusion Du={self.Du} outside valid range (0, 0.5]")
        if self.Dv <= 0 or self.Dv > 0.5:
            raise ValueError(f"Diffusion Dv={self.Dv} outside valid range (0, 0.5]")
        if self.dt <= 0 or self.dt > 2.0:
            raise ValueError(f"Time step dt={self.dt} outside valid range (0, 2.0]")
        
        # Check CFL condition for diffusion stability
        # For stability: D * dt / dx^2 < 0.5 (conservative)
        max_D = max(self.Du, self.Dv)
        cfl = max_D * self.dt / (self.dx ** 2)
        if cfl > 0.25:
            raise ValueError(
                f"CFL condition violated: {cfl:.3f} > 0.25. "
                f"Reduce dt or increase dx for stability."
            )
    
    def get_stability_info(self) -> Dict[str, float]:
        """Get stability metrics for these parameters.
        
        Returns:
            Dictionary with stability metrics.
        """
        cfl_u = self.Du * self.dt / (self.dx ** 2)
        cfl_v = self.Dv * self.dt / (self.dx ** 2)
        diffusion_ratio = self.Du / self.Dv
        
        return {
            'cfl_u': cfl_u,
            'cfl_v': cfl_v,
            'cfl_max': max(cfl_u, cfl_v),
            'diffusion_ratio': diffusion_ratio,
            'feed_kill_ratio': self.F / self.k,
        }


# Stable pattern presets from literature
# Based on Pearson's classification (1993) and extensive testing

PRESETS: Dict[str, GrayScottParams] = {
    # Mitosis pattern - stable spots that divide
    'spots': GrayScottParams(
        F=0.0367,
        k=0.0649,
        Du=0.16,
        Dv=0.08,
        dt=1.0,
        dx=1.0
    ),
    
    # Labyrinthine pattern - maze-like stripes
    'stripes': GrayScottParams(
        F=0.035,
        k=0.060,
        Du=0.16,
        Dv=0.08,
        dt=1.0,
        dx=1.0
    ),
    
    # Pulsating waves - dynamic wave patterns
    'waves': GrayScottParams(
        F=0.025,
        k=0.050,
        Du=0.16,
        Dv=0.08,
        dt=1.0,
        dx=1.0
    ),
    
    # Coral growth pattern - branching structures
    'coral': GrayScottParams(
        F=0.0545,
        k=0.062,
        Du=0.16,
        Dv=0.08,
        dt=1.0,
        dx=1.0
    ),
    
    # Spiral waves - rotating spiral patterns
    'spirals': GrayScottParams(
        F=0.018,
        k=0.051,
        Du=0.16,
        Dv=0.08,
        dt=1.0,
        dx=1.0
    ),
    
    # Moving spots - spots that drift
    'moving_spots': GrayScottParams(
        F=0.014,
        k=0.054,
        Du=0.16,
        Dv=0.08,
        dt=1.0,
        dx=1.0
    ),
}


def get_preset(name: str) -> GrayScottParams:
    """Get a parameter preset by name.
    
    Args:
        name: Name of the preset (e.g., 'spots', 'stripes', 'waves')
        
    Returns:
        GrayScottParams object with the preset parameters.
        
    Raises:
        KeyError: If preset name is not found.
    """
    if name not in PRESETS:
        available = ', '.join(PRESETS.keys())
        raise KeyError(f"Unknown preset '{name}'. Available: {available}")
    return PRESETS[name]


def list_presets() -> Dict[str, str]:
    """List all available presets with descriptions.
    
    Returns:
        Dictionary mapping preset names to descriptions.
    """
    descriptions = {
        'spots': 'Mitosis pattern - stable spots that divide',
        'stripes': 'Labyrinthine pattern - maze-like stripes',
        'waves': 'Pulsating waves - dynamic wave patterns',
        'coral': 'Coral growth pattern - branching structures',
        'spirals': 'Spiral waves - rotating spiral patterns',
        'moving_spots': 'Moving spots - spots that drift',
    }
    return descriptions


def get_initial_conditions(
    grid_size: Tuple[int, int],
    pattern: str = 'random'
) -> Tuple[np.ndarray, np.ndarray]:
    """Generate initial conditions for the simulation.
    
    Args:
        grid_size: (height, width) of the grid
        pattern: Type of initial pattern ('random', 'center_spot', 'multiple_spots')
        
    Returns:
        Tuple of (U, V) numpy arrays with initial concentrations.
    """
    height, width = grid_size
    
    # Start with U=1, V=0 everywhere (stable state)
    U = np.ones((height, width), dtype=np.float64)
    V = np.zeros((height, width), dtype=np.float64)
    
    if pattern == 'random':
        # Add random perturbations in a central region
        h_start, h_end = height // 4, 3 * height // 4
        w_start, w_end = width // 4, 3 * width // 4
        
        U[h_start:h_end, w_start:w_end] += np.random.uniform(
            -0.1, 0.1, (h_end - h_start, w_end - w_start)  # Increased from 0.05
        )
        V[h_start:h_end, w_start:w_end] += np.random.uniform(
            0.0, 0.25, (h_end - h_start, w_end - w_start)  # Increased from 0.1
        )
        
    elif pattern == 'center_spot':
        # Single spot in the center
        cy, cx = height // 2, width // 2
        radius = min(height, width) // 20
        
        y, x = np.ogrid[:height, :width]
        mask = (x - cx) ** 2 + (y - cy) ** 2 <= radius ** 2
        
        U[mask] = 0.5
        V[mask] = 0.25
        
    elif pattern == 'multiple_spots':
        # Multiple spots in a grid pattern
        spacing = min(height, width) // 8
        radius = spacing // 4
        
        for i in range(2, height - 2, spacing):
            for j in range(2, width - 2, spacing):
                y, x = np.ogrid[:height, :width]
                mask = (x - j) ** 2 + (y - i) ** 2 <= radius ** 2
                U[mask] = 0.5
                V[mask] = 0.25
    
    # Ensure values are in valid range
    U = np.clip(U, 0.0, 1.0)
    V = np.clip(V, 0.0, 1.0)
    
    return U, V
