"""
Diagnostic 10k Experiment Runner

Runs a 10,000-generation experiment with resource profiling to diagnose
system stability before the full 200k run.
"""

import sys
from pathlib import Path
import time

# Add genesis_engine_v2 to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'genesis_engine_v2'))

from engine.genesis_engine import GenesisEngine
from engine.codon_translator import CodonTranslator
from engine.diagnostics.pnct_metrics import PNCTLogger
from engine.diagnostics.resource_profiler import ResourceProfiler


def run_diagnostic():
    """Run 10k diagnostic experiment with resource profiling."""
    print("=" * 70)
    print("DIAGNOSTIC 10K EXPERIMENT")
    print("Resource Profiling to Diagnose System Stability")
    print("=" * 70)
    print()
    
    # Configuration
    total_gens = 10000
    population_size = 100  # Same as failed 200k run
    mutation_rate = 0.3
    checkpoint_interval = 2000
    memory_log_interval = 100
    
    print("Configuration:")
    print(f"  Generations: {total_gens:,}")
    print(f"  Population: {population_size}")
    print(f"  Checkpoints: Every {checkpoint_interval:,} gens")
    print(f"  Resource logging: Every {memory_log_interval} gens")
    print()
    
    # Create output directory
    run_dir = Path("runs") / "diagnostic_10k"
    run_dir.mkdir(parents=True, exist_ok=True)
    
    # Initialize profiler
    resource_log = run_dir / "resource_profile.log"
    profiler = ResourceProfiler(log_file=str(resource_log))
    
    print("Initializing engine...")
    engine = GenesisEngine(
        population_size=population_size,
        mutation_rate=mutation_rate,
        simulation_steps=10
    )
    
    translator = CodonTranslator()
    pnct_logger = PNCTLogger(
        gac_interval=500,
        nnd_interval=1000,
        translator=translator
    )
    
    print("  Engine initialized")
    print()
    
    # Run evolution
    print("Running evolution with resource monitoring...")
    print(f"{'Gen':>6} {'Pop':>5} {'GAC':>7} {'EPC':>7} {'Mem(MB)':>9} {'Time':>8}")
    print("-" * 65)
    
    start_time = time.time()
    last_report = start_time
    
    for gen in range(total_gens):
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
        
        # Progress reporting
        if (gen + 1) % 1000 == 0:
            current_time = time.time()
            interval_time = current_time - last_report
            last_report = current_time
            
            gac_hist = pnct_logger.get_gac_history()
            epc_hist = pnct_logger.get_epc_history()
            
            gac_mean = gac_hist[-1]['genome_length']['mean'] if gac_hist else 0
            epc_mean = epc_hist[-1]['lz_complexity']['mean'] if epc_hist else 0
            
            memory_mb = profiler.get_memory_mb()
            
            print(f"{gen+1:6d} {len(engine.population):5d} "
                  f"{gac_mean:7.1f} {epc_mean:7.3f} "
                  f"{memory_mb:9.1f} "
                  f"{interval_time:8.2f}s")
    
    total_time = time.time() - start_time
    gens_per_sec = total_gens / total_time
    
    print("-" * 70)
    print(f"Total time: {total_time:.2f}s ({gens_per_sec:.1f} gen/s)")
    print()
    
    # Generate and display report
    print("=" * 70)
    print("GENERATING RESOURCE PROFILE REPORT")
    print("=" * 70)
    print()
    
    profiler.save_report()
    report = profiler.generate_report()
    print(report)
    
    print(f"\nDetailed resource log saved to: {resource_log}")
    print()
    
    return profiler


if __name__ == '__main__':
    profiler = None
    try:
        profiler = run_diagnostic()
        
        # Exit code based on recommendation
        trend = profiler.calculate_memory_trend()
        peak_mb = profiler.get_peak_memory_mb()
        
        if trend['trend'] == 'flat' and peak_mb < 500:
            exit_code = 0  # Safe to proceed
        elif trend['growth_percent'] > 50:
            exit_code = 2  # Debug needed
        else:
            exit_code = 1  # Caution
        
        profiler.cleanup()
        sys.exit(exit_code)
            
    except Exception as e:
        print(f"\n[ERROR] Diagnostic failed: {e}")
        import traceback
        traceback.print_exc()
        if profiler:
            profiler.cleanup()
        sys.exit(3)
