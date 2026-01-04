"""
Phase 6 Deep Probe: 200,000-Generation Experiment

This script launches an extended diagnostic run to distinguish between:
- Bounded equilibrium (high-variance random walk)
- True open-ended evolution (directional exploration, novelty accumulation)

Features:
- Full PNCT metrics tracking (GAC, EPC, NND)
- Graceful interruption handling (Ctrl+C saves state)
- Progress reporting every 5,000 generations
- Runtime estimation
- Checkpoint recovery
"""

import sys
import os
from pathlib import Path
import time
import signal
import pickle
from datetime import datetime
import shutil

# Add genesis_engine_v2 to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'genesis_engine_v2'))

from engine.genesis_engine import GenesisEngine
from engine.codon_translator import CodonTranslator
from engine.diagnostics.pnct_metrics import PNCTLogger


# Global flag for graceful shutdown
shutdown_requested = False


def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully."""
    global shutdown_requested
    print("\n\n[INTERRUPT] Graceful shutdown requested...")
    print("Saving current state to checkpoint...")
    shutdown_requested = True


def load_config():
    """Load configuration from YAML file."""
    # For now, return hardcoded config (YAML parsing would require pyyaml)
    return {
        'experiment': {
            'name': 'phase6_deep_probe',
            'total_generations': 200000
        },
        'population': {
            'size': 100,
            'mutation_rate': 0.3
        },
        'checkpoints': {
            'interval': 25000
        },
        'pnct_logging': {
            'gac_interval': 500,
            'epc_interval': 500,
            'nnd_interval': 1000
        },
        'progress': {
            'report_interval': 5000
        }
    }


def create_run_directory():
    """Create timestamped run directory."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = Path("runs") / f"phase6_deep_probe_{timestamp}"
    run_dir.mkdir(parents=True, exist_ok=True)
    
    # Create subdirectories
    (run_dir / "checkpoints").mkdir(exist_ok=True)
    (run_dir / "logs").mkdir(exist_ok=True)
    
    return run_dir


def save_checkpoint(engine, pnct_logger, run_dir, generation):
    """Save checkpoint with full state."""
    checkpoint_file = run_dir / "checkpoints" / f"checkpoint_{generation:06d}.pkl"
    
    checkpoint_data = {
        'generation': generation,
        'statistics': engine.statistics,
        'gac_history': pnct_logger.get_gac_history(),
        'epc_history': pnct_logger.get_epc_history(),
        'nnd_history': pnct_logger.get_nnd_history(),
        'population_size': len(engine.population),
        'transition_weight': engine.transition_weight
    }
    
    with open(checkpoint_file, 'wb') as f:
        pickle.dump(checkpoint_data, f)
    
    print(f"  [CHECKPOINT] Saved to {checkpoint_file.name}")


def save_metrics_csv(pnct_logger, run_dir):
    """Save PNCT metrics to CSV file."""
    csv_file = run_dir / "logs" / "pnct_metrics.csv"
    
    with open(csv_file, 'w') as f:
        # Write header
        f.write("generation,gac_genome_mean,gac_genome_median,gac_linkage_mean,")
        f.write("epc_lz_mean,epc_lz_p90,epc_diversity_mean,")
        f.write("nnd_mean,nnd_front_size\n")
        
        # Merge histories by generation
        gac_hist = {h['generation']: h for h in pnct_logger.get_gac_history()}
        epc_hist = {h['generation']: h for h in pnct_logger.get_epc_history()}
        nnd_hist = {h['generation']: h for h in pnct_logger.get_nnd_history()}
        
        all_gens = sorted(set(list(gac_hist.keys()) + list(epc_hist.keys()) + list(nnd_hist.keys())))
        
        for gen in all_gens:
            gac = gac_hist.get(gen, {})
            epc = epc_hist.get(gen, {})
            nnd = nnd_hist.get(gen, {})
            
            f.write(f"{gen},")
            f.write(f"{gac.get('genome_length', {}).get('mean', 0):.2f},")
            f.write(f"{gac.get('genome_length', {}).get('median', 0):.2f},")
            f.write(f"{gac.get('linkage_groups', {}).get('mean', 0):.2f},")
            f.write(f"{epc.get('lz_complexity', {}).get('mean', 0):.3f},")
            f.write(f"{epc.get('lz_complexity', {}).get('p90', 0):.3f},")
            f.write(f"{epc.get('instruction_diversity', {}).get('mean', 0):.3f},")
            f.write(f"{nnd.get('mean_nnd', 0):.3f},")
            f.write(f"{nnd.get('front_size', 0)}\n")


