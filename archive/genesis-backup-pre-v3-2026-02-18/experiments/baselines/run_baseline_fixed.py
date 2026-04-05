"""
Baseline Experiment 2: Fixed Constraints (No CARP, No FSD)
Uses fixed constraint parameters without adaptive regulation.
"""

import argparse
import sys
import json
import time
from pathlib import Path
import traceback

# Add genesis engine to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'genesis_engine_v2'))

from engine.genesis_engine import GenesisEngine
from engine.codon_translator import CodonTranslator
from engine.diagnostics.pnct_metrics import PNCTLogger

class FixedGenesisEngine(GenesisEngine):
    """
    GenesisEngine variant with CARP and FSD disabled.
    Enforces static constraints.
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # We don't need to do anything special here, we'll just skip the
        # logic in run_cycle
        print("[FixedGenesisEngine] Initialized with Fixed Constraints (No CARP, No FSD)")

    def run_cycle(self):
        """
        Execute one generation cycle, skipping CARP and FSD.
        """
        # Step 1: Development
        # (Agents get traits directly from genome via CodonTranslator - handled in __init__ / reproduce)
        
        # Step 2: Simulation (Increment ages)
        for step in range(self.simulation_steps):
            for agent in self.population:
                agent.age += 1
            self.world.age += 1
        
        # SKIPPED: Step 2.2 Temporal Phase
        # SKIPPED: Step 2.4 Resource Interactions
        # We want PURE fixed constraints, so maybe we DO want resources?
        # "Fixed Constraints" usually implies just the hard physical constraints.
        # But if we skip resources, they die?
        # The prompt says: "Fixed Constraints... static parameters... (No CARP)".
        # It implies CARP is the independent variable being removed.
        # FSD is "adaptive regulation".
        # Resources are part of the detailed environment.
        # Let's keep resources but DISABLE the adaptive parts (Attributes of regions?).
        # Actually, let's look at the "No CARP" condition in the paper context.
        # Likely it means: Standard Genesis environment (Resources + Physics) but NO Predator-Prey and NO Dynamic Pressure.
        
        # Step 2.4: Resource Interactions (Keep this for basic survival/fitness)
        for agent in self.population:
            best_resource, _ = self.resource_system.get_best_resource_for_agent(agent)
            
            # Simple consumption
            resource_energy = self.resource_system.agent_consumes_resource(agent, best_resource)
            
            # Regional logic is static in default env, so that's fine.
            # Just skipping the complex adaptive stuff if any.
            
            if not hasattr(agent, 'resource_energy'):
                agent.resource_energy = 0.0
            agent.resource_energy += resource_energy
            
        self.resource_system.regenerate_resources()
        
        # SKIPPED: Step 2.45 Migration
        # SKIPPED: Step 2.48 Update Behavioral Traits (Only needed for CARP)
        # SKIPPED: Step 2.5 CARP
        # SKIPPED: Step 2.6 Innovation Tracking (FSD)
        
        # Step 3: Evaluation
        # We need calculate_fitness. 
        # GenesisEngine uses external_evaluator (None by default?) 
        # and internal_evaluator (Pareto).
        # Let's check run_cycle in GenesisEngine again? 
        # It calls calculate_fitness(agent, self.world).
        
        from engine.genesis_engine import calculate_fitness
        
        external_scores = {}
        for agent in self.population:
            external_scores[agent.id] = calculate_fitness(agent, self.world)
            
        # Step 3.5: Parent Viability
        viable_parents = []
        for agent in self.population:
            if self.physics_gatekeeper.check_viability_with_tracking(agent, 'parent'):
                 viable_parents.append(agent)
        self.population[:] = viable_parents
        
        # Step 3.6: Internal Evaluation
        internal_scores = self.internal_evaluator.evaluate_population(self.population)
        
        # Normalize
        normalized_external = self._normalize_scores(external_scores)
        normalized_internal = self._normalize_scores(internal_scores)
        
        final_scores = {}
        for agent in self.population:
            ext_norm = normalized_external[agent.id]
            int_norm = normalized_internal[agent.id]
            final_scores[agent.id] = (
                self.transition_weight * ext_norm +
                (1 - self.transition_weight) * int_norm
            )
            
        # Log stats
        self._log_statistics(external_scores, internal_scores, normalized_external, normalized_internal, final_scores, [])
        
        # Step 4: Selection
        num_parents = max(1, len(self.population) // 2)
        parents = self.select_parents(final_scores, num_parents)
        
        # Reproduction
        offspring = []
        if parents:
            offspring_per_parent = self.population_size // len(parents)
            remainder = self.population_size % len(parents)
            for i, parent in enumerate(parents):
                num = offspring_per_parent + (1 if i < remainder else 0)
                for _ in range(num):
                    offspring.append(parent.reproduce(self.mutation_rate))
        else:
            # Emergency restart if all died?
            # Or just let it go extinct.
            pass

        # Step 4.5: Gatekeeper (Offspring)
        viable_offspring = []
        for child in offspring:
            if self.physics_gatekeeper.check_viability_with_tracking(child, 'offspring'):
                viable_offspring.append(child)
        
        self.population = viable_offspring
        
        # Increment
        self.generation += 1


def run_fixed_baseline():
    parser = argparse.ArgumentParser()
    parser.add_argument('--seed', type=int, required=True, help='Random seed')
    parser.add_argument('--generations', type=int, default=10000, help='Generations')
    args = parser.parse_args()
    
    print(f"Starting Fixed Constraints Baseline (Seed={args.seed}, Gens={args.generations})")
    
    # Setup Paths
    root_dir = Path(__file__).parent.parent.parent
    results_dir = root_dir / 'results' / 'baselines'
    results_dir.mkdir(parents=True, exist_ok=True)
    
    # Initialize Engine
    engine = FixedGenesisEngine(
        population_size=50,
        mutation_rate=0.2, # Fixed
    )
    
    # Set seeds
    import numpy as np
    import random
    np.random.seed(args.seed)
    random.seed(args.seed)
    
    translator = CodonTranslator()
    # Log every 50 generations
    pnct_logger = PNCTLogger(gac_interval=50, nnd_interval=50, translator=translator)
    
    start_time = time.time()
    
    try:
        for gen in range(args.generations):
            engine.run_cycle()
            
            # Log Metrics
            pnct_logger.log_metrics(gen + 1, engine.population, engine.internal_evaluator, translator)
            
            # Simple Progress
            if (gen+1) % 1000 == 0:
                print(f"Gen {gen+1}/{args.generations} Pop={len(engine.population)}")
                
    except Exception as e:
        print(f"Error: {e}")
        traceback.print_exc()
        
    # Calculate Final Metrics
    final_gac = 0.0
    final_epc = 0.0
    
    if engine.population:
        # Use PNCT Logger history
        gac_hist = pnct_logger.get_gac_history()
        epc_hist = pnct_logger.get_epc_history()
        
        if gac_hist:
            final_gac = gac_hist[-1]['genome_length']['mean']
        if epc_hist:
            final_epc = epc_hist[-1]['lz_complexity']['mean']
        
    print(f"Final GAC: {final_gac}")
    print(f"Final EPC: {final_epc}")
    
    # Save Result
    result = {
        'seed': args.seed,
        'final_gac': final_gac,
        'final_epc': final_epc,
        'generations': args.generations
    }
    
    out_file = results_dir / f'fixed_constraints_seed_{args.seed}.json'
    with open(out_file, 'w') as f:
        json.dump(result, f, indent=2)
    
    # NEW: Save detailed time-series logs
    logs_path = results_dir / f"fixed_constraints_seed_{args.seed}_timeseries.json"
    timeseries_data = {
        'gac_history': pnct_logger.get_gac_history(),
        'epc_history': pnct_logger.get_epc_history(),
        'nnd_history': pnct_logger.get_nnd_history()
    }
    with open(logs_path, 'w') as f:
        json.dump(timeseries_data, f, indent=2)
        
    print(f"Saved to {out_file}")
    print(f"Saved timeseries to {logs_path}")

if __name__ == '__main__':
    run_fixed_baseline()
