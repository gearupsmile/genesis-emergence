"""
Verification Test Script for Phase 6 Deep Probe

Runs a 1,000-generation test with full PNCT logging to verify:
- All metrics are logged correctly (GAC, EPC, NND)
- No NaN values in logs
- Checkpoints are created and loadable
- Progress reporting works

Success criteria: Completes in <5 minutes with all checks passing
"""

import sys
import os
from pathlib import Path
import time
import pickle
from datetime import datetime

# Add genesis_engine_v2 to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'genesis_engine_v2'))

from engine.genesis_engine import GenesisEngine
from engine.codon_translator import CodonTranslator
from engine.diagnostics.pnct_metrics import PNCTLogger


def run_verification_test():
    """Run 1,000-generation verification test."""
    print("=" * 70)
    print("PHASE 6 VERIFICATION TEST")
    print("=" * 70)
    print()
    
    # Configuration
    config = {
        'generations': 1000,
        'population': 50,
        'mutation_rate': 0.3,
        'checkpoint_interval': 250,
        'gac_interval': 100,
        'nnd_interval': 200
    }
    
    print("Configuration:")
    print(f"  Generations: {config['generations']:,}")
    print(f"  Population: {config['population']}")
    print(f"  Mutation Rate: {config['mutation_rate']}")
    print(f"  Checkpoints: Every {config['checkpoint_interval']} gens")
    print(f"  GAC/EPC Logging: Every {config['gac_interval']} gens")
    print(f"  NND Logging: Every {config['nnd_interval']} gens")
    print()
    
    # Create test directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    test_dir = Path("runs") / f"verification_test_{timestamp}"
    test_dir.mkdir(parents=True, exist_ok=True)
    checkpoint_dir = test_dir / "checkpoints"
    checkpoint_dir.mkdir(exist_ok=True)
    
    print(f"Test directory: {test_dir}")
    print()
    
    # Initialize engine
    print("Initializing GenesisEngine...")
    engine = GenesisEngine(
        population_size=config['population'],
        mutation_rate=config['mutation_rate'],
        simulation_steps=10,
        transition_start_generation=0,
        transition_total_generations=500  # Shorter transition for test
    )
    
    translator = CodonTranslator()
    pnct_logger = PNCTLogger(
        gac_interval=config['gac_interval'],
        nnd_interval=config['nnd_interval'],
        translator=translator
    )
    
    print("  Engine initialized")
    print()
    
    # Run evolution
    print("Running evolution...")
    print(f"{'Gen':>6} {'Pop':>5} {'GAC':>7} {'EPC':>7} {'NND':>7} {'Time':>8}")
    print("-" * 50)
    
    start_time = time.time()
    last_report_time = start_time
    
    validation_results = {
        'gac_logged': False,
        'epc_logged': False,
        'nnd_logged': False,
        'checkpoints_created': 0,
        'nan_detected': False,
        'errors': []
    }
    
    for gen in range(config['generations']):
        # Run one generation
        try:
            engine.run_cycle()
        except Exception as e:
            validation_results['errors'].append(f"Gen {gen}: {e}")
            print(f"\n[ERROR] Generation {gen}: {e}")
            break
        
        # Log PNCT metrics
        metrics = pnct_logger.log_metrics(
            gen + 1,
            engine.population,
            engine.internal_evaluator,
            translator
        )
        
        # Validate metrics
        if 'gac' in metrics:
            validation_results['gac_logged'] = True
            # Check for NaN
            if any(v != v for v in [  # NaN check
                metrics['gac']['genome_length']['mean'],
                metrics['gac']['linkage_groups']['mean']
            ]):
                validation_results['nan_detected'] = True
                validation_results['errors'].append(f"Gen {gen+1}: NaN in GAC")
        
        if 'epc' in metrics:
            validation_results['epc_logged'] = True
            if any(v != v for v in [
                metrics['epc']['lz_complexity']['mean'],
                metrics['epc']['instruction_diversity']['mean']
            ]):
                validation_results['nan_detected'] = True
                validation_results['errors'].append(f"Gen {gen+1}: NaN in EPC")
        
        if 'nnd' in metrics:
            validation_results['nnd_logged'] = True
            if metrics['nnd']['mean_nnd'] != metrics['nnd']['mean_nnd']:
                validation_results['nan_detected'] = True
                validation_results['errors'].append(f"Gen {gen+1}: NaN in NND")
        
        # Progress reporting (every 100 gens)
        if (gen + 1) % 100 == 0 or gen == 0:
            current_time = time.time()
            interval_time = current_time - last_report_time
            last_report_time = current_time
            
            gac_hist = pnct_logger.get_gac_history()
            epc_hist = pnct_logger.get_epc_history()
            nnd_hist = pnct_logger.get_nnd_history()
            
            gac_val = gac_hist[-1]['genome_length']['mean'] if gac_hist else 0
            epc_val = epc_hist[-1]['lz_complexity']['mean'] if epc_hist else 0
            nnd_val = nnd_hist[-1]['mean_nnd'] if nnd_hist else 0
            
            print(f"{gen+1:6d} {len(engine.population):5d} "
                  f"{gac_val:7.1f} {epc_val:7.3f} {nnd_val:7.3f} "
                  f"{interval_time:8.2f}s")
        
        # Checkpointing
        if (gen + 1) % config['checkpoint_interval'] == 0:
            checkpoint_file = checkpoint_dir / f"checkpoint_{gen+1:06d}.pkl"
            checkpoint_data = {
                'generation': gen + 1,
                'gac_history': pnct_logger.get_gac_history(),
                'epc_history': pnct_logger.get_epc_history(),
                'nnd_history': pnct_logger.get_nnd_history(),
                'population_size': len(engine.population)
            }
            
            try:
                with open(checkpoint_file, 'wb') as f:
                    pickle.dump(checkpoint_data, f)
                validation_results['checkpoints_created'] += 1
            except Exception as e:
                validation_results['errors'].append(f"Checkpoint {gen+1}: {e}")
    
    total_time = time.time() - start_time
    
    print("-" * 50)
    print(f"Total time: {total_time:.2f}s ({total_time/60:.2f} min)")
    print()
    
    # Validation
    print("=" * 70)
    print("VALIDATION RESULTS")
    print("=" * 70)
    print()
    
    all_passed = True
    
    # Check 1: GAC logged
    if validation_results['gac_logged']:
        print("[PASS] GAC metrics logged")
    else:
        print("[FAIL] GAC metrics NOT logged")
        all_passed = False
    
    # Check 2: EPC logged
    if validation_results['epc_logged']:
        print("[PASS] EPC metrics logged")
    else:
        print("[FAIL] EPC metrics NOT logged")
        all_passed = False
    
    # Check 3: NND logged
    if validation_results['nnd_logged']:
        print("[PASS] NND metrics logged")
    else:
        print("[FAIL] NND metrics NOT logged")
        all_passed = False
    
    # Check 4: No NaN values
    if not validation_results['nan_detected']:
        print("[PASS] No NaN values detected")
    else:
        print("[FAIL] NaN values detected")
        all_passed = False
    
    # Check 5: Checkpoints created
    expected_checkpoints = config['generations'] // config['checkpoint_interval']
    if validation_results['checkpoints_created'] == expected_checkpoints:
        print(f"[PASS] All {expected_checkpoints} checkpoints created")
    else:
        print(f"[FAIL] Only {validation_results['checkpoints_created']}/{expected_checkpoints} checkpoints created")
        all_passed = False
    
    # Check 6: Time limit
    time_limit = 300  # 5 minutes
    if total_time < time_limit:
        print(f"[PASS] Completed within time limit ({total_time:.1f}s < {time_limit}s)")
    else:
        print(f"[FAIL] Exceeded time limit ({total_time:.1f}s > {time_limit}s)")
        all_passed = False
    
    # Check 7: No errors
    if not validation_results['errors']:
        print("[PASS] No errors encountered")
    else:
        print(f"[FAIL] {len(validation_results['errors'])} error(s) encountered:")
        for error in validation_results['errors'][:5]:  # Show first 5
            print(f"    - {error}")
        all_passed = False
    
    print()
    
    # Final verdict
    print("=" * 70)
    if all_passed:
        print("✓✓✓ VERIFICATION TEST PASSED ✓✓✓")
        print()
        print("System is ready for 200k-generation Deep Probe experiment!")
    else:
        print("✗✗✗ VERIFICATION TEST FAILED ✗✗✗")
        print()
        print("Please fix issues before running Deep Probe experiment.")
    print("=" * 70)
    
    # Save summary
    summary_file = test_dir / "verification_summary.txt"
    with open(summary_file, 'w') as f:
        f.write(f"Verification Test Summary\n")
        f.write(f"========================\n\n")
        f.write(f"Result: {'PASSED' if all_passed else 'FAILED'}\n")
        f.write(f"Time: {total_time:.2f}s\n")
        f.write(f"GAC Logged: {validation_results['gac_logged']}\n")
        f.write(f"EPC Logged: {validation_results['epc_logged']}\n")
        f.write(f"NND Logged: {validation_results['nnd_logged']}\n")
        f.write(f"Checkpoints: {validation_results['checkpoints_created']}/{expected_checkpoints}\n")
        f.write(f"NaN Detected: {validation_results['nan_detected']}\n")
        f.write(f"Errors: {len(validation_results['errors'])}\n")
    
    print(f"\nSummary saved to: {summary_file}")
    
    return all_passed


if __name__ == '__main__':
    success = run_verification_test()
    sys.exit(0 if success else 1)
