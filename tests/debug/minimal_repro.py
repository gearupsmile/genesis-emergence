"""
Minimal Reproduction Case - Physics Gatekeeper Enforcement Failure

Creates a single violating agent and traces its path through one generation cycle
to find where the termination decision is lost.

Debug Mission: Find the broken link in the enforcement chain.
"""

import sys
from pathlib import Path

# Add genesis_engine_v2 to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'genesis_engine_v2'))

from engine.genesis_engine import GenesisEngine
from engine.evolvable_genome import EvolvableGenome
from engine.structurally_evolvable_agent import StructurallyEvolvableAgent


def create_violating_agent():
    """Create an agent guaranteed to violate the energy constant."""
    # Create genome with 30 genes (cost ~0.82, well above 0.5 threshold)
    genome = EvolvableGenome(['AAA'] * 30)
    agent = StructurallyEvolvableAgent(genome)
    
    print(f"Created violating agent:")
    print(f"  ID: {agent.id}")
    print(f"  Genome length: {genome.get_length()} genes")
    print(f"  Metabolic cost: {genome.metabolic_cost:.4f}")
    print(f"  Energy constant: 0.5")
    print(f"  SHOULD BE TERMINATED: {genome.metabolic_cost > 0.5}")
    print()
    
    return agent


def trace_single_cycle():
    """Trace a single violating agent through one generation cycle."""
    print("=" * 70)
    print("MINIMAL REPRODUCTION CASE: Physics Gatekeeper Enforcement")
    print("=" * 70)
    print()
    
    # Create engine with single violating agent
    print("Step 1: Initialize engine")
    engine = GenesisEngine(
        population_size=1,  # Start with 1 agent
        mutation_rate=0.0,  # No mutations to keep it simple
        simulation_steps=1
    )
    
    # Replace the random initial population with our violating agent
    violating_agent = create_violating_agent()
    engine.population = [violating_agent]
    
    print(f"Initial population: {len(engine.population)} agent(s)")
    print(f"  Agent ID: {engine.population[0].id}")
    print(f"  Agent cost: {engine.population[0].genome.metabolic_cost:.4f}")
    print()
    
    # Manually step through run_cycle() with instrumentation
    print("=" * 70)
    print("TRACING THROUGH run_cycle()")
    print("=" * 70)
    print()
    
    # Step 1: Development
    print("Step 1: Development")
    for agent in engine.population:
        agent.develop(engine.translator)
    engine.world.develop_physics(engine.translator)
    print(f"  Population after development: {len(engine.population)} agent(s)")
    print()
    
    # Step 2: Simulation (age increment)
    print("Step 2: Simulation")
    for step in range(engine.simulation_steps):
        for agent in engine.population:
            agent.age += 1
        engine.world.age += 1
    print(f"  Population after simulation: {len(engine.population)} agent(s)")
    print()
    
    # Step 2.5: Physics Gatekeeper (THE CRITICAL STEP)
    print("Step 2.5: Physics Gatekeeper (CRITICAL)")
    print("-" * 70)
    
    from engine.physics.physics_gatekeeper import PhysicalInvariantGatekeeper
    
    if not hasattr(engine, 'physics_gatekeeper'):
        engine.physics_gatekeeper = PhysicalInvariantGatekeeper(energy_constant=0.5)
    
    print(f"  BEFORE gatekeeper:")
    print(f"    Population size: {len(engine.population)}")
    for agent in engine.population:
        print(f"    Agent {agent.id[:8]}: cost={agent.genome.metabolic_cost:.4f}, viable={agent.genome.metabolic_cost <= 0.5}")
    print()
    
    # CRITICAL LINE: Apply gatekeeper
    survivors, terminated_ids = engine.physics_gatekeeper.enforce_population_constraints(engine.population)
    
    print(f"  GATEKEEPER RETURNED:")
    print(f"    Survivors: {len(survivors)}")
    print(f"    Terminated IDs: {terminated_ids}")
    print()
    
    # CRITICAL CHECK: Is the population actually updated?
    print(f"  BEFORE assignment:")
    print(f"    engine.population = {[a.id[:8] for a in engine.population]}")
    
    engine.population = survivors
    
    print(f"  AFTER assignment:")
    print(f"    engine.population = {[a.id[:8] for a in engine.population]}")
    print()
    
    if len(terminated_ids) > 0:
        if not hasattr(engine, 'physics_violations'):
            engine.physics_violations = []
        
        engine.physics_violations.append({
            'generation': engine.generation,
            'terminated_count': len(terminated_ids),
            'terminated_ids': terminated_ids
        })
    
    print(f"  AFTER gatekeeper:")
    print(f"    Population size: {len(engine.population)}")
    if engine.population:
        for agent in engine.population:
            print(f"    Agent {agent.id[:8]}: cost={agent.genome.metabolic_cost:.4f}")
    else:
        print("    [POPULATION EMPTY - AGENT TERMINATED]")
    print()
    
    # Check if we should stop here (population extinct)
    if len(engine.population) == 0:
        print("=" * 70)
        print("RESULT: Agent was CORRECTLY TERMINATED by gatekeeper")
        print("=" * 70)
        return True
    
    # Continue with rest of cycle to see if agent reappears
    print("Step 3: Evaluation")
    external_scores = {}
    world_state = engine.world.to_dict()
    
    from engine.bootstrap_evaluator import calculate_fitness
    for agent in engine.population:
        external_scores[agent.id] = calculate_fitness(agent, world_state)
    
    internal_scores = engine.internal_evaluator.evaluate_population(engine.population)
    
    print(f"  Population after evaluation: {len(engine.population)} agent(s)")
    print()
    
    # Step 4: Selection & Reproduction
    print("Step 4: Selection & Reproduction")
    print(f"  Population BEFORE reproduction: {len(engine.population)} agent(s)")
    
    if len(engine.population) > 0:
        # Normalize and blend scores
        normalized_external = engine._normalize_scores(external_scores)
        normalized_internal = engine._normalize_scores(internal_scores)
        
        final_scores = {}
        for agent in engine.population:
            ext_norm = normalized_external[agent.id]
            int_norm = normalized_internal[agent.id]
            final_scores[agent.id] = (
                engine.transition_weight * ext_norm +
                (1 - engine.transition_weight) * int_norm
            )
        
        # Selection
        from engine.bootstrap_evaluator import tournament_selection
        num_parents = max(1, len(engine.population) // 2)
        parents = tournament_selection(
            engine.population,
            final_scores,
            num_parents=num_parents,
            tournament_size=3
        )
        
        print(f"  Selected {len(parents)} parent(s)")
        
        # Reproduction
        offspring = []
        offspring_per_parent = engine.population_size // len(parents)
        remainder = engine.population_size % len(parents)
        
        for i, parent in enumerate(parents):
            num_offspring = offspring_per_parent + (1 if i < remainder else 0)
            for _ in range(num_offspring):
                child = parent.reproduce(engine.mutation_rate)
                offspring.append(child)
                print(f"    Created offspring {child.id[:8]}: cost={child.genome.metabolic_cost:.4f}")
        
        print(f"  Created {len(offspring)} offspring")
        
        # CRITICAL: Replace population with offspring
        engine.population = offspring
        
        print(f"  Population AFTER reproduction: {len(engine.population)} agent(s)")
        for agent in engine.population:
            print(f"    Agent {agent.id[:8]}: cost={agent.genome.metabolic_cost:.4f}, viable={agent.genome.metabolic_cost <= 0.5}")
    
    print()
    
    print("=" * 70)
    print("RESULT: Checking if violating agent survived")
    print("=" * 70)
    
    # Check if any agent violates the constraint
    violators = [a for a in engine.population if a.genome.metabolic_cost > 0.5]
    
    if violators:
        print(f"[BUG FOUND] {len(violators)} violating agent(s) in population!")
        for agent in violators:
            print(f"  Agent {agent.id[:8]}: cost={agent.genome.metabolic_cost:.4f}")
        print()
        print("ANALYSIS: The gatekeeper terminated the parent, but reproduction")
        print("created offspring BEFORE the next gatekeeper check!")
        return False
    else:
        print("[SUCCESS] No violating agents in population")
        return True


if __name__ == '__main__':
    success = trace_single_cycle()
    sys.exit(0 if success else 1)
