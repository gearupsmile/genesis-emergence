"""
25k Physics V2 Validation Probe

Validates the Physical Invariant Architecture at the scale where
the previous exploit emerged (25,000 generations).

Core Question: "What does evolution look like when the law cannot be broken?"

Success Criteria:
- ZERO physics violations (hard requirement)
- GAC stabilizes below energy limit
- EPC shows non-decreasing trend
- Population remains stable

Phase 2 - Validation
"""

import sys
import os
from pathlib import Path
import time
import signal
import pickle
from datetime import datetime
import json

# Add genesis_engine_v2 to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'genesis_engine_v2'))

from engine.genesis_engine import GenesisEngine
from engine.codon_translator import CodonTranslator
from engine.diagnostics.pnct_metrics import PNCTLogger


# Global state
shutdown_requested = False


def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully."""
    global shutdown_requested
    print("\n\n[INTERRUPT] Graceful shutdown requested...")
    shutdown_requested = True


def save_checkpoint(engine, pnct_logger, run_dir, generation):
    """Save checkpoint with physics gatekeeper data."""
    checkpoint_file = run_dir / "checkpoints" / f"checkpoint_{generation:06d}.pkl"
    
    # Collect physics gatekeeper statistics
    physics_stats = engine.physics_gatekeeper.get_statistics() if hasattr(engine, 'physics_gatekeeper') else {}
    physics_violations = engine.physics_violations if hasattr(engine, 'physics_violations') else []
    
    checkpoint_data = {
        'generation': generation,
        'statistics': engine.statistics,
        'gac_history': pnct_logger.get_gac_history(),
        'epc_history': pnct_logger.get_epc_history(),
        'nnd_history': pnct_logger.get_nnd_history(),
        'population_size': len(engine.population),
        'transition_weight': engine.transition_weight,
        'timestamp': datetime.now().isoformat(),
        # NEW: Physics gatekeeper data
        'physics_stats': physics_stats,
        'physics_violations': physics_violations
    }
    
    with open(checkpoint_file, 'wb') as f:
        pickle.dump(checkpoint_data, f)
    
    print(f"  [CHECKPOINT] Saved: {checkpoint_file.name}")
    
    # Save violation log separately for easy access
    if physics_violations:
        violation_file = run_dir / "logs" / f"violations_{generation:06d}.json"
        with open(violation_file, 'w') as f:
            json.dump(physics_violations, f, indent=2)
        print(f"  [WARNING] {len(physics_violations)} violation events logged")


def run_25k_validation_probe():
    """Execute the 25,000-generation Physics V2 validation probe."""
    global shutdown_requested
    
    # Set up signal handler
    signal.signal(signal.SIGINT, signal_handler)
    
    print("=" * 70)
    print("25K PHYSICS V2 VALIDATION PROBE")
    print("=" * 70)
    print()
    print("Mission: Validate Physical Invariant Architecture at scale")
    print("Question: What does evolution look like when the law cannot be broken?")
    print()
    
    # Configuration
    total_gens = 25000
    population_size = 100
    mutation_rate = 0.3
    checkpoint_interval = 5000
    gac_interval = 500
    nnd_interval = 1000
    report_interval = 1000
    
    print("Configuration:")
    print(f"  Total generations: {total_gens:,}")
    print(f"  Population: {population_size}")
    print(f"  Mutation rate: {mutation_rate}")
    print(f"  Energy constant: 0.5 (hard limit)")
    print(f"  Checkpoints: Every {checkpoint_interval:,} gens")
    print(f"  PNCT logging: GAC/EPC every {gac_interval}, NND every {nnd_interval}")
    print()
    
    # Create experiment directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = Path("runs") / f"25k_physics_v2_validation_{timestamp}"
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "checkpoints").mkdir(exist_ok=True)
    (run_dir / "logs").mkdir(exist_ok=True)
    
    print(f"Experiment directory: {run_dir}")
    print()
    
    # Initialize engine (with physics gatekeeper automatically enabled)
    print("Initializing GenesisEngine with PhysicalInvariantGatekeeper...")
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
    print(f"  Physics Gatekeeper: {engine.physics_gatekeeper if hasattr(engine, 'physics_gatekeeper') else 'Will be created on first cycle'}")
    print()
    
    # Run evolution
    print("=" * 70)
    print("RUNNING EVOLUTION")
    print("=" * 70)
    print()
    print(f"{'Gen':<8} {'Pop':<5} {'GAC':<8} {'EPC_LZ':<8} {'MaxCost':<9} {'Viols':<7} {'Time':<10} {'Gen/s':<8}")
    print("-" * 70)
    
    start_time = time.time()
    last_report_time = start_time
    
    for gen in range(total_gens):
        if shutdown_requested:
            print("\n[SHUTDOWN] Saving final checkpoint...")
            save_checkpoint(engine, pnct_logger, run_dir, gen)
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
        if len(engine.population) < 5:
            print(f"\n[EARLY TERMINATION] Population collapsed to {len(engine.population)} agents")
            save_checkpoint(engine, pnct_logger, run_dir, gen + 1)
            return
        
        # Progress reporting
        if (gen + 1) % report_interval == 0 or gen == 0:
            current_time = time.time()
            elapsed = current_time - start_time
            interval_time = current_time - last_report_time
            last_report_time = current_time
            
            gens_per_sec = (gen + 1) / elapsed if elapsed > 0 else 0
            
            # Get latest metrics
            gac_hist = pnct_logger.get_gac_history()
            epc_hist = pnct_logger.get_epc_history()
            
            gac_mean = gac_hist[-1]['genome_length']['mean'] if gac_hist else 0
            epc_lz = epc_hist[-1]['lz_complexity']['mean'] if epc_hist else 0
            
            # Get physics stats
            max_cost = max(agent.genome.metabolic_cost for agent in engine.population) if engine.population else 0
            total_viols = len(engine.physics_violations) if hasattr(engine, 'physics_violations') else 0
            
            print(f"{gen+1:<8d} {len(engine.population):<5d} "
                  f"{gac_mean:<8.1f} {epc_lz:<8.3f} {max_cost:<9.3f} "
                  f"{total_viols:<7d} {interval_time:<10.2f}s {gens_per_sec:<8.1f}")
        
        # Checkpointing
        if (gen + 1) % checkpoint_interval == 0:
            save_checkpoint(engine, pnct_logger, run_dir, gen + 1)
    
    # Completion
    total_time = time.time() - start_time
    print("-" * 70)
    print(f"Total time: {total_time:.2f}s ({total_time/60:.2f} min, {total_time/3600:.2f} hours)")
    print()
    
    # Save final data
    print("Saving final data...")
    save_checkpoint(engine, pnct_logger, run_dir, total_gens)
    
    # Generate validation report
    print()
    print("=" * 70)
    print("VALIDATION REPORT")
    print("=" * 70)
    print()
    
    # Physics Invariant Validation
    physics_stats = engine.physics_gatekeeper.get_statistics()
    total_violations = physics_stats['total_violations']
    
    print("1. PHYSICS INVARIANT ENFORCEMENT")
    print("-" * 70)
    print(f"   Total viability checks: {physics_stats['total_checks']:,}")
    print(f"   Total violations: {total_violations}")
    print(f"   Violation rate: {physics_stats['violation_rate']:.4%}")
    
    if total_violations == 0:
        print("   [SUCCESS] ZERO violations - Physical invariant holds!")
    else:
        print(f"   [CRITICAL FAILURE] {total_violations} violations detected!")
        print("   The physical invariant was breached. Investigate violation logs.")
    print()
    
    # GAC Analysis
    gac_hist = pnct_logger.get_gac_history()
    if gac_hist:
        gac_values = [h['genome_length']['mean'] for h in gac_hist]
        final_gac = gac_values[-1]
        max_gac = max(gac_values)
        
        print("2. GENOME ARCHITECTURE COMPLEXITY (GAC)")
        print("-" * 70)
        print(f"   Initial GAC: {gac_values[0]:.1f}")
        print(f"   Final GAC: {final_gac:.1f}")
        print(f"   Maximum GAC: {max_gac:.1f}")
        print(f"   Energy constant limit: {engine.physics_gatekeeper.energy_constant}")
        
        # Calculate equivalent genome length for energy constant
        # cost = 0.005 * (length ^ 1.5)
        # 0.5 = 0.005 * (length ^ 1.5)
        # length = (0.5 / 0.005) ^ (1/1.5) ≈ 46.4
        max_viable_length = (engine.physics_gatekeeper.energy_constant / 0.005) ** (1/1.5)
        print(f"   Max viable genome length: ~{max_viable_length:.1f} genes")
        
        if final_gac < max_viable_length * 0.8:
            print(f"   [SUCCESS] GAC well below limit ({final_gac:.1f} < {max_viable_length:.1f})")
        else:
            print(f"   [WARNING] GAC approaching limit ({final_gac:.1f} / {max_viable_length:.1f})")
        print()
    
    # EPC Analysis
    epc_hist = pnct_logger.get_epc_history()
    if epc_hist:
        epc_values = [h['lz_complexity']['mean'] for h in epc_hist]
        
        print("3. EXPRESSED PHENOTYPIC COMPLEXITY (EPC)")
        print("-" * 70)
        print(f"   Initial EPC: {epc_values[0]:.3f}")
        print(f"   Final EPC: {epc_values[-1]:.3f}")
        print(f"   Change: {epc_values[-1] - epc_values[0]:+.3f}")
        
        if epc_values[-1] >= epc_values[0]:
            print("   [SUCCESS] EPC maintained or increased")
        else:
            print("   [WARNING] EPC decreased (possible stagnation)")
        print()
    
    # Population Stability
    print("4. POPULATION STABILITY")
    print("-" * 70)
    print(f"   Final population: {len(engine.population)} agents")
    
    if len(engine.population) >= 50:
        print("   [SUCCESS] Population stable")
    elif len(engine.population) >= 20:
        print("   [WARNING] Population reduced but viable")
    else:
        print("   [CRITICAL] Population critically low")
    print()
    
    print("=" * 70)
    print("EXPERIMENT COMPLETE")
    print("=" * 70)
    print(f"\nResults saved to: {run_dir}")
    print()
    
    # Return success/failure based on hard requirement
    return total_violations == 0


if __name__ == '__main__':
    try:
        success = run_25k_validation_probe()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
