"""
Final Deep Probe Launch Script

Launches the definitive 200,000-generation experiment with:
- Comprehensive monitoring
- Interim analysis at checkpoints
- Automatic completion analysis
- Recovery from interruptions
- Resource tracking

Estimated runtime: ~2.1 hours (based on 1k-gen test)
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
from engine.verification.constraint_checker import ConstraintChecker


# Global state
shutdown_requested = False
experiment_state = {
    'start_time': None,
    'generations_completed': 0,
    'last_checkpoint': 0
}


def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully."""
    global shutdown_requested
    print("\n\n[INTERRUPT] Graceful shutdown requested...")
    print("Saving current state...")
    shutdown_requested = True


def create_experiment_directory():
    """Create timestamped experiment directory."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = Path("runs") / f"deep_probe_200k_{timestamp}"
    run_dir.mkdir(parents=True, exist_ok=True)
    
    # Create subdirectories
    (run_dir / "checkpoints").mkdir(exist_ok=True)
    (run_dir / "logs").mkdir(exist_ok=True)
    (run_dir / "interim_analysis").mkdir(exist_ok=True)
    
    return run_dir


def save_checkpoint(engine, pnct_logger, run_dir, generation, validate=True):
    """Save checkpoint with optional integrity validation."""
    checkpoint_file = run_dir / "checkpoints" / f"checkpoint_{generation:06d}.pkl"
    
    checkpoint_data = {
        'generation': generation,
        'statistics': engine.statistics,
        'gac_history': pnct_logger.get_gac_history(),
        'epc_history': pnct_logger.get_epc_history(),
        'nnd_history': pnct_logger.get_nnd_history(),
        'population_size': len(engine.population),
        'transition_weight': engine.transition_weight,
        'timestamp': datetime.now().isoformat()
    }
    
    # Save with retry logic
    max_attempts = 3
    for attempt in range(max_attempts):
        try:
            with open(checkpoint_file, 'wb') as f:
                pickle.dump(checkpoint_data, f)
            
            # Validate if requested
            if validate:
                with open(checkpoint_file, 'rb') as f:
                    test_load = pickle.load(f)
                    if test_load['generation'] != generation:
                        raise ValueError("Checkpoint validation failed")
            
            print(f"  [CHECKPOINT] Saved and validated: {checkpoint_file.name}")
            return True
            
        except Exception as e:
            print(f"  [WARNING] Checkpoint save attempt {attempt+1} failed: {e}")
            if attempt == max_attempts - 1:
                print(f"  [ERROR] Failed to save checkpoint after {max_attempts} attempts")
                return False
            time.sleep(1)
    
    return False


def run_interim_analysis(run_dir, generation):
    """Run quick analysis at checkpoint."""
    print(f"\n  [INTERIM ANALYSIS] Generation {generation:,}")
    
    analysis_dir = run_dir / "interim_analysis" / f"checkpoint_{generation:06d}"
    analysis_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        # Import analysis modules
        sys.path.insert(0, str(Path(__file__).parent.parent / 'analysis'))
        from phase6_analyzer import DeepProbeAnalyzer
        from visualization import plot_gac_trajectory, plot_epc_trajectory
        
        # Load data
        analyzer = DeepProbeAnalyzer(str(run_dir))
        data = analyzer.load_and_process()
        
        # Generate quick plots
        plot_gac_trajectory(data, analysis_dir)
        plot_epc_trajectory(data, analysis_dir)
        
        # Quick stats
        if data['gac']:
            gac_current = data['gac'][-1]['genome_mean']
            gac_start = data['gac'][0]['genome_mean']
            gac_growth = ((gac_current - gac_start) / gac_start * 100) if gac_start > 0 else 0
            print(f"    GAC: {gac_start:.1f} -> {gac_current:.1f} ({gac_growth:+.1f}%)")
        
        if data['epc']:
            epc_current = data['epc'][-1]['lz_mean']
            epc_start = data['epc'][0]['lz_mean']
            print(f"    EPC: {epc_start:.3f} -> {epc_current:.3f}")
        
        print(f"    Plots saved to: {analysis_dir}")
        
    except Exception as e:
        print(f"    [WARNING] Interim analysis failed: {e}")


def save_metrics_csv(pnct_logger, run_dir):
    """Save PNCT metrics to CSV."""
    csv_file = run_dir / "logs" / "pnct_metrics.csv"
    
    with open(csv_file, 'w') as f:
        # Header
        f.write("generation,gac_genome_mean,gac_genome_median,gac_linkage_mean,")
        f.write("epc_lz_mean,epc_lz_p90,epc_diversity_mean,")
        f.write("nnd_mean,nnd_front_size\n")
        
        # Merge histories
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


def run_final_deep_probe(dry_run=False, skip_verification=False):
    """Execute the final 200k-generation Deep Probe experiment."""
    global shutdown_requested, experiment_state
    
    # Set up signal handler
    signal.signal(signal.SIGINT, signal_handler)
    
    print("=" * 70)
    print("FINAL DEEP PROBE: 200,000-GENERATION EXPERIMENT")
    if dry_run:
        print("(DRY RUN MODE: 5,000 generations)")
    print("=" * 70)
    print()
    
    # Configuration
    total_gens = 5000 if dry_run else 200000
    population_size = 100
    mutation_rate = 0.3
    checkpoint_interval = 1000 if dry_run else 25000
    gac_interval = 500
    nnd_interval = 1000
    report_interval = 500 if dry_run else 5000
    
    print("Configuration:")
    print(f"  Total generations: {total_gens:,}")
    print(f"  Population: {population_size}")
    print(f"  Mutation rate: {mutation_rate}")
    print(f"  Checkpoints: Every {checkpoint_interval:,} gens")
    print(f"  PNCT logging: GAC/EPC every {gac_interval}, NND every {nnd_interval}")
    print()
    
    # Create experiment directory
    run_dir = create_experiment_directory()
    print(f"Experiment directory: {run_dir}")
    print()
    
    # MANDATORY PRE-FLIGHT VERIFICATION
    if not skip_verification:
        verification_log = run_dir / "logs" / "verification_report.log"
        checker = ConstraintChecker(log_file=str(verification_log))
        
        if not checker.run_all_checks():
            print()
            print("=" * 70)
            print("CRITICAL: EVOLUTIONARY CONSTRAINT VIOLATED")
            print("=" * 70)
            print()
            print("One or more critical evolutionary constraints failed verification.")
            print("The experiment CANNOT proceed until these issues are resolved.")
            print()
            print(f"See detailed report: {verification_log}")
            print()
            sys.exit(1)
    else:
        print("[WARNING] Constraint verification SKIPPED (--skip-verification flag)")
        print()
    
    # Copy config
    try:
        shutil.copy("configs/final_deep_probe.yaml", run_dir / "config_used.yaml")
    except:
        pass
    
    # Initialize engine
    print("Initializing GenesisEngine...")
    engine = GenesisEngine(
        population_size=population_size,
        mutation_rate=mutation_rate,
        simulation_steps=10,
        transition_start_generation=0,
        transition_total_generations=10000
    )
    
    translator = CodonTranslator()
    pnct_logger = PNCTLogger(
        gac_interval=gac_interval,
        nnd_interval=nnd_interval,
        translator=translator
    )
    
    print("  Engine initialized")
    print()
    
    # Run evolution
    print("=" * 70)
    print("RUNNING EVOLUTION")
    print("=" * 70)
    print()
    print(f"{'Gen':>8} {'Pop':>5} {'GAC':>7} {'EPC_LZ':>8} {'NND':>7} {'Time':>10} {'Gen/s':>8} {'ETA':>12}")
    print("-" * 70)
    
    experiment_state['start_time'] = time.time()
    last_report_time = experiment_state['start_time']
    
    for gen in range(total_gens):
        if shutdown_requested:
            print("\n[SHUTDOWN] Saving final checkpoint...")
            save_checkpoint(engine, pnct_logger, run_dir, gen)
            save_metrics_csv(pnct_logger, run_dir)
            print(f"[SHUTDOWN] Stopped at generation {gen}")
            return
        
        # Run one generation
        try:
            engine.run_cycle()
        except Exception as e:
            print(f"\n[ERROR] Generation {gen}: {e}")
            save_checkpoint(engine, pnct_logger, run_dir, gen)
            raise
        
        # Log PNCT metrics
        pnct_logger.log_metrics(
            gen + 1,
            engine.population,
            engine.internal_evaluator,
            translator
        )
        
        # Early termination check
        if len(engine.population) < 10:
            print(f"\n[EARLY TERMINATION] Population collapsed to {len(engine.population)} agents")
            save_checkpoint(engine, pnct_logger, run_dir, gen + 1)
            save_metrics_csv(pnct_logger, run_dir)
            return
        
        # Progress reporting
        if (gen + 1) % report_interval == 0 or gen == 0:
            current_time = time.time()
            elapsed = current_time - experiment_state['start_time']
            interval_time = current_time - last_report_time
            last_report_time = current_time
            
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
            
            print(f"{gen+1:8d} {len(engine.population):5d} "
                  f"{gac_mean:7.1f} {epc_lz:8.3f} {nnd_mean:7.3f} "
                  f"{interval_time:10.2f}s "
                  f"{gens_per_sec:8.1f} "
                  f"{eta_seconds/60:9.1f} min")
        
        # Checkpointing
        if (gen + 1) % checkpoint_interval == 0:
            save_checkpoint(engine, pnct_logger, run_dir, gen + 1)
            
            # Interim analysis
            if not dry_run:
                run_interim_analysis(run_dir, gen + 1)
        
        experiment_state['generations_completed'] = gen + 1
    
    # Completion
    total_time = time.time() - experiment_state['start_time']
    print("-" * 70)
    print(f"Total time: {total_time:.2f}s ({total_time/60:.2f} min, {total_time/3600:.2f} hours)")
    print()
    
    # Save final data
    print("Saving final data...")
    save_checkpoint(engine, pnct_logger, run_dir, total_gens)
    save_metrics_csv(pnct_logger, run_dir)
    print()
    
    # Run full analysis
    if not dry_run:
        print("=" * 70)
        print("RUNNING COMPREHENSIVE ANALYSIS")
        print("=" * 70)
        print()
        
        try:
            sys.path.insert(0, str(Path(__file__).parent.parent / 'analysis'))
            from report_generator import generate_phase6_report
            
            result = generate_phase6_report(str(run_dir))
            
            print()
            print("=" * 70)
            print("PIVOT DECISION")
            print("=" * 70)
            print(f"Recommendation: {result['decision']['recommendation']}")
            print(f"Confidence: {result['decision']['confidence_score']}%")
            print()
            print("Key Evidence:")
            for i, evidence in enumerate(result['decision']['key_evidence'], 1):
                print(f"  {i}. {evidence}")
            print()
            
        except Exception as e:
            print(f"[WARNING] Automated analysis failed: {e}")
            print("Run manually: python analysis/report_generator.py <run_dir>")
    
    print("=" * 70)
    print("EXPERIMENT COMPLETE")
    print("=" * 70)
    print(f"\nResults saved to: {run_dir}")
    print()


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Launch Final Deep Probe Experiment')
    parser.add_argument('--dry-run', action='store_true', 
                       help='Run 5,000-generation dry run instead of full 200k')
    parser.add_argument('--skip-verification', action='store_true',
                       help='Skip pre-flight constraint verification (NOT RECOMMENDED)')
    
    args = parser.parse_args()
    
    try:
        run_final_deep_probe(dry_run=args.dry_run, skip_verification=args.skip_verification)
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
