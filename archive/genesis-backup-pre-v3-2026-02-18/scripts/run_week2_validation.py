"""
Week 2 Validation Experiment

Implements the complete ADM validation protocol:
1. Baseline run (5,000 gens) with ADM in recording mode
2. Crisis simulation (80% removal)
3. ADM recovery run (500 gens)
4. Control recovery run (500 gens)
5. Comparison and analysis

Week 2 - Decoupled Validation
"""

import sys
from pathlib import Path
import time
import pickle

# Add genesis_engine_v2 to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'genesis_engine_v2'))

from engine.genesis_engine import GenesisEngine
from engine.codon_translator import CodonTranslator
from engine.diversity.active_diversity_manager import ActiveDiversityManager
from engine.diversity.crisis_simulator import (
    simulate_crisis, repopulate_from_archive, repopulate_from_random,
    save_pre_crisis_snapshot, restore_pre_crisis_snapshot
)
from engine.diversity.recovery_metrics import (
    calculate_energy_efficiency, track_recovery_trajectory,
    compare_recovery_rates, calculate_archive_distinctness
)


def run_baseline_with_adm(generations=5000):
    """
    Phase 1: Run baseline with ADM in recording mode.
    
    Returns:
        Tuple of (engine, adm, pre_crisis_baseline)
    """
    print("=" * 70)
    print("PHASE 1: BASELINE RUN WITH ADM")
    print("=" * 70)
    print()
    
    # Initialize
    engine = GenesisEngine(
        population_size=100,
        mutation_rate=0.3,
        simulation_steps=10
    )
    
    adm = ActiveDiversityManager(
        archive_size=50,
        n_clusters=10,
        update_interval=100
    )
    
    translator = CodonTranslator()
    
    print(f"Running {generations} generations with ADM recording...")
    print(f"  Population: {engine.population_size}")
    print(f"  ADM archive capacity: {adm.archive_size}")
    print(f"  Clusters: {adm.n_clusters}")
    print()
    
    start_time = time.time()
    
    for gen in range(generations):
        # Run generation
        engine.run_cycle()
        
        # Update ADM clusters
        adm.update_clusters(engine.population, translator)
        
        # Archive agents (sample 10 per generation to avoid overhead)
        for agent in engine.population[::10]:  # Every 10th agent
            adm.archive_agent(agent, translator)
        
        # Progress reporting
        if (gen + 1) % 1000 == 0:
            elapsed = time.time() - start_time
            gen_per_sec = (gen + 1) / elapsed
            composition = adm.get_archive_composition()
            print(f"  Gen {gen+1}/{generations}: "
                  f"Archive={composition['size']}/{adm.archive_size}, "
                  f"Clusters={len(composition['cluster_distribution'])}, "
                  f"Diversity={composition['signature_variance']:.3f}, "
                  f"{gen_per_sec:.1f} gen/s")
    
    total_time = time.time() - start_time
    print(f"\nBaseline complete: {total_time:.1f}s ({generations/total_time:.1f} gen/s)")
    
    # Calculate pre-crisis baseline
    pre_crisis_baseline = {
        'avg_energy_efficiency': calculate_energy_efficiency(engine.population),
        'population_size': len(engine.population),
        'generation': engine.generation
    }
    
    print(f"\nPre-crisis baseline:")
    print(f"  Energy efficiency: {pre_crisis_baseline['avg_energy_efficiency']:.3f}")
    print(f"  Population: {pre_crisis_baseline['population_size']}")
    
    # Show archive composition
    composition = adm.get_archive_composition()
    print(f"\nADM Archive composition:")
    print(f"  Size: {composition['size']}")
    print(f"  Clusters represented: {len(composition['cluster_distribution'])}")
    print(f"  Avg priority: {composition['avg_priority']:.3f}")
    print(f"  Signature variance: {composition['signature_variance']:.3f}")
    
    return engine, adm, pre_crisis_baseline, translator


def run_adm_recovery(engine, adm, pre_crisis_baseline, translator, recovery_gens=500):
    """
    Phase 2: ADM recovery run.
    
    Returns:
        Recovery trajectory
    """
    print("\n" + "=" * 70)
    print("PHASE 2: ADM RECOVERY RUN")
    print("=" * 70)
    print()
    
    # Apply crisis
    removed_agents, crisis_state = simulate_crisis(engine, removal_rate=0.8, seed=42)
    
    # Repopulate from ADM archive
    repopulate_from_archive(engine, adm, mutation_rate=0.05)
    
    # Track recovery
    print(f"\nTracking recovery for {recovery_gens} generations...")
    trajectory = track_recovery_trajectory(engine, pre_crisis_baseline, max_gens=recovery_gens, translator=translator)
    
    return trajectory, removed_agents


