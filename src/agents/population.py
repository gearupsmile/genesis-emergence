"""
Population management for agent-based system.

Manages collection of agents, handles births/deaths, tracks statistics,
and provides efficient spatial queries.
"""

import numpy as np
from typing import List, Tuple, Dict, Optional
from .base_agent import Agent


class Population:
    """Manages a population of agents with spatial efficiency."""
    
    def __init__(self, max_population: int = 1000, custom_params: Optional[Dict] = None):
        """Initialize population manager.
        
        Args:
            max_population: Maximum number of agents allowed
            custom_params: Optional dict to override agent parameters
        """
        self.agents: List[Agent] = []
        self.max_population = max_population
        self.custom_params = custom_params  # Store for spawning new agents
        
        # Statistics
        self.total_births = 0
        self.total_deaths = 0
        self.cycle_count = 0
        
        # History for tracking dynamics
        self.population_history: List[int] = []
        self.energy_history: List[float] = []
    
    def add_agent(self, agent: Agent) -> bool:
        """Add an agent to the population.
        
        Args:
            agent: Agent to add
            
        Returns:
            True if added, False if population at max
        """
        if len(self.agents) >= self.max_population:
            return False
        
        self.agents.append(agent)
        self.total_births += 1
        return True
    
    def spawn_random_agents(
        self,
        count: int,
        bounds: Tuple[int, int],
        energy: Optional[float] = None
    ) -> int:
        """Spawn agents at random positions.
        
        Args:
            count: Number of agents to spawn
            bounds: (height, width) of the world
            energy: Starting energy (None for default)
            
        Returns:
            Number of agents actually spawned
        """
        height, width = bounds
        spawned = 0
        
        for _ in range(count):
            if len(self.agents) >= self.max_population:
                break
            
            x = np.random.uniform(0, width)
            y = np.random.uniform(0, height)
            
            agent = Agent(x, y, energy, custom_params=self.custom_params)
            if self.add_agent(agent):
                spawned += 1
        
        return spawned
    
    def update(self, U: np.ndarray) -> Dict[str, int]:
        """Update all agents: move, consume, metabolize, reproduce.
        
        Args:
            U: U concentration field (will be modified by consumption)
            
        Returns:
            Dictionary with update statistics
        """
        height, width = U.shape
        bounds = (height, width)
        
        births = 0
        deaths = 0
        
        # Phase 1: Movement
        for agent in self.agents:
            if agent.alive:
                agent.move(U, bounds)
        
        # Phase 2: Energy consumption
        for agent in self.agents:
            if agent.alive:
                agent.consume_energy(U)
        
        # Phase 3: Metabolism
        for agent in self.agents:
            if agent.alive:
                agent.metabolize()
                
                # Check for death
                if not agent.alive:
                    deaths += 1
        
        # Phase 4: Reproduction
        offspring = []
        for agent in self.agents:
            if agent.can_reproduce():
                child = agent.reproduce()
                if child is not None:
                    offspring.append(child)
                    births += 1
        
        # Add offspring (up to population limit)
        for child in offspring:
            if len(self.agents) >= self.max_population:
                break
            self.agents.append(child)
        
        # Phase 5: Remove dead agents
        self.agents = [a for a in self.agents if a.alive]
        
        # Update statistics
        self.total_births += births
        self.total_deaths += deaths
        self.cycle_count += 1
        
        # Record history
        self.population_history.append(len(self.agents))
        if len(self.agents) > 0:
            avg_energy = np.mean([a.energy for a in self.agents])
            self.energy_history.append(avg_energy)
        else:
            self.energy_history.append(0.0)
        
        return {
            'births': births,
            'deaths': deaths,
            'population': len(self.agents)
        }
    
    def get_statistics(self) -> Dict:
        """Get current population statistics.
        
        Returns:
            Dictionary with comprehensive statistics
        """
        if len(self.agents) == 0:
            return {
                'population': 0,
                'avg_energy': 0.0,
                'min_energy': 0.0,
                'max_energy': 0.0,
                'avg_age': 0.0,
                'total_births': self.total_births,
                'total_deaths': self.total_deaths,
                'cycle': self.cycle_count
            }
        
        energies = [a.energy for a in self.agents]
        ages = [a.age for a in self.agents]
        
        return {
            'population': len(self.agents),
            'avg_energy': float(np.mean(energies)),
            'min_energy': float(np.min(energies)),
            'max_energy': float(np.max(energies)),
            'std_energy': float(np.std(energies)),
            'avg_age': float(np.mean(ages)),
            'max_age': int(np.max(ages)),
            'total_births': self.total_births,
            'total_deaths': self.total_deaths,
            'cycle': self.cycle_count
        }
    
    def get_spatial_distribution(self, bounds: Tuple[int, int], grid_size: int = 32) -> np.ndarray:
        """Get spatial distribution of agents as a heatmap.
        
        Args:
            bounds: (height, width) of the world
            grid_size: Size of the heatmap grid
            
        Returns:
            2D array with agent counts per cell
        """
        height, width = bounds
        heatmap = np.zeros((grid_size, grid_size), dtype=np.int32)
        
        for agent in self.agents:
            # Map agent position to grid cell
            gx = int((agent.x / width) * grid_size)
            gy = int((agent.y / height) * grid_size)
            
            # Clamp to valid range
            gx = np.clip(gx, 0, grid_size - 1)
            gy = np.clip(gy, 0, grid_size - 1)
            
            heatmap[gy, gx] += 1
        
        return heatmap
    
    def get_agents_near(self, x: float, y: float, radius: float) -> List[Agent]:
        """Get agents within radius of position.
        
        Args:
            x: X position
            y: Y position
            radius: Search radius
            
        Returns:
            List of agents within radius
        """
        nearby = []
        radius_sq = radius ** 2
        
        for agent in self.agents:
            dx = agent.x - x
            dy = agent.y - y
            dist_sq = dx**2 + dy**2
            
            if dist_sq <= radius_sq:
                nearby.append(agent)
        
        return nearby
    
    def clear(self) -> None:
        """Remove all agents."""
        self.agents.clear()
        self.total_births = 0
        self.total_deaths = 0
        self.cycle_count = 0
        self.population_history.clear()
        self.energy_history.clear()
    
    def __len__(self) -> int:
        """Get population count."""
        return len(self.agents)
    
    def __iter__(self):
        """Iterate over agents."""
        return iter(self.agents)
    
    def __repr__(self) -> str:
        """String representation."""
        return f"Population(size={len(self.agents)}, births={self.total_births}, deaths={self.total_deaths})"
