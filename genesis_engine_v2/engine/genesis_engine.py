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
from .pareto_evaluator import ParetoCoevolutionEvaluator


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
                 simulation_steps: int = 10,
                 transition_start_generation: int = 0,
                 transition_total_generations: int = 10000):
        """
        Initialize the Genesis Engine.
        
        Args:
            population_size: Number of agents in population
            mutation_rate: Probability of mutations during reproduction
            simulation_steps: Number of simulation steps per cycle (for age increment)
            transition_start_generation: Generation to start transition (default: 0)
            transition_total_generations: Generations for complete transition (default: 10000)
        """
        # Core components
        self.translator = CodonTranslator()
        self.ais = ArtificialImmuneSystem()
        
        # Dual evaluators (Phase 4.2)
        self.external_evaluator = None  # Uses calculate_fitness function
        self.internal_evaluator = ParetoCoevolutionEvaluator()
        
        # Configuration
        self.population_size = population_size
        self.mutation_rate = mutation_rate
        self.simulation_steps = simulation_steps
        
        # Transition configuration (Phase 4.2)
        self.transition_start_generation = transition_start_generation
        self.transition_total_generations = transition_total_generations
        self.transition_weight = 1.0  # Starts at 1.0 (100% external)
        
        # State
        self.population: List[StructurallyEvolvableAgent] = []
        self.world: Optional[KernelWorld] = None
        self.generation = 0
        self.statistics: List[Dict] = []
        
        # Physics enforcement tracking (Phase 2)
        self.offspring_terminations_log = []  # Track violating offspring terminated before entering population
        
        # Environmental systems (Week 3)
        from .environment.resource_niches import ResourceNicheSystem
        from .environment.spatial_regions import SpatialEnvironment
        from .environment.temporal_cycles import TemporalEnvironment
        from .pressure.functional_stagnation_detector import FunctionalStagnationDetector
        from .behavior.behavioral_tracker import BehavioralTracker
        self.resource_system = ResourceNicheSystem()
        self.spatial_env = SpatialEnvironment(migration_rate=0.1)
        self.temporal_env = TemporalEnvironment(cycle_length=500)
        self.fsd = FunctionalStagnationDetector(window_size=100, innovation_threshold=2)
        self.behavioral_tracker = BehavioralTracker(window_size=100)  # NEW: Action-based tracking
        
        # Base energy constant for FSD pressure application
        self.base_energy_constant = 0.5
        
        # Initialize population and world
        self._initialize_population()
        self._initialize_world()
        
        # Initialize spatial assignments after population creation
        self.spatial_env.initialize_agents(self.population)
    
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
    
    def _normalize_scores(self, score_dict: Dict[str, float]) -> Dict[str, float]:
        """
        Normalize scores to [0, 1] range for fair comparison.
        
        CRITICAL: Without normalization, external scores (~76) would swamp
        internal scores (~0-3), making the transition meaningless.
        
        Args:
            score_dict: Dict mapping agent_id to raw score
            
        Returns:
            Dict mapping agent_id to normalized score in [0, 1]
            
        Edge case: If all scores are identical (max == min), assign 0.5 to all.
        """
        if not score_dict:
            return {}
        
        scores = list(score_dict.values())
        min_score = min(scores)
        max_score = max(scores)
        
        # Handle edge case: all scores identical
        if max_score == min_score:
            return {agent_id: 0.5 for agent_id in score_dict}
        
        # Normalize to [0, 1]
        normalized = {}
        for agent_id, raw_score in score_dict.items():
            normalized[agent_id] = (raw_score - min_score) / (max_score - min_score)
        
        return normalized
    
    def run_cycle(self):
        """
        Execute one complete generation cycle.
        
        5-Step Loop:
        1. Development: Translate genotypes to phenotypes
        2. Simulation: Run interactions (placeholder: increment ages)
        2.5. Physics Enforcement: Apply immutable physical laws (NEW - Phase 2)
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
        
        # Step 2.2: Temporal Phase Update (Week 3)
        phase_changed = self.temporal_env.update_phase(self.generation)
        if phase_changed:
            current_phase = self.temporal_env.get_current_phase()
            print(f"  {current_phase.get_log_prefix()} Entering {current_phase.name} phase")
        
        # Apply temporal modifiers to resources
        self.temporal_env.apply_resource_modifiers(self.resource_system)
        
        # Step 2.4: Resource Interactions (Week 3)
        # Agents consume resources based on specialization AND regional modifiers
        for agent in self.population:
            # Get agent's region
            region = self.spatial_env.get_region_for_agent(agent.id)
            
            # Determine best resource for agent
            best_resource, _ = self.resource_system.get_best_resource_for_agent(agent)
            
            # Apply regional resource multipliers
            # (This modifies resource availability for this agent)
            resource_energy = self.resource_system.agent_consumes_resource(agent, best_resource)
            
            # Apply regional fitness modifier
            regional_modifier = region.calculate_fitness_modifier(agent)
            resource_energy *= regional_modifier
            
            # Track resource energy for fitness calculation
            if not hasattr(agent, 'resource_energy'):
                agent.resource_energy = 0.0
            agent.resource_energy += resource_energy
            
            # BEHAVIORAL TRACKING (Emergency Fix)
            # Record resource acquisition action
            if best_resource:
                self.behavioral_tracker.action_recorder.record_resource_acquisition(
                    agent.id, best_resource
                )
            
            # Record energy intake
            self.behavioral_tracker.action_recorder.record_energy_intake(
                agent.id, resource_energy
            )
            
            # Record constraint pressure
            self.behavioral_tracker.action_recorder.record_constraint_check(
                agent.id, agent.genome.metabolic_cost, region.energy_constant
            )
        
        # Regenerate resources for next generation
        self.resource_system.regenerate_resources()
        
        # Step 2.45: Migration (every 100 generations)
        self.spatial_env.allow_migration(self.population, self.generation)
        
        # Step 2.6: Innovation Tracking (Week 3 - FSD)
        innovation_count = self.fsd.track_innovation(
            self.generation, 
            self.population, 
            self.resource_system, 
            self.spatial_env
        )
        
        # Step 2.5: Physics Gatekeeper (NEW - Phase 2: Physical Invariant Architecture)
        # Enforce immutable physical laws BEFORE evaluation and reproduction
        # This ensures agents cannot evolve around constraints
        from .physics.physics_gatekeeper import PhysicalInvariantGatekeeper
        
        if not hasattr(self, 'physics_gatekeeper'):
            self.physics_gatekeeper = PhysicalInvariantGatekeeper(energy_constant=0.5)
        
        # Apply physical constraints - agents exceeding metabolic limit are terminated
        self.population, terminated_ids = self.physics_gatekeeper.enforce_population_constraints(self.population)
        
        # Log physics violations if any occurred
        if len(terminated_ids) > 0:
            if not hasattr(self, 'physics_violations'):
                self.physics_violations = []
            
            self.physics_violations.append({
                'generation': self.generation,
                'terminated_count': len(terminated_ids),
                'terminated_ids': terminated_ids
            })

        
        # Step 3: Dual Evaluation (Phase 4.2)
        # Calculate both external fitness and internal Pareto distinction
        external_scores = {}
        world_state = self.world.to_dict()  # For future use
        
        # External fitness (BootstrapEvaluator)
        for agent in self.population:
            external_scores[agent.id] = calculate_fitness(agent, world_state)
        
        # Internal distinction (ParetoCoevolutionEvaluator)
        internal_scores = self.internal_evaluator.evaluate_population(self.population)
        
        # CRITICAL: Normalize both score sets to [0, 1] for fair comparison
        normalized_external = self._normalize_scores(external_scores)
        normalized_internal = self._normalize_scores(internal_scores)
        
        # Blend scores based on transition weight
        final_scores = {}
        for agent in self.population:
            ext_norm = normalized_external[agent.id]
            int_norm = normalized_internal[agent.id]
            final_scores[agent.id] = (
                self.transition_weight * ext_norm +
                (1 - self.transition_weight) * int_norm
            )
        
        # Update transition weight (linear decay)
        if self.generation >= self.transition_start_generation:
            if self.transition_total_generations > 0:
                decay = 1.0 / self.transition_total_generations
                self.transition_weight = max(0.0, self.transition_weight - decay)
        
        # Track statistics BEFORE reproduction (while IDs still match)
        self._log_statistics(
            external_scores, internal_scores,
            normalized_external, normalized_internal,
            final_scores, []
        )  # No purging yet
        
        # Step 4: Selection & Reproduction
        num_parents = max(1, len(self.population) // 2)
        parents = tournament_selection(
            self.population, 
            final_scores,  # Use blended scores for selection
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
        
        # TIER 2 GATEKEEPER (NEW - Phase 2 Fix): Check offspring BEFORE they enter population
        # This ensures NO violating agent ever exists in self.population, not even for 1 generation
        viable_offspring, terminated_offspring_ids = self.physics_gatekeeper.enforce_population_constraints(offspring)
        
        # Log offspring terminations (distinct from parent terminations)
        if len(terminated_offspring_ids) > 0:
            self.offspring_terminations_log.append({
                'generation': self.generation,
                'terminated_count': len(terminated_offspring_ids),
                'terminated_ids': terminated_offspring_ids,
                'reason': 'offspring_exceeded_energy_constant'
            })
        
        # Replace population with ONLY viable offspring
        self.population = viable_offspring
        
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
    
    def _log_statistics(self, external_scores: Dict[str, float],
                        internal_scores: Dict[str, float],
                        normalized_external: Dict[str, float],
                        normalized_internal: Dict[str, float],
                        final_scores: Dict[str, float],
                        purged_ids: List[str]):
        """Log statistics for this generation with dual scores."""
        if len(self.population) == 0:
            # Population extinct - log zeros
            stats = {
                'generation': self.generation,
                'population_size': 0,
                'transition_weight': self.transition_weight,
                'avg_external_score': 0.0,
                'max_external_score': 0.0,
                'avg_internal_score': 0.0,
                'max_internal_score': 0.0,
                'avg_final_score': 0.0,
                'max_final_score': 0.0,
                'avg_genome_length': 0.0,
                'avg_linkage_groups': 0.0,
                'num_purged': len(purged_ids)
            }
        else:
            # Calculate statistics
            valid_external = [external_scores.get(a.id, 0.0) for a in self.population]
            valid_internal = [internal_scores.get(a.id, 0.0) for a in self.population]
            valid_final = [final_scores.get(a.id, 0.0) for a in self.population]
            
            stats = {
                'generation': self.generation,
                'population_size': len(self.population),
                'transition_weight': self.transition_weight,
                # Raw scores
                'avg_external_score': sum(valid_external) / len(valid_external) if valid_external else 0.0,
                'max_external_score': max(valid_external) if valid_external else 0.0,
                'avg_internal_score': sum(valid_internal) / len(valid_internal) if valid_internal else 0.0,
                'max_internal_score': max(valid_internal) if valid_internal else 0.0,
                # Final blended score
                'avg_final_score': sum(valid_final) / len(valid_final) if valid_final else 0.0,
                'max_final_score': max(valid_final) if valid_final else 0.0,
                # Genome stats
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
