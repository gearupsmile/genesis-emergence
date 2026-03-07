"""
Novelty Search Baseline - Final Experiment

Runs the Novelty Search algorithm under the EXACT same conditions as the 
main 'Deep Probe' experiment (200k generations, pop=50) to provide a 
fair baseline for comparing Open-Endedness.

differences:
- Replaces fitness-based selection with Novelty Search (sparsity in GAC/EPC/NND space).
- Logs Archive Size alongside standard metrics.
"""

import sys
import os
import gc
import json
import argparse
from pathlib import Path
import time
from datetime import datetime
import signal

# Disable output buffering
sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)

# Add genesis_engine_v2 to path (assuming deep inside experiments/baselines)
# ../../genesis_engine_v2
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'genesis_engine_v2'))

from engine.genesis_engine import GenesisEngine
from engine.novelty_search import NoveltySearch
from engine.codon_translator import CodonTranslator
from engine.diagnostics.pnct_metrics import PNCTLogger
from engine.diagnostics.resource_profiler import ResourceProfiler

# Global state
shutdown_requested = False

def signal_handler(sig, frame):
    global shutdown_requested
    print("\n[SIGNAL] Shutdown requested...")
    shutdown_requested = True

class NoveltyGenesisEngine(GenesisEngine):
    """
    GenesisEngine variant that uses Novelty Search for selection.
    All other physics/aging/interaction logic is identical to base engine.
    """
    def __init__(self, population_size, mutation_rate, simulation_steps=10):
        super().__init__(population_size, mutation_rate, simulation_steps)
        # Initialize Novelty Search
        self.novelty_search = NoveltySearch(
            k_neighbors=15,
            archive_threshold=0.3,
            max_archive_size=2000  # Larger archive for 200k run
        )
        print("[NoveltyGenesisEngine] Initialized with Novelty Search Selection")

    def select_parents(self, final_scores, num_parents):
        """Override standard selection with Novelty Selection."""
        # Note: final_scores are ignored, we use novelty scores
        return self.novelty_search.select_parents(self.population, num_parents)