def run_control_recovery(snapshot_file, removed_agents, pre_crisis_baseline, translator, recovery_gens=500):
    """
    Phase 3: Control recovery run.
    
    Returns:
        Recovery trajectory
    """
    print("\n" + "=" * 70)
    print("PHASE 3: CONTROL RECOVERY RUN")
    print("=" * 70)
    print()
    
    # Restore pre-crisis state
    engine = GenesisEngine(population_size=100, mutation_rate=0.3, simulation_steps=10)
    restore_pre_crisis_snapshot(engine, snapshot_file)
    
    # Apply identical crisis
    simulate_crisis(engine, removal_rate=0.8, seed=42)
    
    # Repopulate from random sample
    repopulate_from_random(engine, removed_agents, mutation_rate=0.05, seed=42)
    
    # Track recovery
    print(f"\nTracking recovery for {recovery_gens} generations...")
    trajectory = track_recovery_trajectory(engine, pre_crisis_baseline, max_gens=recovery_gens, translator=translator)
    
    return trajectory


def analyze_results(adm, removed_agents, adm_trajectory, control_trajectory, pre_crisis_baseline, translator):
    """
    Phase 4: Analysis and validation.
    
    Returns:
        Results dictionary
    """
    print("\n" + "=" * 70)
    print("PHASE 4: ANALYSIS & VALIDATION")
    print("=" * 70)
    print()
    
    # C1: Archive Distinctness
    print("C1: Archive Distinctness Test")
    print("-" * 70)
    
    # Create random sample from removed agents (same size as archive)
    import random
    random.seed(42)
    random_sample = random.sample(removed_agents, min(50, len(removed_agents)))
    
    distinctness = calculate_archive_distinctness(adm.archive, random_sample, translator)
    print(f"  Behavioral distance: {distinctness:.3f}")
    print(f"  Threshold: > 0.3")
    
    C1_pass = distinctness > 0.3
    print(f"  Result: {'PASS' if C1_pass else 'FAIL'}")
    print()
    
    # C2: Recovery Superiority
    print("C2: Recovery Superiority Test")
    print("-" * 70)
    
    comparison = compare_recovery_rates(
        adm_trajectory, 
        control_trajectory,
        pre_crisis_baseline['avg_energy_efficiency']
    )
    
    print(f"  ADM recovery time: {comparison['adm_recovery_time']} generations")
    print(f"  Control recovery time: {comparison['control_recovery_time']} generations")
    print(f"  Speedup: {comparison['speedup']:.2%}")
    print(f"  Threshold: ≥ 40%")
    
    C2_pass = comparison['speedup'] >= 0.4
    print(f"  Result: {'PASS' if C2_pass else 'FAIL'}")
    print()
    
    # C3: No Integration
    print("C3: No Integration Test")
    print("-" * 70)
    print("  Stagnation Detector: NOT IMPLEMENTED (as required)")
    C3_pass = True
    print(f"  Result: PASS")
    print()
    
    # Overall result
    print("=" * 70)
    print("OVERALL VALIDATION RESULT")
    print("=" * 70)
    
    all_pass = C1_pass and C2_pass and C3_pass
    print(f"  C1 (Archive Distinctness): {'PASS' if C1_pass else 'FAIL'}")
    print(f"  C2 (Recovery Superiority): {'PASS' if C2_pass else 'FAIL'}")
    print(f"  C3 (No Integration): {'PASS' if C3_pass else 'FAIL'}")
    print()
    print(f"  OVERALL: {'SUCCESS ✓' if all_pass else 'FAILURE ✗'}")
    print()
    
    return {
        'C1_distinctness': distinctness,
        'C1_pass': C1_pass,
        'C2_comparison': comparison,
        'C2_pass': C2_pass,
        'C3_pass': C3_pass,
        'overall_pass': all_pass
    }


def main():
    """Run complete Week 2 validation experiment."""
    print("=" * 70)
    print("WEEK 2 VALIDATION: ACTIVE DIVERSITY MANAGER")
    print("=" * 70)
    print()
    
    # Create output directory
    output_dir = Path("runs/week2_adm_validation")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Phase 1: Baseline
    engine, adm, pre_crisis_baseline, translator = run_baseline_with_adm(generations=5000)
    
    # Save pre-crisis snapshot
    snapshot_file = output_dir / "pre_crisis_snapshot.pkl"
    save_pre_crisis_snapshot(engine, str(snapshot_file))
    
    # Phase 2: ADM Recovery
    adm_trajectory, removed_agents = run_adm_recovery(engine, adm, pre_crisis_baseline, translator, recovery_gens=500)
    
    # Phase 3: Control Recovery
    control_trajectory = run_control_recovery(str(snapshot_file), removed_agents, pre_crisis_baseline, translator, recovery_gens=500)
    
    # Phase 4: Analysis
    results = analyze_results(adm, removed_agents, adm_trajectory, control_trajectory, pre_crisis_baseline, translator)
    
    # Save results
    results_file = output_dir / "validation_results.pkl"
    with open(results_file, 'wb') as f:
        pickle.dump({
            'adm_trajectory': adm_trajectory,
            'control_trajectory': control_trajectory,
            'pre_crisis_baseline': pre_crisis_baseline,
            'results': results,
            'adm_composition': adm.get_archive_composition()
        }, f)
    
    print(f"\nResults saved to: {output_dir}")
    
    return results['overall_pass']


if __name__ == '__main__':
    try:
        success = main()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n[ERROR] Experiment failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
