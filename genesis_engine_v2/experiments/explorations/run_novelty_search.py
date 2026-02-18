"""
Novelty Search Experiment Runner

Runs the Genesis Engine with Novelty Search selection.
Logs archive size, max scores, and population statistics.
"""

import sys
import os
import time
from pathlib import Path

# Fix paths
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "genesis_engine_v2"))

from genesis_engine_v2.engine.genesis_engine import GenesisEngine
from genesis_engine_v2.engine.novelty_search import NoveltySearch

def run_novelty_experiment(generations=100, population_size=50):
    print("="*60)
    print(f"NOVELTY SEARCH EXPERIMENT ({generations} generations)")
    print("="*60)
    
    # Initialize Engine (using minimal settings for speed)
    engine = GenesisEngine(population_size=population_size, mutation_rate=0.2)
    
    # Initialize Novelty Search
    search = NoveltySearch(
        k_neighbors=15,
        archive_threshold=0.3, # Lower threshold for easier entry initially
        max_archive_size=500
    )
    
    print(f"Initialized with {population_size} agents.")
    print("Starting evolution loop...")
    print()
    print(f"{'Gen':<6} | {'Pop':<5} | {'Archive':<7} | {'MaxNov':<8} | {'AvgNov':<8} | {'AvgGAC':<8}")
    print("-" * 65)
    
    start_time = time.time()
    
    for gen in range(generations):
        # 1. Run Engine Cycle (Interaction, Physics, Aging)
        # We override the reproduction step, so we just run the physics/age interactions
        # engine.run_cycle() normally does everything. 
        # We need to intervene in the SELECTION phase.
        
        # GenesisEngine structure typically calls internal_evaluator.evaluate_population
        # then selection, then reproduction.
        
        # We will manually drive the cycle to inject Novelty Selection:
        
        # A. Pre-selection physics/interactions (if any)
        # engine.interaction_handler.process_interactions(engine.population) # Simplification
        
        # B. Novelty Selection & Reproduction
        parents = search.select_parents(engine.population, num_parents=population_size)
        
        # C. Create Offspring
        offspring = []
        for parent in parents:
            child = parent.reproduce(mutation_rate=engine.mutation_rate)
            offspring.append(child)
            
        # D. Replace Population
        # (Physics gatekeeper check typically happens here or in run_cycle)
        survivors, rejected = engine.physics_gatekeeper.enforce_population_constraints(offspring)
        
        # If too many rejected, fill with parents? Or just run with smaller pop?
        # For this test, we accept the survivors.
        engine.population = survivors
        
        # Ensure minimum population (cloning if needed)
        if len(engine.population) < population_size // 2 and len(engine.population) > 0:
             while len(engine.population) < population_size:
                 engine.population.append(random.choice(engine.population).reproduce())
                 
        if len(engine.population) == 0:
            print("EXTINCTION EVENT! Restarting...")
            engine = GenesisEngine(population_size=population_size)
            continue
            
        # Logging
        scores, _ = search.calculate_novelty_scores(engine.population)
        if scores:
            max_nov = max(scores.values())
            avg_nov = sum(scores.values()) / len(scores)
        else:
            max_nov = 0
            avg_nov = 0
            
        gac_avg = sum(a.genome.get_length() for a in engine.population) / len(engine.population)
        
        if (gen + 1) % 10 == 0 or gen == 0:
            print(f"{gen+1:<6} | {len(engine.population):<5} | {len(search.archive):<7} | {max_nov:.4f}   | {avg_nov:.4f}   | {gac_avg:.1f}")

    print("-" * 65)
    print(f"Completed in {time.time() - start_time:.2f}s")
    print(f"Final Archive Size: {len(search.archive)}")
    
    # Save Archive?
    # ...

import random
if __name__ == "__main__":
    run_novelty_experiment(generations=100)