def run_novelty_baseline():
    """Run the Novelty Search baseline."""
    global shutdown_requested
    
    parser = argparse.ArgumentParser()
    parser.add_argument('--seed', type=int, default=42, help='Random seed')
    parser.add_argument('--generations', type=int, default=200000, help='Total generations')
    args = parser.parse_args()
    
    # Set seeds
    import numpy as np
    import random
    np.random.seed(args.seed)
    random.seed(args.seed)
    
    signal.signal(signal.SIGINT, signal_handler)
    
    print("=" * 70)
    print(f"NOVELTY SEARCH BASELINE (Seed={args.seed})")
    print("=" * 70)
    
    # Configuration
    total_gens = args.generations
    population_size = 50
    mutation_rate = 0.3
    checkpoint_interval = 10000
    memory_log_interval = 500
    
    # Create run directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = Path("runs") / f"novelty_search_seed_{args.seed}_{timestamp}"
    run_dir.mkdir(parents=True, exist_ok=True)
    
    # Also ensure results/baselines exists for final JSON
    results_dir = Path("results/baselines")
    results_dir.mkdir(parents=True, exist_ok=True)
    
    (run_dir / "logs").mkdir(exist_ok=True)
    (run_dir / "checkpoints").mkdir(exist_ok=True)
    
    # Logging
    log_file = open(run_dir / "logs" / "run.log", 'w', buffering=1)
    def log_print(msg):
        print(msg)
        log_file.write(msg + "\n")
        log_file.flush()
        
    log_print(f"Run Directory: {run_dir}")
    log_print(f"Configuration: Pop={population_size}, Mut={mutation_rate}, Gens={total_gens}")
    
    # Initialize components
    profiler = ResourceProfiler(log_file=str(run_dir / "logs" / "resource_profile.log"))
    translator = CodonTranslator()
    # Log every 50 generations for high-res plots
    pnct_logger = PNCTLogger(gac_interval=50, nnd_interval=50, translator=translator)
    
    # Initialize Engine
    engine = NoveltyGenesisEngine(
        population_size=population_size,
        mutation_rate=mutation_rate
    )
    
    log_print("\nRUNNING EVOLUTION")
    log_print(f"{'Gen':>8} {'Pop':>5} {'Arch':>5} {'GAC':>7} {'EPC':>7} {'NovScore':>8} {'Mem(MB)':>9} {'Gen/s':>7}")
    log_print("-" * 80)
    
    start_time = time.time()
    
    try:
        for gen in range(total_gens):
            if shutdown_requested:
                break
                
            # Run Cycle (Physics -> Interactions -> Selection (Novelty) -> Reproduction)
            engine.run_cycle()
            
            # Logging logic
            pnct_logger.log_metrics(gen + 1, engine.population, engine.internal_evaluator, translator)
            
            if (gen + 1) % memory_log_interval == 0:
                profiler.log_resources(gen + 1)
                
            if (gen + 1) % checkpoint_interval == 0:
                log_print(f"  [CHECKPOINT] Generation {gen+1}")
                # Save checkpoint logic here if needed
                
            # Reporting (Console every 1000)
            if (gen + 1) % 1000 == 0 or (gen+1) == total_gens: 
                current_time = time.time()
                elapsed = current_time - start_time
                gens_per_sec = (gen + 1) / elapsed
                
                # Metrics
                gac_hist = pnct_logger.get_gac_history()
                epc_hist = pnct_logger.get_epc_history()
                gac_mean = gac_hist[-1]['genome_length']['mean'] if gac_hist else 0.0
                epc_mean = epc_hist[-1]['lz_complexity']['mean'] if epc_hist else 0.0
                
                # Novelty Metrics
                archive_size = len(engine.novelty_search.archive)
                
                # Quick re-calc for logging
                scores, _ = engine.novelty_search.calculate_novelty_scores(engine.population)
                avg_novelty = sum(scores.values()) / len(scores) if scores else 0
                
                memory_mb = profiler.get_memory_mb()
                
                log_print(f"{gen+1:8d} {len(engine.population):5d} {archive_size:5d} "
                          f"{gac_mean:7.1f} {epc_mean:7.3f} {avg_novelty:8.4f} "
                          f"{memory_mb:9.1f} {gens_per_sec:7.1f}")
                          
    except Exception as e:
        log_print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc(file=log_file)
        
    finally:
        total_time = time.time() - start_time
        log_print("-" * 80)
        log_print(f"Complete. Total time: {total_time:.2f}s")
        log_print(f"Final Archive Size: {len(engine.novelty_search.archive)}")
        
        # Calculate Final Metrics
        final_gac = 0.0
        final_epc = 0.0
        if engine.population:
            final_gac = sum(a.genome.get_length() for a in engine.population) / len(engine.population)
            epc_hist = pnct_logger.get_epc_history()
            if epc_hist:
                 final_epc = epc_hist[-1]['lz_complexity']['mean']
        
        # Save JSON result (Summary)
        result = {
            'seed': args.seed,
            'final_gac': final_gac,
            'final_epc': final_epc,
            'archive_size': len(engine.novelty_search.archive),
            'generations': total_gens
        }
        json_path = results_dir / f"novelty_search_seed_{args.seed}.json"
        with open(json_path, 'w') as f:
            json.dump(result, f, indent=2)
            
        # NEW: Save detailed time-series logs
        logs_path = results_dir / f"novelty_search_seed_{args.seed}_timeseries.json"
        timeseries_data = {
            'gac_history': pnct_logger.get_gac_history(),
            'epc_history': pnct_logger.get_epc_history(),
            'nnd_history': pnct_logger.get_nnd_history()
        }
        with open(logs_path, 'w') as f:
            json.dump(timeseries_data, f, indent=2)
            
        log_print(f"Saved metrics to {json_path}")
        log_print(f"Saved timeseries to {logs_path}")
        
        log_file.close()
        profiler.cleanup()

if __name__ == '__main__':
    run_novelty_baseline()