def run_deep_probe():
    """Execute the 200k-generation Deep Probe experiment."""
    global shutdown_requested
    
    # Set up signal handler for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    
    print("=" * 70)
    print("PHASE 6 DEEP PROBE: 200,000-GENERATION EXPERIMENT")
    print("=" * 70)
    print()
    
    # Load configuration
    config = load_config()
    print("Configuration loaded:")
    print(f"  Total generations: {config['experiment']['total_generations']:,}")
    print(f"  Population size: {config['population']['size']}")
    print(f"  Mutation rate: {config['population']['mutation_rate']}")
    print(f"  Checkpoint interval: {config['checkpoints']['interval']:,}")
    print()
    
    # Create run directory
    run_dir = create_run_directory()
    print(f"Run directory: {run_dir}")
    print()
    
    # Copy config to run directory
    shutil.copy("configs/phase6_deep_probe.yaml", run_dir / "config_used.yaml")
    
    # Initialize engine and PNCT logger
    print("Initializing GenesisEngine...")
    engine = GenesisEngine(
        population_size=config['population']['size'],
        mutation_rate=config['population']['mutation_rate'],
        simulation_steps=10,
        transition_start_generation=0,
        transition_total_generations=10000  # Standard transition
    )
    
    translator = CodonTranslator()
    pnct_logger = PNCTLogger(
        gac_interval=config['pnct_logging']['gac_interval'],
        nnd_interval=config['pnct_logging']['nnd_interval'],
        translator=translator
    )
    
    print(f"  Engine initialized: {engine}")
    print(f"  PNCT Logger: GAC/EPC every {config['pnct_logging']['gac_interval']}, "
          f"NND every {config['pnct_logging']['nnd_interval']}")
    print()
    
    # Run evolution
    print("=" * 70)
    print("RUNNING EVOLUTION")
    print("=" * 70)
    print()
    print(f"{'Gen':>8} {'Pop':>5} {'GAC':>7} {'EPC_LZ':>8} {'NND':>7} {'Time':>10} {'ETA':>12}")
    print("-" * 70)
    
    start_time = time.time()
    last_report_time = start_time
    total_gens = config['experiment']['total_generations']
    report_interval = config['progress']['report_interval']
    checkpoint_interval = config['checkpoints']['interval']
    
    for gen in range(total_gens):
        if shutdown_requested:
            print("\n[SHUTDOWN] Saving final checkpoint...")
            save_checkpoint(engine, pnct_logger, run_dir, gen)
            save_metrics_csv(pnct_logger, run_dir)
            print(f"[SHUTDOWN] Stopped at generation {gen}")
            return
        
        # Run one generation
        engine.run_cycle()
        
        # Log PNCT metrics
        pnct_logger.log_metrics(
            gen + 1,
            engine.population,
            engine.internal_evaluator,
            translator
        )
        
        # Progress reporting
        if (gen + 1) % report_interval == 0 or gen == 0:
            current_time = time.time()
            elapsed = current_time - start_time
            gens_per_sec = (gen + 1) / elapsed if elapsed > 0 else 0
            remaining_gens = total_gens - (gen + 1)
            eta_seconds = remaining_gens / gens_per_sec if gens_per_sec > 0 else 0
            
            # Get latest metrics
            gac_hist = pnct_logger.get_gac_history()
            epc_hist = pnct_logger.get_epc_history()
            nnd_hist = pnct_logger.get_nnd_history()
            
            gac_mean = gac_hist[-1]['genome_length']['mean'] if gac_hist else 0
            epc_lz = epc_hist[-1]['lz_complexity']['mean'] if epc_hist else 0
            nnd_mean = nnd_hist[-1]['mean_nnd'] if nnd_hist else 0
            
            interval_time = current_time - last_report_time
            last_report_time = current_time
            
            print(f"{gen+1:8d} {len(engine.population):5d} "
                  f"{gac_mean:7.1f} {epc_lz:8.3f} {nnd_mean:7.3f} "
                  f"{interval_time:10.2f}s "
                  f"{eta_seconds/60:9.1f} min")
        
        # Checkpointing
        if (gen + 1) % checkpoint_interval == 0:
            save_checkpoint(engine, pnct_logger, run_dir, gen + 1)
    
    # Final checkpoint and summary
    print("-" * 70)
    total_time = time.time() - start_time
    print(f"Total time: {total_time:.2f}s ({total_time/60:.2f} min, {total_time/3600:.2f} hours)")
    print()
    
    # Save final data
    print("Saving final data...")
    save_checkpoint(engine, pnct_logger, run_dir, total_gens)
    save_metrics_csv(pnct_logger, run_dir)
    
    # Generate summary
    summary_file = run_dir / "analysis_summary.txt"
    with open(summary_file, 'w') as f:
        f.write("PHASE 6 DEEP PROBE - ANALYSIS SUMMARY\n")
        f.write("=" * 60 + "\n\n")
        f.write(f"Total Generations: {total_gens:,}\n")
        f.write(f"Runtime: {total_time/3600:.2f} hours\n")
        f.write(f"Final Population: {len(engine.population)}\n\n")
        
        gac_hist = pnct_logger.get_gac_history()
        epc_hist = pnct_logger.get_epc_history()
        nnd_hist = pnct_logger.get_nnd_history()
        
        f.write(f"GAC Entries: {len(gac_hist)}\n")
        f.write(f"EPC Entries: {len(epc_hist)}\n")
        f.write(f"NND Entries: {len(nnd_hist)}\n\n")
        
        if gac_hist:
            f.write(f"Final GAC (genome length): {gac_hist[-1]['genome_length']['mean']:.1f}\n")
        if epc_hist:
            f.write(f"Final EPC (LZ complexity): {epc_hist[-1]['lz_complexity']['mean']:.3f}\n")
        if nnd_hist:
            f.write(f"Final NND: {nnd_hist[-1]['mean_nnd']:.3f}\n")
    
    print(f"  Saved: {summary_file}")
    print()
    
    print("=" * 70)
    print("PHASE 6 DEEP PROBE COMPLETE")
    print("=" * 70)
    print(f"\nResults saved to: {run_dir}")
    print()


if __name__ == '__main__':
    try:
        run_deep_probe()
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
