"""
Parameter Exploration Script

This script runs shorter experiments (2,000 generations) with different
parameter settings to find configurations that increase exploratory vigor
while maintaining system stability.

Parameters to explore:
1. Mutation Rate (mutation_rate)
2. AIS Forgetting Rate (forgetting_rate)
3. Transition Period (transition_total_generations)

Goal: Find gentle levers to increase exploration without breaking stability.
"""

import sys
from pathlib import Path
import time

sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'genesis_engine_v2'))

from engine.genesis_engine import GenesisEngine


def calculate_exploratory_vigor(statistics, start_gen=1000):
    """
    Calculate metrics that indicate exploratory behavior.
    
    Returns dict with:
    - metric_variance: Average variance across key metrics
    - novelty_events: Count of significant metric changes
    - exploration_score: Combined score
    """
    post_start = [s for s in statistics if s['generation'] >= start_gen]
    
    if len(post_start) < 100:
        return {'metric_variance': 0, 'novelty_events': 0, 'exploration_score': 0}
    
    # Extract metrics
    genome_lengths = [s['avg_genome_length'] for s in post_start]
    internal_scores = [s['avg_internal_score'] for s in post_start]
    linkage_groups = [s['avg_linkage_groups'] for s in post_start]
    
    # Calculate variances
    genome_var = sum((x - sum(genome_lengths)/len(genome_lengths))**2 for x in genome_lengths) / len(genome_lengths)
    internal_var = sum((x - sum(internal_scores)/len(internal_scores))**2 for x in internal_scores) / len(internal_scores)
    linkage_var = sum((x - sum(linkage_groups)/len(linkage_groups))**2 for x in linkage_groups) / len(linkage_groups)
    
    avg_variance = (genome_var + internal_var + linkage_var) / 3
    
    # Detect novelty events (significant jumps)
    novelty_count = 0
    
    # Check for genome length jumps
    for i in range(1, len(genome_lengths)):
        if abs(genome_lengths[i] - genome_lengths[i-1]) > 5:
            novelty_count += 1
    
    # Check for internal score spikes
    for i in range(1, len(internal_scores)):
        if abs(internal_scores[i] - internal_scores[i-1]) > 5:
            novelty_count += 1
    
    # Combined exploration score
    exploration_score = avg_variance * 0.7 + novelty_count * 0.3
    
    return {
        'metric_variance': avg_variance,
        'novelty_events': novelty_count,
        'exploration_score': exploration_score,
        'genome_var': genome_var,
        'internal_var': internal_var,
        'linkage_var': linkage_var
    }


def run_experiment(name, **kwargs):
    """Run a single 2000-generation experiment with given parameters."""
    print(f"\n{'='*60}")
    print(f"Experiment: {name}")
    print(f"{'='*60}")
    
    # Default parameters
    params = {
        'population_size': 100,
        'mutation_rate': 0.1,
        'simulation_steps': 10,
        'transition_start_generation': 0,
        'transition_total_generations': 1000  # Faster transition for experiments
    }
    
    # Override with experiment-specific params
    params.update(kwargs)
    
    print(f"Parameters:")
    for key, value in params.items():
        print(f"  {key}: {value}")
    print()
    
    # Initialize engine
    engine = GenesisEngine(**params)
    
    # Run evolution
    total_gens = 2000
    log_interval = 500
    
    print(f"Running {total_gens} generations...")
    start_time = time.time()
    
    for gen in range(total_gens):
        engine.run_cycle()
        
        if (gen + 1) % log_interval == 0:
            stats = engine.statistics[-1]
            print(f"  Gen {gen+1}: "
                  f"weight={stats['transition_weight']:.2f}, "
                  f"genome={stats['avg_genome_length']:.1f}, "
                  f"internal={stats['avg_internal_score']:.2f}")
    
    elapsed = time.time() - start_time
    print(f"Completed in {elapsed:.2f} seconds")
    
    # Analyze results
    vigor = calculate_exploratory_vigor(engine.statistics, start_gen=1000)
    
    # Get final stats
    final_stats = engine.statistics[-1]
    
    results = {
        'name': name,
        'params': params,
        'runtime': elapsed,
        'final_population': final_stats['population_size'],
        'final_genome_length': final_stats['avg_genome_length'],
        'final_internal_score': final_stats['avg_internal_score'],
        'vigor': vigor
    }
    
    return results


