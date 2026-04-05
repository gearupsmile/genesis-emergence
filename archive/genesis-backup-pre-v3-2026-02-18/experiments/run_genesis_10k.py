"""
Standard Genesis Experiment (10k Generations)

Replicates the main experimental condition described in the paper:
"In twelve independent Genesis runs of 10,000 generations each, external fitness 
is progressively eliminated..."

Configuration:
- Total Generations: 10,000
- Transition Period: 5,000 (Fitness removed linearly)
- Post-Transition: 5,000 (Pure endogenous evolution)
- Population: 50
- Mutation Rate: 0.1
"""

import argparse
import sys
import json
import time
from pathlib import Path
import random
import numpy as np

# Add genesis engine to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'genesis_engine_v2'))

from engine.genesis_engine import GenesisEngine
from engine.codon_translator import CodonTranslator

def run_genesis_experiment():
    parser = argparse.ArgumentParser()
    parser.add_argument('--seed', type=int, required=True, help='Random seed')
    parser.add_argument('--generations', type=int, default=10000, help='Total generations')
    parser.add_argument('--transition', type=int, default=5000, help='Generations to eliminate fitness')
    args = parser.parse_args()
    
    print(f"Starting Genesis Experiment (Seed={args.seed})")
    print(f"  Total Generations: {args.generations}")
    print(f"  Transition Period: {args.transition}")
    print(f"  Phase 1 (Mixed): Gens 0-{args.transition}")
    print(f"  Phase 2 (Endogenous): Gens {args.transition}-{args.generations}")
    
    # Setup Paths
    root_dir = Path(__file__).parent.parent
    results_dir = root_dir / 'results' / 'genesis_main'
    results_dir.mkdir(parents=True, exist_ok=True)
    
    # Set seeds
    random.seed(args.seed)
    np.random.seed(args.seed)
    
    # Initialize Engine
    # Standard configuration matching baselines where possible
    engine = GenesisEngine(
        population_size=50,
        mutation_rate=0.1,  # Standard baseline rate
        transition_start_generation=0,
        transition_total_generations=args.transition
    )
    
    # Tracking
    history = []
    
    start_time = time.time()
    
    try:
        for gen in range(args.generations):
            engine.run_cycle()
            
            # Log every 50 generations (high res for figures)
            if (gen + 1) % 50 == 0:
                stats = engine.statistics[-1]
                
                # Capture metrics
                record = {
                    'generation': gen + 1,
                    'transition_weight': stats.get('transition_weight', 0.0),
                    'gac': stats.get('avg_genome_length', 0),
                    'epc': stats.get('avg_internal_score', 0), # Using internal score as EPC proxy in this context
                    'pop_size': len(engine.population)
                }
                history.append(record)
                
                # Progress print
                if (gen + 1) % 1000 == 0:
                    print(f"Gen {gen+1}/{args.generations} "
                          f"Weight={record['transition_weight']:.2f} "
                          f"GAC={record['gac']:.2f}")

    except Exception as e:
        print(f"[ERROR] Run failed: {e}")
        import traceback
        traceback.print_exc()
        
    # Final save
    outfile = results_dir / f"genesis_seed_{args.seed}.json"
    
    output_data = {
        'seed': args.seed,
        'config': vars(args),
        'history': history,
        'final_stats': engine.statistics[-1] if engine.statistics else {}
    }
    
    with open(outfile, 'w') as f:
        json.dump(output_data, f, indent=2)
        
    print(f"completed. Results saved to {outfile}")

if __name__ == '__main__':
    run_genesis_experiment()
