"""
Minimal agent implementation for emergence experiments with evolvable genomes.

Agents have the simplest possible behavior:
- Sense local U concentration (energy)
- Move toward higher U gradients
- Consume U to gain energy
- Lose energy over time (metabolism)
- Reproduce when energy > threshold
- Die when energy <= 0

Agents now have EVOLVABLE GENOMES that modify how they interact
with fixed world physics (World_98).
"""

import numpy as np
from typing import Tuple, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .genome import Genome


class Agent:
    """Agent with evolvable genome."""
    
    # World_98 physics (FIXED environmental rules)
    # NOTE: These can be adjusted at runtime via set_world_baselines() for self-tuning
    WORLD_METABOLISM = 0.648
    WORLD_CONSUMPTION_RATE = 6.99
    WORLD_REPRODUCTION_THRESHOLD = 76.9
    WORLD_REPRODUCTION_COST = 86.9
    
    @classmethod
    def set_world_baselines(cls, metabolism=None, consumption=None, 
                           threshold=None, cost=None):
        """Adjust world baseline parameters (for self-tuning worlds).
        
        This allows runtime adjustment of the baseline parameters that all agents
        use to calculate their effective values (baseline × gene_multiplier).
        
        Args:
            metabolism: New metabolism baseline (clamped to 0.3-1.5)
            consumption: New consumption rate baseline (clamped to 3.0-12.0)
            threshold: New reproduction threshold baseline (clamped to 40.0-150.0)
            cost: New reproduction cost baseline (clamped to 15.0-120.0)
        """
        if metabolism is not None:
            cls.WORLD_METABOLISM = np.clip(metabolism, 0.3, 1.5)
        if consumption is not None:
            cls.WORLD_CONSUMPTION_RATE = np.clip(consumption, 3.0, 12.0)
        if threshold is not None:
            cls.WORLD_REPRODUCTION_THRESHOLD = np.clip(threshold, 40.0, 150.0)
        if cost is not None:
            cls.WORLD_REPRODUCTION_COST = np.clip(cost, 15.0, 120.0)
    
    def __init__(self, x: float, y: float, energy: float = 100.0, 
                 genome: Optional['Genome'] = None):
        """Initialize agent at position with energy and genome.
        
        Args:
            x: X position (float for sub-pixel precision)
            y: Y position (float for sub-pixel precision)
            energy: Starting energy (default: 100.0)
            genome: Genome object (creates default if None)
        """
        self.x = x
        self.y = y
        self.energy = energy
        self.age = 0
        self.alive = True
        
        # Genome determines how agent interacts with world physics
        if genome is None:
            from .genome import Genome
            self.genome = Genome()
        else:
            self.genome = genome
        
        # Statistics
        self.total_consumed = 0.0
        self.offspring_count = 0
    
    def get_effective_metabolism(self) -> float:
        """Calculate actual metabolism from world × gene multiplier."""
        return self.WORLD_METABOLISM * self.genome.genes['metabolism_multiplier']
    
    def get_effective_consumption_rate(self) -> float:
        """Calculate actual consumption rate from world × gene multiplier."""
        return self.WORLD_CONSUMPTION_RATE * self.genome.genes['consumption_multiplier']
    
    def get_effective_reproduction_threshold(self) -> float:
        """Calculate actual reproduction threshold from world × gene multiplier."""
        return self.WORLD_REPRODUCTION_THRESHOLD * self.genome.genes['reproduction_th_multiplier']
    
    def get_effective_reproduction_cost(self) -> float:
        """Calculate actual reproduction cost from world × gene multiplier."""
        return self.WORLD_REPRODUCTION_COST * self.genome.genes['reproduction_cost_multiplier']
    
    def sense_gradient(self, U: np.ndarray) -> Tuple[float, float]:
        """Sense U gradient using gene-determined sensor radius.
        
        Args:
            U: U concentration field (2D array)
            
        Returns:
            (dx, dy) normalized gradient direction
        """
        height, width = U.shape
        cx = int(np.clip(self.x, 0, width - 1))
        cy = int(np.clip(self.y, 0, height - 1))
        
        # Use gene-determined sensor radius
        radius = int(self.genome.genes['sensor_radius'])
        
        # Sample in 4 directions
        north_y = max(0, cy - radius)
        south_y = min(height - 1, cy + radius)
        west_x = max(0, cx - radius)
        east_x = min(width - 1, cx + radius)
        
        north = U[north_y, cx]
        south = U[south_y, cx]
        west = U[cy, west_x]
        east = U[cy, east_x]
        
        # Compute gradient
        dx = east - west
        dy = south - north
        
        # Normalize
        magnitude = np.sqrt(dx*dx + dy*dy)
        if magnitude > 0:
            dx /= magnitude
            dy /= magnitude
        
        return dx, dy
    
    def move(self, U: np.ndarray, bounds: Tuple[int, int]):
        """Move using gene-determined speed.
        
        Args:
            U: U concentration field
            bounds: (height, width) of the field
        """
        if not self.alive:
            return
        
        # Calculate gradient direction
        dx, dy = self.sense_gradient(U)
        
        # Use gene-determined move speed
        speed = self.genome.genes['move_speed']
        self.x += dx * speed
        self.y += dy * speed
        
        # Periodic boundaries
        height, width = bounds
        self.x = self.x % width
        self.y = self.y % height
    
    def consume_energy(self, U: np.ndarray) -> float:
        """Consume U and gain energy based on effective consumption rate.
        
        Args:
            U: U concentration field (modified in-place)
            
        Returns:
            Amount of U consumed
        """
        if not self.alive:
            return 0.0
        
        height, width = U.shape
        
        # Get grid position
        x = int(np.clip(self.x, 0, width - 1))
        y = int(np.clip(self.y, 0, height - 1))
        
        # Consume available U (limited by what's there)
        available_U = U[y, x]
        consumption = min(available_U, 0.1)  # Max 0.1 U per cycle
        
        # Remove from field
        U[y, x] -= consumption
        
        # Gain energy using effective consumption rate
        energy_gained = consumption * self.get_effective_consumption_rate()
        self.energy += energy_gained
        self.total_consumed += consumption
        
        return consumption
    
    def metabolize(self):
        """Lose energy based on effective metabolism."""
        if not self.alive:
            return
        
        self.energy -= self.get_effective_metabolism()
        self.age += 1
        
        # Check for death
        if self.energy <= 0:
            self.alive = False
            self.energy = 0
    
    def can_reproduce(self) -> bool:
        """Check if energy exceeds effective reproduction threshold.
        
        Returns:
            True if agent can reproduce
        """
        return self.alive and self.energy >= self.get_effective_reproduction_threshold()
    
    def reproduce(self) -> Optional['Agent']:
        """Create offspring with MUTATED genome.
        
        Returns:
            New agent (offspring) with mutated genome, or None if cannot reproduce
        """
        if not self.can_reproduce():
            return None
        
        # Pay reproduction cost
        cost = self.get_effective_reproduction_cost()
        self.energy -= cost
        
        # Offspring gets MUTATED genome (this is where evolution happens!)
        offspring_genome = self.genome.copy().mutate()
        
        # Create offspring at nearby position
        offspring = Agent(
            x=self.x + np.random.uniform(-5, 5),
            y=self.y + np.random.uniform(-5, 5),
            energy=cost,
            genome=offspring_genome
        )
        
        self.offspring_count += 1
        return offspring
    
    def get_position(self) -> Tuple[float, float]:
        """Get current position."""
        return self.x, self.y
    
    def get_energy_ratio(self) -> float:
        """Get energy as ratio of 100.0."""
        return self.energy / 100.0
    
    def __repr__(self):
        """String representation of agent."""
        status = "alive" if self.alive else "dead"
        return (f"Agent(pos=({self.x:.1f},{self.y:.1f}), "
                f"energy={self.energy:.1f}, {status})")
