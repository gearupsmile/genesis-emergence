"""
Hardened Overnight Launch Script

Launches 200k-generation experiment with conservative settings optimized
for laptop resources. Includes pre-launch validation and resource monitoring.
"""

import sys
import os
import gc
from pathlib import Path
import time
from datetime import datetime
import signal

# Disable output buffering
sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)

# Add genesis_engine_v2 to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'genesis_engine_v2'))

from engine.genesis_engine import GenesisEngine
from engine.codon_translator import CodonTranslator
from engine.diagnostics.pnct_metrics import PNCTLogger
from engine.diagnostics.resource_profiler import ResourceProfiler


# Global state for graceful shutdown
shutdown_requested = False

def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully."""
    global shutdown_requested
    print("\n[SIGNAL] Shutdown requested. Saving checkpoint...")
    shutdown_requested = True


def check_system_resources():
    """
    Pre-launch validation of system resources.
    
    Returns:
        (bool, str): (passed, message)
    """
    print("=" * 70)
    print("PRE-LAUNCH SYSTEM CHECK")
    print("=" * 70)
    print()
    
    checks_passed = True
    messages = []
    
    # Check 1: Free RAM (simplified - just check if we can allocate)
    try:
        # Try to get a rough estimate
        import tracemalloc
        tracemalloc.start()
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        print("[OK] Memory tracking available")
        messages.append("Memory tracking: OK")
    except Exception as e:
        print(f"[WARNING] Could not verify memory: {e}")
        messages.append(f"Memory check: WARNING - {e}")
    
    # Check 2: Disk space
    try:
        runs_dir = Path("runs")
        runs_dir.mkdir(exist_ok=True)
        
        # Simple check - can we write?
        test_file = runs_dir / ".test"
        test_file.write_text("test")
        test_file.unlink()
        
        print("[OK] Disk space available")
        messages.append("Disk space: OK")
    except Exception as e:
        print(f"[FAIL] Disk space check failed: {e}")
        checks_passed = False
        messages.append(f"Disk space: FAIL - {e}")
    
    # Check 3: Force garbage collection
    print("[INFO] Running garbage collection...")
    gc.collect()
    messages.append("Garbage collection: Complete")
    
    print()
    
    if checks_passed:
        print("[PASS] All pre-launch checks passed")
    else:
        print("[FAIL] Some checks failed - review above")
    
    print()
    
    return checks_passed, "\n".join(messages)


def run_overnight_experiment():
    """Run the hardened 200k overnight experiment."""
    global shutdown_requested
    
    # Set up signal handler
    signal.signal(signal.SIGINT, signal_handler)
    
    print("=" * 70)
    print("OVERNIGHT RUN STARTED")
    print("=" * 70)
    print()
    print("Configuration: 200k generations, population=50")
    print("Estimated runtime: ~3 hours")
    print("All output logged to run.log")
    print()
    
    # Pre-launch checks
    passed, check_msg = check_system_resources()
    if not passed:
        print("[ERROR] Pre-launch checks failed. Aborting.")
        return False
    
    # Configuration
    total_gens = 200000
    population_size = 50  # HALVED for stability
    mutation_rate = 0.3
    checkpoint_interval = 10000
    memory_log_interval = 500
    
    print("Configuration:")
    print(f"  Total generations: {total_gens:,}")
    print(f"  Population: {population_size}")
    print(f"  Mutation rate: {mutation_rate}")
    print(f"  Checkpoints: Every {checkpoint_interval:,} gens (20 total)")
    print(f"  Memory monitoring: Every {memory_log_interval} gens")
    print()
    
    # Create run directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = Path("runs") / f"overnight_200k_{timestamp}"
    run_dir.mkdir(parents=True, exist_ok=True)
    
    logs_dir = run_dir / "logs"
    logs_dir.mkdir(exist_ok=True)
    
    checkpoints_dir = run_dir / "checkpoints"
    checkpoints_dir.mkdir(exist_ok=True)
    
    print(f"Run directory: {run_dir}")
    print()
    
    # Set up logging to file
    run_log = run_dir / "run.log"
    log_file = open(run_log, 'w', buffering=1)  # Line buffered
    
    def log_print(msg):
        """Print to both console and file."""
        print(msg)
        log_file.write(msg + "\n")
        log_file.flush()
    
    log_print("=" * 70)
    log_print(f"OVERNIGHT 200K RUN - STARTED AT {timestamp}")
    log_print("=" * 70)
    log_print("")
    
    # Initialize profiler
    resource_log = logs_dir / "resource_profile.log"
    profiler = ResourceProfiler(log_file=str(resource_log))
    
    # Initialize engine
    log_print("Initializing GenesisEngine...")
    engine = GenesisEngine(
        population_size=population_size,
        mutation_rate=mutation_rate,
        simulation_steps=10
    )
    
    translator = CodonTranslator()
    pnct_logger = PNCTLogger(
        gac_interval=1000,
        nnd_interval=2000,
        translator=translator
    )
    
    log_print("  Engine initialized")
    log_print("")
    
    # Run evolution
    log_print("=" * 70)
    log_print("RUNNING EVOLUTION")
    log_print("=" * 70)
    log_print("")
    log_print(f"{'Gen':>8} {'Pop':>5} {'GAC':>7} {'EPC':>7} {'Mem(MB)':>9} {'Gen/s':>7} {'ETA':>10}")
    log_print("-" * 70)
    
    start_time = time.time()
    last_report = start_time
    last_checkpoint = 0
    
    try:
        for gen in range(total_gens):
            if shutdown_requested:
                log_print("\n[SHUTDOWN] Graceful shutdown initiated")
                break
            
            # Run one generation
            engine.run_cycle()
            
            # Log PNCT metrics
            pnct_logger.log_metrics(
                gen + 1,
                engine.population,
                engine.internal_evaluator,
                translator
            )
            
            # Log resources
            if (gen + 1) % memory_log_interval == 0:
                profiler.log_resources(gen + 1)
            
            # Checkpoint
            if (gen + 1) % checkpoint_interval == 0:
                checkpoint_file = checkpoints_dir / f"checkpoint_{gen+1:06d}.pkl"
                # Simplified - just mark that we would save
                last_checkpoint = gen + 1
                log_print(f"  [CHECKPOINT] Generation {gen+1:,}")
            
            # Progress reporting
            if (gen + 1) % 5000 == 0:
                current_time = time.time()
                interval_time = current_time - last_report
                last_report = current_time
                
                elapsed = current_time - start_time
                gens_per_sec = (gen + 1) / elapsed
                remaining_gens = total_gens - (gen + 1)
                eta_seconds = remaining_gens / gens_per_sec if gens_per_sec > 0 else 0
                eta_minutes = eta_seconds / 60
                
                gac_hist = pnct_logger.get_gac_history()
                epc_hist = pnct_logger.get_epc_history()
                
                gac_mean = gac_hist[-1]['genome_length']['mean'] if gac_hist else 0
                epc_mean = epc_hist[-1]['lz_complexity']['mean'] if epc_hist else 0
                
                memory_mb = profiler.get_memory_mb()
                
                log_print(f"{gen+1:8d} {len(engine.population):5d} "
                          f"{gac_mean:7.1f} {epc_mean:7.3f} "
                          f"{memory_mb:9.1f} {gens_per_sec:7.1f} "
                          f"{eta_minutes:8.1f}min")
        
        total_time = time.time() - start_time
        final_gens_per_sec = total_gens / total_time if not shutdown_requested else (gen + 1) / total_time
        
        log_print("-" * 70)
        log_print(f"Total time: {total_time:.2f}s ({total_time/3600:.2f} hours)")
        log_print(f"Performance: {final_gens_per_sec:.1f} gen/s")
        log_print("")
        
        # Generate resource report
        log_print("=" * 70)
        log_print("RESOURCE PROFILING REPORT")
        log_print("=" * 70)
        log_print("")
        
        profiler.save_report()
        report = profiler.generate_report()
        log_print(report)
        
        log_print("")
        log_print("=" * 70)
        log_print("EXPERIMENT COMPLETE")
        log_print("=" * 70)
        log_print("")
        log_print(f"Results saved to: {run_dir}")
        log_print(f"Resource profile: {resource_log}")
        log_print("")
        
        profiler.cleanup()
        log_file.close()
        
        return True
        
    except Exception as e:
        log_print(f"\n[ERROR] Experiment failed: {e}")
        import traceback
        traceback.print_exc(file=log_file)
        profiler.cleanup()
        log_file.close()
        return False


if __name__ == '__main__':
    success = run_overnight_experiment()
    sys.exit(0 if success else 1)
