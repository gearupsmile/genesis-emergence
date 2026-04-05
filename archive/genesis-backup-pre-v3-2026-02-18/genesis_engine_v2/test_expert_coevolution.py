"""
Expert Co-Evolution Test - 1,000 Generation Definitive Validation

Expert mandate: "Co-evolutionary arms race is the ultimate stress test."
Target: Behavioral variance > 0.02 for sustained innovation.
"""

import sys
from pathlib import Path
import numpy as np
import time

sys.path.insert(0, str(Path(__file__).parent))

from engine.genesis_engine_minimal import GenesisEngineMinimal
from engine.carp.species import Species


def run_expert_coevolution_test():
    """
    Expert-prescribed test for open-ended evolution.
    
    PRIMARY METRIC: Behavioral variance > 0.02
    
    SUCCESS CRITERIA:
    1. PRIMARY: Behavioral variance > 0.02 for ≥3 consecutive 100-gen windows
    2. Stability: Both species survive at gen 1000 (>20 foragers, >10 predators)
    3. Law Integrity: Zero physics violations (100% compliance)
    4. Trait Evolution: Clear divergence in aggression (predators↑) vs exploration (foragers↑)
    5. No Simple Cycles: Capture rate shows irregular oscillations
    """
    print("=" * 70)
    print("EXPERT CO-EVOLUTION TEST: 1,000 GENERATIONS")
    print("=" * 70)
    print()
    print("Expert Hypothesis: Frequency-dependent selection generates sustained")
    print("behavioral diversity through co-evolutionary arms race.")
    print()
    print("Target: Behavioral variance > 0.02")
    print("=" * 70)
    print()
    
    # Initialize engine
    print("Initializing GenesisEngineMinimal (population=100)...")
    engine = GenesisEngineMinimal(population_size=100, forager_ratio=0.7, mutation_rate=0.3)
    print(f"  Initial population: {len(engine.population)}")
    print(f"  Forager ratio: {engine.forager_ratio}")
    print(f"  Mutation rate: {engine.mutation_rate}")
    print()
    
    # Metrics tracking
    metrics = {
        'generation': [],
        'behavioral_variance': [],  # PRIMARY METRIC
        'forager_count': [],
        'predator_count': [],
        'forager_aggression': [],
        'predator_aggression': [],
        'forager_exploration': [],
        'predator_exploration': [],
        'avg_genome_length': [],
        'capture_rate': [],
        'total_captures': []
    }
    
    print("Running 1,000 generations...")
    print()
    
    start_time = time.time()
    
    for gen in range(1000):
        engine.run_cycle()
        
        # Collect statistics
        stats = engine.get_statistics()
        
        metrics['generation'].append(stats['generation'])
        metrics['behavioral_variance'].append(stats['behavioral_variance'])
        metrics['forager_count'].append(stats['forager_count'])
        metrics['predator_count'].append(stats['predator_count'])
        metrics['forager_aggression'].append(stats['forager_aggression'])
        metrics['predator_aggression'].append(stats['predator_aggression'])
        metrics['forager_exploration'].append(stats['forager_exploration'])
        metrics['predator_exploration'].append(stats['predator_exploration'])
        metrics['avg_genome_length'].append(stats['avg_genome_length'])
        metrics['capture_rate'].append(stats['carp_stats']['capture_rate'])
        metrics['total_captures'].append(stats['carp_stats']['successful_captures'])
        
        # Report every 100 generations
        if (gen + 1) % 100 == 0:
            elapsed = time.time() - start_time
            print(f"Gen {gen+1} ({elapsed:.1f}s):")
            print(f"  Variance: {stats['behavioral_variance']:.6f}")
            print(f"  Population: {stats['population_size']} "
                  f"(F:{stats['forager_count']}, P:{stats['predator_count']})")
            print(f"  Aggression: F={stats['forager_aggression']:.3f}, "
                  f"P={stats['predator_aggression']:.3f}")
            print(f"  Exploration: F={stats['forager_exploration']:.3f}, "
                  f"P={stats['predator_exploration']:.3f}")
            print(f"  Captures: {stats['carp_stats']['successful_captures']} "
                  f"({stats['carp_stats']['capture_rate']:.1%})")
            print()
    
    total_time = time.time() - start_time
    
    print("=" * 70)
    print("TEST COMPLETE")
    print("=" * 70)
    print(f"Total time: {total_time:.1f} seconds")
    print()
    
    return metrics, engine


