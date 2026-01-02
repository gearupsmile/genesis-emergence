"""
GenesisEngine - Integrated Simulation Loop

This module implements the GenesisEngine class that integrates all components
into a complete evolutionary simulation loop.

Phase 3.2: Bootstrap Evolution - Integrated Simulation Loop
"""

import random
from typing import List, Dict, Optional
from .codon_translator import CodonTranslator
from .ais import ArtificialImmuneSystem
from .kernel_world import KernelWorld
from .structurally_evolvable_agent import StructurallyEvolvableAgent
from .evolvable_genome import EvolvableGenome
from .linkage_structure import LinkageStructure
from .bootstrap_evaluator import calculate_fitness, tournament_selection


class GenesisEngine:
    """
    Main simulation driver for the Genesis Engine v2.
    
    Integrates all components into a complete evolutionary loop:
    1. Development (translate genotypes to phenotypes)
    2. Simulation (placeholder: increment ages)
    3. Evaluation (calculate fitness)
    4. Selection & Reproduction (evolve population)
    5. AIS Culling (lifecycle management)
    
    This is the complete bootstrap evolution system.
    """
    
    def __init__(self, population_size: int = 20, mutation_rate: float = 0.2,
                 simulation_steps: int = 10):
        """
        Initialize the Genesis Engine.
        
        Args:
            population_size: Number of agents in population
            mutation_rate: Probability of mutations during reproduction
            simulation_steps: Number of simulation steps per cycle (for age increment)
        """
        # Core components
        self.translator = CodonTranslator()
        self.ais = ArtificialImmuneSystem()
        
        # Configuration
        self.population_size = population_size
        self.mutation_rate = mutation_rate
        self.simulation_steps = simulation_steps
        
        # State
        self.population: List[StructurallyEvolvableAgent] = []
        self.world: Optional[KernelWorld] = None
        self.generation = 0
        self.statistics: List[Dict] = []
        
        # Initialize population and world
        self._initialize_population()
        self._initialize_world()
    
    def _initialize_population(self):
        """Create initial population of random agents."""
        self.population = []
        
        for i in range(self.population_size):
            # Create random genome (3-5 genes)
            num_genes = random.randint(3, 5)
            codons = [random.choice(['AAA', 'CAA', 'GAA', 'TAA', 'ACA']) 
                     for _ in range(num_genes)]
            genome = EvolvableGenome(codons)
            
            # Create agent with uniform linkage
            agent = StructurallyEvolvableAgent(genome)
            self.population.append(agent)
    
    def _initialize_world(self):
        """Create initial world with random genotype."""
        # Create random world genotype (6-9 codons)
        num_codons = random.randint(6, 9)
        world_genotype = ''.join([random.choice(['AAA', 'CAA', 'GAA', 'TAA', 'ACA']) 
                                  for _ in range(num_codons)])
        self.world = KernelWorld(world_genotype)
    
    def run_cycle(self):
        """
        Execute one complete generation cycle.
        
        5-Step Loop:
        1. Development: Translate genotypes to phenotypes
        2. Simulation: Run interactions (placeholder: increment ages)
        3. Evaluation: Calculate fitness scores
        4. Selection & Reproduction: Evolve population
        5. AIS Culling: Apply lifecycle management
        """
        # Step 1: Development
        for agent in self.population:
            agent.develop(self.translator)
        self.world.develop_physics(self.translator)
        
        # Step 2: Simulation (placeholder)
        # Currently just increments age for AIS forgetting
        # Future: Real physics, agent-world interactions, energy transfer
        for step in range(self.simulation_steps):
            for agent in self.population:
                agent.age += 1
            self.world.age += 1
        
        # Step 3: Evaluation
        fitness_scores = {}
        world_state = self.world.to_dict()  # For future use
        
        for agent in self.population:
            fitness_scores[agent.id] = calculate_fitness(agent, world_state)
        
        # Track statistics BEFORE reproduction (while IDs still match)
        self._log_statistics(fitness_scores, [])  # No purging yet
        
        # Step 4: Selection & Reproduction
        num_parents = max(1, len(self.population) // 2)
        parents = tournament_selection(
            self.population, 
            fitness_scores, 
            num_parents=num_parents,
            tournament_size=3
        )
        
        # Reproduce to maintain population size
        offspring = []
        offspring_per_parent = self.population_size // len(parents)
        remainder = self.population_size % len(parents)
        
        for i, parent in enumerate(parents):
            num_offspring = offspring_per_parent + (1 if i < remainder else 0)
            for _ in range(num_offspring):
                child = parent.reproduce(self.mutation_rate)
                offspring.append(child)
        
        self.population = offspring
        
        # Step 5: AIS Culling
        # Convert all entities to dicts
        all_entities = [agent.to_dict() for agent in self.population]
        all_entities.append(self.world.to_dict())
        
        # Apply AIS cycle
        updated_entities, purged_ids = self.ais.apply_cycle(all_entities)
        
        # Update agents from AIS results
        updated_dict = {e['id']: e for e in updated_entities}
        
        for agent in self.population:
            if agent.id in updated_dict:
                agent.update_from_dict(updated_dict[agent.id])
        
        if self.world.id in updated_dict:
            self.world.update_from_dict(updated_dict[self.world.id])
        
        # Remove purged agents
        self.population = [a for a in self.population if a.id not in purged_ids]
        
        # Check if world was purged (shouldn't happen with default AIS params)
        if self.world.id in purged_ids:
            # Recreate world
            self._initialize_world()
        
        # Update statistics with purge count
        if self.statistics:
            self.statistics[-1]['num_purged'] = len(purged_ids)
            self.statistics[-1]['population_size'] = len(self.population)  # Update after purging
        
        # Increment generation
        self.generation += 1
    
    def _log_statistics(self, fitness_scores: Dict[str, float], purged_ids: List[str]):
        """Log statistics for this generation."""
        if len(self.population) == 0:
            # Population extinct - log zeros
            stats = {
                'generation': self.generation,
                'population_size': 0,
                'avg_fitness': 0.0,
                'max_fitness': 0.0,
                'avg_genome_length': 0.0,
                'avg_linkage_groups': 0.0,
                'num_purged': len(purged_ids)
            }
        else:
            # Calculate statistics
            valid_fitness = [fitness_scores.get(a.id, 0.0) for a in self.population]
            
            stats = {
                'generation': self.generation,
                'population_size': len(self.population),
                'avg_fitness': sum(valid_fitness) / len(valid_fitness) if valid_fitness else 0.0,
                'max_fitness': max(valid_fitness) if valid_fitness else 0.0,
                'avg_genome_length': sum(a.genome.get_length() for a in self.population) / len(self.population),
                'avg_linkage_groups': sum(a.linkage_structure.get_num_groups() for a in self.population) / len(self.population),
                'num_purged': len(purged_ids)
            }
        
        self.statistics.append(stats)
    
    def get_statistics_summary(self) -> str:
        """Get formatted summary of recent statistics."""
        if not self.statistics:
            return "No statistics available"
        
        latest = self.statistics[-1]
        summary = (
            f"Generation {latest['generation']}: "
            f"pop={latest['population_size']}, "
            f"avg_fitness={latest['avg_fitness']:.2f}, "
            f"max_fitness={latest['max_fitness']:.2f}, "
            f"avg_genome={latest['avg_genome_length']:.1f}, "
            f"avg_linkage={latest['avg_linkage_groups']:.1f}, "
            f"purged={latest['num_purged']}"
        )
        return summary
    
    def __repr__(self) -> str:
        """String representation for debugging."""
        return (f"GenesisEngine(generation={self.generation}, "
                f"population={len(self.population)}, "
                f"mutation_rate={self.mutation_rate})")


if __name__ == '__main__':
    # Demonstration
    print("=" * 60)
    print("GenesisEngine Demonstration")
    print("=" * 60)
    print()
    
    # Create engine
    engine = GenesisEngine(population_size=10, mutation_rate=0.2)
    print(f"Initialized: {engine}")
    print(f"  Population: {len(engine.population)} agents")
    print(f"  World: {engine.world}")
    print()
    
    # Run 5 generations
    print("Running 5 generations...")
    for gen in range(5):
        engine.run_cycle()
        print(f"  {engine.get_statistics_summary()}")
    
    print()
    print("=" * 60)
    print("Genesis Engine v2 - Complete Bootstrap Evolution System")
    print("  Phase 1.1: CodonTranslator ✓")
    print("  Phase 1.2: AIS ✓")
    print("  Phase 1.3: KernelAgent/World ✓")
    print("  Phase 2.1: EvolvableGenome ✓")
    print("  Phase 2.2: LinkageStructure ✓")
    print("  Phase 2.3: StructurallyEvolvableAgent ✓")
    print("  Phase 3.1: BootstrapEvaluator ✓")
    print("  Phase 3.2: GenesisEngine ✓")
    print("=" * 60)