def print_results_summary(all_results):
    """Print comparison of all experiments."""
    output = []
    output.append("\n" + "="*70)
    output.append("EXPERIMENT COMPARISON")
    output.append("="*70)
    output.append("")
    
    # Table header
    output.append(f"{'Experiment':<25} {'Pop':>5} {'Genome':>7} {'Internal':>9} {'Variance':>9} {'Novelty':>8} {'Explore':>8}")
    output.append("-"*70)
    
    # Baseline first
    baseline = [r for r in all_results if 'Baseline' in r['name']][0]
    output.append(f"{baseline['name']:<25} "
          f"{baseline['final_population']:5d} "
          f"{baseline['final_genome_length']:7.1f} "
          f"{baseline['final_internal_score']:9.2f} "
          f"{baseline['vigor']['metric_variance']:9.2f} "
          f"{baseline['vigor']['novelty_events']:8d} "
          f"{baseline['vigor']['exploration_score']:8.2f}")
    
    output.append("-"*70)
    
    # Other experiments
    for result in all_results:
        if 'Baseline' in result['name']:
            continue
        
        output.append(f"{result['name']:<25} "
              f"{result['final_population']:5d} "
              f"{result['final_genome_length']:7.1f} "
              f"{result['final_internal_score']:9.2f} "
              f"{result['vigor']['metric_variance']:9.2f} "
              f"{result['vigor']['novelty_events']:8d} "
              f"{result['vigor']['exploration_score']:8.2f}")
    
    output.append("")
    
    # Find best performer
    best = max(all_results, key=lambda r: r['vigor']['exploration_score'])
    output.append(f"Best Exploration Score: {best['name']}")
    output.append(f"  Exploration Score: {best['vigor']['exploration_score']:.2f}")
    output.append(f"  Metric Variance: {best['vigor']['metric_variance']:.2f}")
    output.append(f"  Novelty Events: {best['vigor']['novelty_events']}")
    output.append("")
    
    # Write to file
    out_path = Path(__file__).parent.parent.parent / 'analysis' / 'latex_figures' / 'data' / 'param_exploration_results.txt'
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, 'w') as f:
        f.write('\n'.join(output))
    print(f"Results saved to {out_path}")


def run_parameter_exploration():
    """Run all parameter exploration experiments."""
    print("="*70)
    print("PARAMETER EXPLORATION FOR INCREASED EXPLORATORY VIGOR")
    print("="*70)
    print()
    print("Goal: Find parameter settings that increase exploration")
    print("      while maintaining population stability")
    print()
    
    all_results = []
    
    # Set seed for reproducibility
    import random
    random.seed(42)
    
    # Baseline (from Genesis Moment test)
    print("\n[1/7] Running Baseline...")
    baseline = run_experiment(
        "Baseline",
        mutation_rate=0.1,
        transition_total_generations=1000
    )
    all_results.append(baseline)
    
    # Experiment 1: Higher mutation rate
    print("\n[2/7] Running High Mutation Rate...")
    high_mutation = run_experiment(
        "High Mutation (0.3)",
        mutation_rate=0.3,
        transition_total_generations=1000
    )
    all_results.append(high_mutation)
    
    # Experiment 2: Very high mutation rate
    print("\n[3/7] Running Very High Mutation Rate...")
    very_high_mutation = run_experiment(
        "Very High Mutation (0.5)",
        mutation_rate=0.5,
        transition_total_generations=1000
    )
    all_results.append(very_high_mutation)
    
    # Experiment 3: Faster transition
    print("\n[4/7] Running Faster Transition...")
    fast_transition = run_experiment(
        "Fast Transition (500 gen)",
        mutation_rate=0.1,
        transition_total_generations=500
    )
    all_results.append(fast_transition)
    
    # Experiment 4: Slower transition
    print("\n[5/7] Running Slower Transition...")
    slow_transition = run_experiment(
        "Slow Transition (1500 gen)",
        mutation_rate=0.1,
        transition_total_generations=1500
    )
    all_results.append(slow_transition)
    
    # Experiment 5: Combined - high mutation + fast transition
    print("\n[6/7] Running Combined (High Mut + Fast Trans)...")
    combined = run_experiment(
        "High Mut + Fast Trans",
        mutation_rate=0.3,
        transition_total_generations=500
    )
    all_results.append(combined)
    
    # Experiment 6: Moderate increase
    print("\n[7/7] Running Moderate Increase...")
    moderate = run_experiment(
        "Moderate (0.2 mut)",
        mutation_rate=0.2,
        transition_total_generations=1000
    )
    all_results.append(moderate)
    
    # Print comparison
    print_results_summary(all_results)
    
    # Recommendations
    print("="*70)
    print("RECOMMENDATIONS")
    print("="*70)
    print()
    
    best = max(all_results, key=lambda r: r['vigor']['exploration_score'])
    
    print("Based on exploratory vigor analysis:")
    print()
    print(f"1. Best Configuration: {best['name']}")
    print(f"   - Mutation Rate: {best['params']['mutation_rate']}")
    print(f"   - Transition Period: {best['params']['transition_total_generations']} generations")
    print(f"   - Exploration Score: {best['vigor']['exploration_score']:.2f}")
    print()
    
    print("2. Observations:")
    
    # Compare mutation rates
    mut_01 = [r for r in all_results if r['params']['mutation_rate'] == 0.1][0]
    mut_03 = [r for r in all_results if r['params']['mutation_rate'] == 0.3][0]
    
    if mut_03['vigor']['exploration_score'] > mut_01['vigor']['exploration_score']:
        print("   - Higher mutation rates increase exploration")
    else:
        print("   - Higher mutation rates may destabilize without increasing exploration")
    
    # Check population stability
    unstable = [r for r in all_results if r['final_population'] < 50]
    if unstable:
        print(f"   - WARNING: {len(unstable)} configuration(s) showed population decline")
    else:
        print("   - All configurations maintained stable populations")
    
    print()
    print("3. Recommended for Long-Term Run (20,000+ generations):")
    print(f"   - Mutation Rate: {best['params']['mutation_rate']}")
    print(f"   - Transition Period: 10,000 generations (for smooth transition)")
    print(f"   - Population Size: 100")
    print()
    
    print("="*70)


if __name__ == '__main__':
    run_parameter_exploration()
