"""
Genesis Engine Minimal - Clean Co-Evolution Implementation

Integrates ONLY validated Tracks 1-3:
- Track 1: Physics Gatekeeper (two-tier enforcement)
- Track 2: Codon System (traits + mutation + complexification)
- Track 3: CARP 2.0 (species + interactions)

NO legacy code. Under 300 lines.
"""

import random
import numpy as np
from typing import List, Dict


class GenesisEngineMinimal:
    """
    Minimal co-evolution engine for expert-mandated 1,000-gen test.
    
    10-step run_cycle():
    1. Update traits
    2. CARP interactions
    3. Calculate fitness
    4. Physics Tier 1 (parents)
    5. Selection & reproduction
    6. Physics Tier 2 (offspring)
    7. Complexification
    8. Population capping
    9. Logging
    10. Increment generation
    """
    
    def __init__(self, population_size: int = 100, forager_ratio: float = 0.7, 
                 mutation_rate: float = 0.3):
        """
        Initialize minimal engine.
        
        Args:
            population_size: Target population size
            forager_ratio: Fraction of population that are foragers (rest are predators)
            mutation_rate: Probability of mutation during reproduction
        """
        # Configuration
        self.population_size = population_size
        self.forager_ratio = forager_ratio
        self.mutation_rate = mutation_rate
        self.generation = 0
        
        # Track 1: Physics Gatekeeper
        from .physics.physics_gatekeeper import PhysicalInvariantGatekeeper
        self.physics_gatekeeper = PhysicalInvariantGatekeeper(energy_constant=0.5)
        
        # Track 3: CARP Components
        from .carp.species_assigner import SpeciesAssigner
        from .carp.interactions import InteractionHandler
        
        self.species_assigner = SpeciesAssigner(forager_ratio=forager_ratio)
        self.interaction_handler = InteractionHandler(
            capture_distance=0.1,
            base_capture_prob=0.3,
            base_energy_transfer=0.4
        )
        
        # Initialize population
        self.population = self._create_initial_population()
        
        # Assign species
        self.species_assigner.assign_species_to_population(self.population)
    
    def _create_initial_population(self) -> List:
        """Create random initial population."""
        from .evolvable_genome import EvolvableGenome
        from .structurally_evolvable_agent import StructurallyEvolvableAgent
        
        population = []
        for _ in range(self.population_size):
            # Random genome (3-5 codons)
            num_codons = random.randint(3, 5)
            codons = [random.choice(['AAA', 'CAA', 'GAA', 'TAA', 'ACA']) 
                     for _ in range(num_codons)]
            genome = EvolvableGenome(codons)
            agent = StructurallyEvolvableAgent(genome)
            agent.energy = 1.0  # Initial energy
            population.append(agent)
        
        return population
    
    def run_cycle(self):
        """Execute one generation cycle (10 steps)."""
        
        # STEP 1: Update Behavioral Traits (Track 2)
        from .codon_translator import translate_genome
        for agent in self.population:
            agent.behavioral_traits = translate_genome(agent.genome)
        
        # STEP 2: CARP Interactions (Track 3)
        from .carp.species import Species
        for agent in self.population:
            if hasattr(agent, 'species'):
                if agent.species == Species.PREDATOR:
                    result = self.interaction_handler.handle_predator_behavior(
                        agent, self.population
                    )
                    if result:
                        forager_id, energy_gained = result
                        agent.energy += energy_gained
                elif agent.species == Species.FORAGER:
                    self.interaction_handler.handle_forager_behavior(
                        agent, self.population
                    )
        
        # STEP 3: Calculate Fitness (Simple)
        for agent in self.population:
            # Fitness = energy + survival bonus
            agent.fitness = agent.energy + 10.0
        
        # STEP 4: Physics Tier 1 - Parent Viability Check (Track 1)
        viable_parents = []
        for agent in self.population:
            if self.physics_gatekeeper.check_viability_with_tracking(agent, 'parent'):
                viable_parents.append(agent)
        
        self.population = viable_parents
        
        if len(self.population) == 0:
            print(f"[EXTINCTION] Gen {self.generation}: All parents rejected!")
            return
        
        # STEP 5: Selection & Reproduction
        num_parents = max(2, self.population_size // 2)
        parents = self._tournament_selection(num_parents=num_parents)
        
        offspring = []
        offspring_per_parent = self.population_size // len(parents)
        remainder = self.population_size % len(parents)
        
        for i, parent in enumerate(parents):
            num_offspring = offspring_per_parent + (1 if i < remainder else 0)
            for _ in range(num_offspring):
                child = parent.reproduce(self.mutation_rate)
                child.energy = 1.0  # Reset energy
                offspring.append(child)
        
        # STEP 6: Physics Tier 2 - Offspring Viability Check (Track 1)
        viable_offspring = []
        for child in offspring:
            if self.physics_gatekeeper.check_viability_with_tracking(child, 'offspring'):
                viable_offspring.append(child)
        
        self.population = viable_offspring
        
        if len(self.population) == 0:
            print(f"[EXTINCTION] Gen {self.generation}: All offspring rejected!")
            return
        
        # STEP 7: Basic Complexification (DISABLED for Phase 1)
        # REASON: Adds codons AFTER Tier 2 gatekeeper check
        # This can create violations when agents exceed 0.5 metabolic cost
        # TODO: Move complexification to BEFORE reproduction in future
        pass
        
        # STEP 8: Population Capping with Gatekeeper Enforcement
        if len(self.population) > self.population_size:
            # Keep top N by fitness
            self.population.sort(key=lambda a: a.fitness, reverse=True)
            self.population = self.population[:self.population_size]
        
        # Maintain population size if too small
        # CRITICAL FIX: Check viability before adding (prevents gatekeeper bypass)
        max_attempts = self.population_size * 10  # Safety limit
        attempts = 0
        
        while len(self.population) < self.population_size and attempts < max_attempts:
            parent = random.choice(self.population)
            child = parent.reproduce(self.mutation_rate)
            child.energy = 1.0
            
            # CRITICAL: Check viability before adding to population
            if self.physics_gatekeeper.check_viability_with_tracking(child, 'offspring'):
                self.population.append(child)
            
            attempts += 1
        
        # Warn if couldn't reach target (shouldn't happen with valid parents)
        if len(self.population) < self.population_size:
            print(f"[WARNING] Gen {self.generation}: Population {len(self.population)}/{self.population_size}")
        
        # STEP 8.5: Gentle Species Rebalancer (ONLY for extreme drift)
        # CRITICAL: Only intervene if ratio drifts to non-viable levels
        # This maintains frequency-dependent selection while preventing extinction
        from .carp.species import Species
        
        forager_count = sum(1 for a in self.population 
                           if hasattr(a, 'species') and a.species == Species.FORAGER)
        predator_count = len(self.population) - forager_count
        
        # ONLY rebalance if viability threatened
        if forager_count < 20 or predator_count < 10:
            # Population at risk - gentle rebalance
            # This is a "law-like" event (population crash), not teleological selection
            print(f"[REBALANCE] Gen {self.generation}: F={forager_count}, P={predator_count}")
            self.species_assigner.assign_species_to_population(self.population)
        
        # STEP 9: Finalize Generation Logging (Track 1)
        self.physics_gatekeeper.finalize_generation(self.generation, self.population)
        
        # STEP 10: Increment Generation
        self.generation += 1
    
    def _tournament_selection(self, num_parents: int, tournament_size: int = 3) -> List:
        """Simple tournament selection."""
        parents = []
        
        for _ in range(num_parents):
            tournament = random.sample(self.population, 
                                      min(tournament_size, len(self.population)))
            winner = max(tournament, key=lambda a: a.fitness)
            parents.append(winner)
        
        return parents
    
    def get_statistics(self) -> Dict:
        """Get current generation statistics."""
        from .carp.species import Species
        
        foragers = [a for a in self.population 
                   if hasattr(a, 'species') and a.species == Species.FORAGER]
        predators = [a for a in self.population 
                    if hasattr(a, 'species') and a.species == Species.PREDATOR]
        
        # Behavioral variance (PRIMARY METRIC)
        traits_matrix = [list(a.behavioral_traits.values()) 
                        for a in self.population if hasattr(a, 'behavioral_traits')]
        
        behavioral_variance = np.var(traits_matrix) if len(traits_matrix) > 1 else 0.0
        
        # Average traits by species
        forager_aggression = np.mean([a.behavioral_traits.get('aggression', 0.5) 
                                     for a in foragers]) if foragers else 0.5
        predator_aggression = np.mean([a.behavioral_traits.get('aggression', 0.5) 
                                      for a in predators]) if predators else 0.5
        
        forager_exploration = np.mean([a.behavioral_traits.get('exploration', 0.5) 
                                      for a in foragers]) if foragers else 0.5
        predator_exploration = np.mean([a.behavioral_traits.get('exploration', 0.5) 
                                       for a in predators]) if predators else 0.5
        
        # Average genome length
        avg_genome_length = np.mean([len(a.genome.sequence) for a in self.population])
        
        return {
            'generation': self.generation,
            'population_size': len(self.population),
            'forager_count': len(foragers),
            'predator_count': len(predators),
            'behavioral_variance': behavioral_variance,
            'forager_aggression': forager_aggression,
            'predator_aggression': predator_aggression,
            'forager_exploration': forager_exploration,
            'predator_exploration': predator_exploration,
            'avg_genome_length': avg_genome_length,
            'physics_stats': self.physics_gatekeeper.logger.get_summary_statistics(),
            'carp_stats': self.interaction_handler.get_statistics()
        }