def analyze_results(metrics, engine):
    """Analyze results against expert success criteria."""
    print("=" * 70)
    print("EXPERT ANALYSIS")
    print("=" * 70)
    print()
    
    # CRITERION 1: Behavioral variance > 0.02 for ≥3 consecutive 100-gen windows
    print("CRITERION 1: Sustained Behavioral Variance")
    print("-" * 70)
    
    variance_windows = []
    for i in range(0, 1000, 100):
        window_variance = np.mean(metrics['behavioral_variance'][i:i+100])
        variance_windows.append(window_variance)
        status = '[PASS]' if window_variance > 0.02 else '[FAIL]'
        print(f"  Gen {i:4d}-{i+99:4d}: Variance = {window_variance:.6f} {status}")
    
    consecutive_high = 0
    max_consecutive = 0
    for v in variance_windows:
        if v > 0.02:
            consecutive_high += 1
            max_consecutive = max(max_consecutive, consecutive_high)
        else:
            consecutive_high = 0
    
    criterion1_pass = max_consecutive >= 3
    print(f"\n  Max consecutive high-variance windows: {max_consecutive}")
    print(f"  Result: {'[PASS]' if criterion1_pass else '[FAIL]'}")
    print()
    
    # CRITERION 2: Population stability
    print("CRITERION 2: Population Stability at Gen 1000")
    print("-" * 70)
    final_foragers = metrics['forager_count'][-1]
    final_predators = metrics['predator_count'][-1]
    print(f"  Foragers: {final_foragers} (target: >20)")
    print(f"  Predators: {final_predators} (target: >10)")
    
    criterion2_pass = final_foragers > 20 and final_predators > 10
    print(f"  Result: {'[PASS]' if criterion2_pass else '[FAIL]'}")
    print()
    
    # CRITERION 3: Physics law integrity
    print("CRITERION 3: Physics Law Integrity")
    print("-" * 70)
    violations = engine.physics_gatekeeper.total_violations
    total_checks = (engine.physics_gatekeeper.logger.total_parent_checks + 
                   engine.physics_gatekeeper.logger.total_offspring_checks)
    print(f"  Total checks: {total_checks}")
    print(f"  Violations: {violations}")
    
    criterion3_pass = violations == 0
    print(f"  Result: {'[PASS]' if criterion3_pass else '[FAIL]'}")
    print()
    
    # CRITERION 4: Trait divergence
    print("CRITERION 4: Trait Divergence (Predators vs Foragers)")
    print("-" * 70)
    
    # Final 100 generations average
    final_forager_agg = np.mean(metrics['forager_aggression'][-100:])
    final_predator_agg = np.mean(metrics['predator_aggression'][-100:])
    final_forager_exp = np.mean(metrics['forager_exploration'][-100:])
    final_predator_exp = np.mean(metrics['predator_exploration'][-100:])
    
    print(f"  Aggression (final 100 gens):")
    print(f"    Foragers: {final_forager_agg:.3f}")
    print(f"    Predators: {final_predator_agg:.3f}")
    print(f"    Divergence: {abs(final_predator_agg - final_forager_agg):.3f}")
    
    print(f"  Exploration (final 100 gens):")
    print(f"    Foragers: {final_forager_exp:.3f}")
    print(f"    Predators: {final_predator_exp:.3f}")
    print(f"    Divergence: {abs(final_forager_exp - final_predator_exp):.3f}")
    
    # Check for meaningful divergence (>0.05 difference)
    agg_divergence = abs(final_predator_agg - final_forager_agg)
    exp_divergence = abs(final_forager_exp - final_predator_exp)
    criterion4_pass = agg_divergence > 0.05 or exp_divergence > 0.05
    
    print(f"  Result: {'[PASS]' if criterion4_pass else '[FAIL]'}")
    print()
    
    # CRITERION 5: No simple cycles
    print("CRITERION 5: Irregular Dynamics (No Simple Cycles)")
    print("-" * 70)
    
    # Check capture rate variance (high variance = irregular)
    capture_rate_variance = np.var(metrics['capture_rate'])
    print(f"  Capture rate variance: {capture_rate_variance:.6f}")
    print(f"  (High variance indicates irregular dynamics)")
    
    criterion5_pass = capture_rate_variance > 0.001  # Threshold for irregularity
    print(f"  Result: {'[PASS]' if criterion5_pass else '[FAIL]'}")
    print()
    
    # OVERALL VERDICT
    print("=" * 70)
    print("EXPERT VERDICT")
    print("=" * 70)
    print()
    
    all_pass = all([criterion1_pass, criterion2_pass, criterion3_pass, 
                   criterion4_pass, criterion5_pass])
    
    if all_pass:
        print("[SUCCESS] ALL CRITERIA PASSED")
        print()
        print("CONCLUSION: Data supports 'sustained open-ended innovation'")
        print("through frequency-dependent selection in co-evolutionary arms race.")
        print()
        print("RECOMMENDATION: Proceed to Phase 7 (Ablation Studies)")
    else:
        print("[FAILURE] SOME CRITERIA FAILED")
        print()
        print("CONCLUSION: System shows 'bounded equilibrium' rather than")
        print("sustained innovation. Behavioral diversity limited.")
        print()
        print("RECOMMENDATION: Architecture redesign per expert framework")
    
    print()
    print("=" * 70)
    
    return {
        'criterion1_sustained_variance': criterion1_pass,
        'criterion2_population_stability': criterion2_pass,
        'criterion3_physics_integrity': criterion3_pass,
        'criterion4_trait_divergence': criterion4_pass,
        'criterion5_irregular_dynamics': criterion5_pass,
        'overall_pass': all_pass,
        'final_variance': metrics['behavioral_variance'][-1],
        'max_consecutive_high_variance_windows': max_consecutive
    }


if __name__ == '__main__':
    try:
        # Run test
        metrics, engine = run_expert_coevolution_test()
        
        # Analyze results
        results = analyze_results(metrics, engine)
        
        # Save metrics for plotting
        import json
        with open('expert_coevolution_metrics.json', 'w') as f:
            # Convert numpy types to Python types for JSON
            metrics_json = {k: [float(v) if isinstance(v, (np.floating, np.integer)) else v 
                               for v in vals] 
                           for k, vals in metrics.items()}
            json.dump(metrics_json, f, indent=2)
        
        print(f"\nMetrics saved to: expert_coevolution_metrics.json")
        
        sys.exit(0 if results['overall_pass'] else 1)
        
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
