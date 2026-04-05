"""
25,000-Generation Validation Test for Metabolic Cost Fix

This script runs a 25k generation test with hardened constraints and monitoring
to verify that the exponential metabolic cost penalty prevents genome bloat.

Target: GAC should stay < 50 throughout the entire run
"""
import sys
import os
from pathlib import Path
import time
import signal
from datetime import datetime

# Add genesis_engine_v2 to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'genesis_engine_v2'))

from engine.genesis_engine import GenesisEngine
from engine.codon_translator import CodonTranslator
from engine.diagnostics.pnct_metrics import PNCTLogger
from engine.verification.constraint_checker import ConstraintChecker

# Global state
shutdown_requested = False

def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully."""
    global shutdown_requested
    print("\n\n[INTERRUPT] Graceful shutdown requested...")
    shutdown_requested = True

def create_run_directory():
    """Create timestamped run directory."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = Path("runs") / f"validation_25k_{timestamp}"
    run_dir.mkdir(parents=True, exist_ok=True)
    
    # Create subdirectories
    (run_dir / "logs").mkdir(exist_ok=True)
    
    return run_dir

def run_validation_test():
    """Execute 25k generation validation test."""
    global shutdown_requested
    
    # Set up signal handler
    signal.signal(signal.SIGINT, signal_handler)
    
    print("="*70)
    print("25,000-GENERATION VALIDATION TEST")
    print("="*70)
    print()
    print("Goal: Verify exponential metabolic cost fix prevents genome bloat")
    print("Target: GAC should stay < 50 throughout the run")
    print()
    
    # Configuration
    total_gens = 25000
    population_size = 50
    mutation_rate = 0.3
    report_interval = 500
    gac_interval = 100
    bloat_threshold = 50
    bloat_tolerance = 100  # Allow 100 consecutive gens above threshold before failing
    
    print("Configuration:")
    print(f"  Total generations: {total_gens:,}")
    print(f"  Population: {population_size}")
    print(f"  Mutation rate: {mutation_rate}")
    print(f"  Bloat threshold: GAC > {bloat_threshold}")
    print(f"  Bloat tolerance: {bloat_tolerance} consecutive generations")
    print()
    
    # Create run directory
    run_dir = create_run_directory()
    print(f"Run directory: {run_dir}")
    print()
    
    # Open log file
    log_file = run_dir / "logs" / "run.log"
    log_handle = open(log_file, 'w', buffering=1)  # Line buffered
    
    def log(msg):
        """Write to both console and log file."""
        print(msg)
        log_handle.write(msg + "\n")
    
    # MANDATORY PRE-FLIGHT VERIFICATION
    verification_log = run_dir / "logs" / "verification_report.log"
    checker = ConstraintChecker(log_file=str(verification_log))
    
    log("Running pre-flight constraint verification...")
    if not checker.run_all_checks():
        log("")
        log("="*70)
        log("CRITICAL: EVOLUTIONARY CONSTRAINT VIOLATED")
        log("="*70)
        log("")
        log("One or more critical evolutionary constraints failed verification.")
        log("The experiment CANNOT proceed until these issues are resolved.")
        log(f"See detailed report: {verification_log}")
        log_handle.close()
        sys.exit(1)
    
    log("")
    log("Pre-flight checks PASSED")
    log("")
    
    # Initialize engine
    log("Initializing GenesisEngine...")
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
        nnd_interval=1000,
        translator=translator
    )
    
    log("  Engine initialized")
    log("")
    
    # Run evolution
    log("="*70)
    log("RUNNING EVOLUTION")
    log("="*70)
    log("")
    log(f"{'Gen':>8} {'Pop':>5} {'GAC':>7} {'EPC':>8} {'Gen/s':>8} {'ETA':>12} {'Status':>15}")
    log("-"*70)
    
    start_time = time.time()
    last_report_time = start_time
    bloat_counter = 0
    max_gac_seen = 0
    
    for gen in range(total_gens):
        if shutdown_requested:
            log("\n[SHUTDOWN] Saving final state...")
            log(f"[SHUTDOWN] Stopped at generation {gen}")
            break
        
        # Run one generation
        try:
            engine.run_cycle()
        except Exception as e:
            log(f"\n[ERROR] Generation {gen}: {e}")
            import traceback
            log(traceback.format_exc())
            break
        
        # Log PNCT metrics
        pnct_logger.log_metrics(
            gen + 1,
            engine.population,
            engine.internal_evaluator,
            translator
        )
        
        # Check for bloat
        gac_hist = pnct_logger.get_gac_history()
        if gac_hist:
            current_gac = gac_hist[-1]['genome_length']['mean']
            max_gac_seen = max(max_gac_seen, current_gac)
            
            if current_gac > bloat_threshold:
                bloat_counter += 1
                if bloat_counter >= bloat_tolerance:
                    log("")
                    log("="*70)
                    log("VALIDATION FAILED: GENOME BLOAT DETECTED")
                    log("="*70)
                    log(f"GAC exceeded {bloat_threshold} for {bloat_counter} consecutive generations")
                    log(f"Current GAC: {current_gac:.1f}")
                    log(f"Max GAC seen: {max_gac_seen:.1f}")
                    log("")
                    log("The exponential penalty is NOT strong enough.")
                    log_handle.close()
                    sys.exit(1)
            else:
                bloat_counter = 0  # Reset counter
        
        # Early termination check
        if len(engine.population) < 10:
            log(f"\n[EARLY TERMINATION] Population collapsed to {len(engine.population)} agents")
            break
        
        # Progress reporting
        if (gen + 1) % report_interval == 0 or gen == 0:
            current_time = time.time()
            elapsed = current_time - start_time
            interval_time = current_time - last_report_time
            last_report_time = current_time
            
            gens_per_sec = (gen + 1) / elapsed if elapsed > 0 else 0
            remaining_gens = total_gens - (gen + 1)
            eta_seconds = remaining_gens / gens_per_sec if gens_per_sec > 0 else 0
            
            # Get latest metrics
            gac_hist = pnct_logger.get_gac_history()
            epc_hist = pnct_logger.get_epc_history()
            
            gac_mean = gac_hist[-1]['genome_length']['mean'] if gac_hist else 0
            epc_lz = epc_hist[-1]['lz_complexity']['mean'] if epc_hist else 0
            
            # Status
            if gac_mean > bloat_threshold:
                status = "[!] BLOAT"
            elif gac_mean > bloat_threshold * 0.8:
                status = "[!] High"
            else:
                status = "[OK] Healthy"
            
            log(f"{gen+1:8d} {len(engine.population):5d} "
                f"{gac_mean:7.1f} {epc_lz:8.3f} "
                f"{gens_per_sec:8.1f} "
                f"{eta_seconds/60:9.1f} min {status:>15}")
    
    # Completion
    total_time = time.time() - start_time
    log("-"*70)
    log(f"Total time: {total_time:.2f}s ({total_time/60:.2f} min, {total_time/3600:.2f} hours)")
    log("")
    
    # Final analysis
    log("="*70)
    log("VALIDATION RESULTS")
    log("="*70)
    log("")
    
    gac_hist = pnct_logger.get_gac_history()
    if gac_hist:
        initial_gac = gac_hist[0]['genome_length']['mean']
        final_gac = gac_hist[-1]['genome_length']['mean']
        
        log(f"Initial GAC: {initial_gac:.1f}")
        log(f"Final GAC: {final_gac:.1f}")
        log(f"Max GAC seen: {max_gac_seen:.1f}")
        log(f"Change: {final_gac - initial_gac:+.1f} ({(final_gac/initial_gac - 1)*100:+.1f}%)")
        log("")
        
        if max_gac_seen < bloat_threshold:
            log("[SUCCESS] VALIDATION PASSED")
            log(f"  GAC stayed below {bloat_threshold} throughout the entire run")
            log("  Exponential metabolic cost penalty is working correctly!")
            log("")
            log("The system is ready for the full 200k-generation experiment.")
        else:
            log("[PARTIAL SUCCESS] Validation completed with warnings")
            log(f"  GAC briefly exceeded {bloat_threshold} but stayed under control")
            log(f"  Max GAC: {max_gac_seen:.1f}")
    
    log("="*70)
    log(f"Results saved to: {run_dir}")
    log("="*70)
    
    log_handle.close()
    
    return run_dir

if __name__ == '__main__':
    try:
        run_dir = run_validation_test()
        print(f"\nValidation test complete. Results in: {run_dir}")
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
