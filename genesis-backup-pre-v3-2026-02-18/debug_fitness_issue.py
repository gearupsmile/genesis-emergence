"""
Diagnostic Script for Zero-Fitness Issue

This script replicates the GenesisEngine initialization and runs 1-2 cycles
with detailed logging to identify why fitness scores are 0.0.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / 'genesis_engine_v2'))

from engine.genesis_engine import GenesisEngine
from engine.bootstrap_evaluator import calculate_fitness

print("=" * 60)
print("DIAGNOSTIC: Zero-Fitness Issue")
print("=" * 60)
print()

# Create engine
engine = GenesisEngine(population_size=5, mutation_rate=0.2, simulation_steps=2)

print("Initial Population:")
for i, agent in enumerate(engine.population):
    print(f"  Agent {i}: phenotype={agent.phenotype}, genome_length={agent.genome.get_length()}")
print()

# Run first cycle with detailed logging
print("=" * 60)
print("CYCLE 1 - DETAILED LOGGING")
print("=" * 60)
print()

# Step 1: Development
print("STEP 1: Development")
for agent in engine.population:
    agent.develop(engine.translator)
print("After development:")
for i, agent in enumerate(engine.population):
    phenotype_len = len(agent.phenotype) if agent.phenotype else 0
    print(f"  Agent {i}: phenotype_length={phenotype_len}, metabolic_cost={agent.genome.metabolic_cost:.3f}")
print()

# Step 2: Simulation
print("STEP 2: Simulation (age increment)")
for step in range(engine.simulation_steps):
    for agent in engine.population:
        agent.age += 1
print(f"Ages incremented by {engine.simulation_steps}")
print()

# Step 3: Evaluation
print("STEP 3: Evaluation")
fitness_scores = {}
for i, agent in enumerate(engine.population):
    # Log details before fitness calculation
    phenotype_len = len(agent.phenotype) if agent.phenotype else 0
    metabolic_cost = agent.genome.metabolic_cost
    
    fitness = calculate_fitness(agent)
    fitness_scores[agent.id] = fitness
    
    print(f"  Agent {i}:")
    print(f"    phenotype_length: {phenotype_len}")
    print(f"    metabolic_cost: {metabolic_cost:.3f}")
    print(f"    fitness: {fitness:.2f}")
    print(f"    formula: (1 + {phenotype_len}) / (1 + {metabolic_cost:.3f}) = {fitness:.2f}")

avg_fitness = sum(fitness_scores.values()) / len(fitness_scores)
print(f"\nAverage fitness: {avg_fitness:.2f}")
print()

# Step 4: Selection & Reproduction
print("STEP 4: Selection & Reproduction")
from engine.bootstrap_evaluator import tournament_selection

num_parents = max(1, len(engine.population) // 2)
parents = tournament_selection(engine.population, fitness_scores, num_parents=num_parents)
print(f"Selected {len(parents)} parents")

# Create offspring
offspring = []
for parent in parents:
    for _ in range(2):
        child = parent.reproduce(engine.mutation_rate)
        offspring.append(child)

print(f"Created {len(offspring)} offspring")
print("\nOffspring state BEFORE next cycle:")
for i, agent in enumerate(offspring):
    phenotype_len = len(agent.phenotype) if agent.phenotype else 0
    print(f"  Offspring {i}: phenotype={agent.phenotype}, phenotype_length={phenotype_len}")

# Replace population
engine.population = offspring
print()

print("=" * 60)
print("CYCLE 2 - CHECK FITNESS CALCULATION")
print("=" * 60)
print()

# Step 1: Development (SKIPPED to show the problem)
print("STEP 1: Development - SKIPPED (to show problem)")
print()

# Step 3: Evaluation WITHOUT development
print("STEP 3: Evaluation (WITHOUT development)")
fitness_scores_cycle2 = {}
for i, agent in enumerate(engine.population):
    phenotype_len = len(agent.phenotype) if agent.phenotype else 0
    metabolic_cost = agent.genome.metabolic_cost
    
    fitness = calculate_fitness(agent)
    fitness_scores_cycle2[agent.id] = fitness
    
    print(f"  Agent {i}:")
    print(f"    phenotype: {agent.phenotype}")
    print(f"    phenotype_length: {phenotype_len}")
    print(f"    metabolic_cost: {metabolic_cost:.3f}")
    print(f"    fitness: {fitness:.2f}")

avg_fitness_cycle2 = sum(fitness_scores_cycle2.values()) / len(fitness_scores_cycle2)
print(f"\nAverage fitness WITHOUT development: {avg_fitness_cycle2:.2f}")
print()

print("=" * 60)
print("DIAGNOSIS COMPLETE")
print("=" * 60)
print()
print("ROOT CAUSE IDENTIFIED:")
print("  After reproduction (Step 4), the population is replaced with")
print("  offspring that have phenotype=None (undeveloped).")
print()
print("  In the NEXT cycle, if development happens BEFORE evaluation,")
print("  fitness should be calculated correctly.")
print()
print("  However, the current run_cycle() logs show avg_fitness=0.00,")
print("  which suggests agents are being evaluated BEFORE development.")
print()
print("HYPOTHESIS:")
print("  The fitness_scores used in _log_statistics() are from BEFORE")
print("  reproduction, but the population has been REPLACED with offspring.")
print("  So the fitness_scores dict has IDs that don't match the new population!")
print()
