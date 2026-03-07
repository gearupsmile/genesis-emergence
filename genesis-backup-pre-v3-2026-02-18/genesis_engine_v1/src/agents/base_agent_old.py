"""
Minimal agent implementation for emergence experiments.

Agents have the simplest possible behavior:
- Sense local U concentration (energy)
- Move toward higher U gradients
- Consume U to gain energy
- Lose energy over time (metabolism)
- Reproduce when energy > threshold
- Die when energy <= 0

No complex behaviors, neural networks, or pre-programmed strategies.
Pure emergence from simple survival rules.
"""

import numpy as np
from typing import Tuple, Optional


class Agent:
    """Minimal agent with pure survival behavior."""
    
    # Class-level parameters (tuned for sustainable populations)
    ENERGY_START = 100.0
    ENERGY_METABOLISM = 0.3  # Reduced from 0.5
    ENERGY_CONSUMPTION_RATE = 5.0  # Increased from 2.0
    ENERGY_REPRODUCTION_THRESHOLD = 120.0  # Reduced from 150.0
    ENERGY_REPRODUCTION_COST = 40.0  # Reduced from 50.0
    MOVEMENT_SPEED = 1.0  # Pixels per cycle
    SENSING_RADIUS = 5.0  # Radius for U sensing
    
    def __init__(self, x: float, y: float, energy: Optional[float] = None, custom_params: Optional[Dict] = None):
        """Initialize agent at position with energy.
        
        Args:
            x: X position (float for sub-pixel precision)
            y: Y position (float for sub-pixel precision)
            energy: Starting energy (defaults to ENERGY_START)
            custom_params: Optional dict to override class-level parameters
                          Keys: metabolism, consumption_rate, reproduction_threshold, reproduction_cost
        """
        self.x = x
        self.y = y
        self.energy = energy if energy is not None else self.ENERGY_START
        self.age = 0
        self.alive = True
        
        # Override class-level parameters if custom_params provided
        if custom_params:
            self.ENERGY_METABOLISM = custom_params.get('metabolism', self.ENERGY_METABOLISM)
            self.ENERGY_CONSUMPTION_RATE = custom_params.get('consumption_rate', self.ENERGY_CONSUMPTION_RATE)
            self.ENERGY_REPRODUCTION_THRESHOLD = custom_params.get('reproduction_threshold', self.ENERGY_REPRODUCTION_THRESHOLD)
            self.ENERGY_REPRODUCTION_COST = custom_params.get('reproduction_cost', self.ENERGY_REPRODUCTION_COST)
        
        # Statistics
        self.total_consumed = 0.0
        self.offspring_count = 0
    
    def sense_gradient(self, U: np.ndarray) -> Tuple[float, float]:
        """Sense U gradient in local neighborhood.
        
        Uses simple 4-direction sampling to find gradient direction.
        
        Args:
            U: U concentration field (2D array)
            
        Returns:
            (dx, dy) normalized gradient direction
        """
        height, width = U.shape
        
        # Current position (with bounds checking)
        cx = int(np.clip(self.x, 0, width - 1))
        cy = int(np.clip(self.y, 0, height - 1))
        
        # Sample in 4 directions
        radius = int(self.SENSING_RADIUS)
        
        # North
        ny = max(0, cy - radius)
        north = U[ny, cx]
        
        # South
        sy = min(height - 1, cy + radius)
        south = U[sy, cx]
        
        # West
        wx = max(0, cx - radius)
        west = U[cy, wx]
        
        # East
        ex = min(width - 1, cx + radius)
        east = U[cy, ex]
        
        # Compute gradient
        dx = east - west
        dy = south - north  # Inverted because y increases downward
        
        # Normalize
        magnitude = np.sqrt(dx**2 + dy**2)
        if magnitude > 0:
            dx /= magnitude
            dy /= magnitude
        
        return dx, dy
    
    def move(self, U: np.ndarray, bounds: Tuple[int, int]) -> None:
        """Move toward higher U concentration.
        
        Args:
            U: U concentration field
            bounds: (height, width) of the field
        """
        if not self.alive:
            return
        
        # Sense gradient
        dx, dy = self.sense_gradient(U)
        
        # Move in gradient direction
        self.x += dx * self.MOVEMENT_SPEED
        self.y += dy * self.MOVEMENT_SPEED
        
        # Wrap around boundaries (periodic)
        height, width = bounds
        self.x = self.x % width
        self.y = self.y % height
    
    def consume_energy(self, U: np.ndarray) -> float:
        """Consume U at current position to gain energy.
        
        Args:
            U: U concentration field (will be modified)
            
        Returns:
            Amount of U consumed
        """
        if not self.alive:
            return 0.0
        
        height, width = U.shape
        
        # Get current grid position
        x = int(np.clip(self.x, 0, width - 1))
        y = int(np.clip(self.y, 0, height - 1))
        
        # Consume available U (limited by what's there)
        available_U = U[y, x]
        consumption = min(available_U, 0.1)  # Max 0.1 U per cycle
        
        # Remove from field
        U[y, x] -= consumption
        
        # Gain energy
        energy_gained = consumption * self.ENERGY_CONSUMPTION_RATE
        self.energy += energy_gained
        self.total_consumed += consumption
        
        return consumption
    
    def metabolize(self) -> None:
        """Lose energy due to metabolism."""
        if not self.alive:
            return
        
        self.energy -= self.ENERGY_METABOLISM
        self.age += 1
        
        # Check for death
        if self.energy <= 0:
            self.alive = False
            self.energy = 0
    
    def can_reproduce(self) -> bool:
        """Check if agent has enough energy to reproduce.
        
        Returns:
            True if energy > threshold
        """
        return self.alive and self.energy >= self.ENERGY_REPRODUCTION_THRESHOLD
    
    def reproduce(self) -> 'Agent':
        """Create offspring by splitting energy.
        
        Returns:
            New agent (offspring) at nearby position
        """
        if not self.can_reproduce():
            return None
        
        # Split energy
        self.energy -= self.ENERGY_REPRODUCTION_COST
        
        # Create offspring at nearby position (small random offset)
        offset_x = np.random.uniform(-5, 5)
        offset_y = np.random.uniform(-5, 5)
        
        # Build custom_params dict from current instance values
        custom_params = {
            'metabolism': self.ENERGY_METABOLISM,
            'consumption_rate': self.ENERGY_CONSUMPTION_RATE,
            'reproduction_threshold': self.ENERGY_REPRODUCTION_THRESHOLD,
            'reproduction_cost': self.ENERGY_REPRODUCTION_COST
        }
        
        offspring = Agent(
            x=self.x + offset_x,
            y=self.y + offset_y,
            energy=self.ENERGY_REPRODUCTION_COST,
            custom_params=custom_params
        )
        
        self.offspring_count += 1
        
        return offspring
    
    def get_position(self) -> Tuple[float, float]:
        """Get current position.
        
        Returns:
            (x, y) position
        """
        return self.x, self.y
    
    def get_energy_ratio(self) -> float:
        """Get energy as ratio of starting energy.
        
        Returns:
            Energy ratio (0.0 to 2.0+)
        """
        return self.energy / self.ENERGY_START
    
    def __repr__(self) -> str:
        """String representation."""
        status = "alive" if self.alive else "dead"
        return f"Agent(pos=({self.x:.1f}, {self.y:.1f}), energy={self.energy:.1f}, {status})"
