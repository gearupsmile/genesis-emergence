"""
Phase 5: Extended 50,000-Generation Exploration

This script executes the recommended long-term evolution run to:
- Characterize long-term evolutionary dynamics
- Test Hypothesis 2: Pareto Front Expansion
- Identify system attractors and equilibria
- Observe emergent patterns over extended timescales

Configuration (from system characterization):
- Population: 100 agents
- Mutation Rate: 0.3 (optimal exploration/stability balance)
- Transition: 10,000 generations
- Total: 50,000 generations (40k pure emergent)
"""

import sys
from pathlib import Path
import time
import pickle

sys.path.insert(0, str(Path(__file__).parent / 'genesis_engine_v2'))

from engine.genesis_engine import GenesisEngine


def calculate_pareto_front_metrics(engine):
    """
    Calculate Pareto front size and metric spans.
    
    Returns dict with:
    - front_size: Number of non-dominated agents
    - metric_spans: Range in each metric dimension
    """
    if len(engine.population) == 0:
        return {'front_size': 0, 'metric_spans': {}}
    
    # Get Pareto front from internal evaluator
    pareto_front = engine.internal_evaluator.get_pareto_front(engine.population)
    
    # Calculate metric spans for entire population
    profiles = [engine.internal_evaluator.calculate_profile(agent) 
                for agent in engine.population]
    
    if len(profiles) == 0:
        return {'front_size': 0, 'metric_spans': {}}
    
    # Transpose to get each metric's values
    metric_names = ['phenotype_len', 'genome_len', 'cost_inv', 
                    'expr_ratio', 'linkage_groups', 'age']
    
    spans = {}
    for i, name in enumerate(metric_names):
        values = [p[i] for p in profiles]
        spans[name] = max(values) - min(values) if values else 0
    
    return {
        'front_size': len(pareto_front),
        'metric_spans': spans
    }


def calculate_diversity_metrics(engine):
    """
    Calculate population diversity metrics.
    
    Returns dict with variance in key metrics.
    """
    if len(engine.population) == 0:
        return {'genome_var': 0, 'linkage_var': 0}
    
    genome_lengths = [agent.genome.get_length() for agent in engine.population]
    linkage_groups = [agent.linkage_structure.get_num_groups() 
                      for agent in engine.population]
    
    # Calculate variance
    genome_mean = sum(genome_lengths) / len(genome_lengths)
    linkage_mean = sum(linkage_groups) / len(linkage_groups)
    
    genome_var = sum((x - genome_mean)**2 for x in genome_lengths) / len(genome_lengths)
    linkage_var = sum((x - linkage_mean)**2 for x in linkage_groups) / len(linkage_groups)
    
    return {
        'genome_var': genome_var,
        'linkage_var': linkage_var
    }


def save_checkpoint(engine, checkpoint_num, checkpoint_dir='checkpoints'):
    """Save engine state and statistics."""
    Path(checkpoint_dir).mkdir(exist_ok=True)
    
    checkpoint_file = Path(checkpoint_dir) / f'checkpoint_{checkpoint_num:05d}.pkl'
    
    checkpoint_data = {
        'generation': engine.generation,
        'statistics': engine.statistics,
        'population_size': len(engine.population),
        'transition_weight': engine.transition_weight
    }
    
    with open(checkpoint_file, 'wb') as f:
        pickle.dump(checkpoint_data, f)
    
    print(f"  [CHECKPOINT] Saved to {checkpoint_file}")


def run_50k_exploration():
    """Execute the 50,000-generation exploration."""
    print("=" * 70)
    print("PHASE 5: EXTENDED 50,000-GENERATION EXPLORATION")
    print("=" * 70)
    print()
    
    # Configuration (from system characterization)
    population_size = 100
    mutation_rate = 0.3  # Optimal balance
    transition_start = 0
    transition_total = 10000
    total_generations = 50000
    log_interval = 500
    checkpoint_interval = 10000
    
    print("Configuration:")
    print(f"  Population Size: {population_size}")
    print(f"  Mutation Rate: {mutation_rate} (24x exploration boost)")
    print(f"  Transition Period: {transition_start} - {transition_total}")
    print(f"  Total Generations: {total_generations}")
    print(f"  Logging Interval: Every {log_interval} generations")
    print(f"  Checkpoint Interval: Every {checkpoint_interval} generations")
    print()
    
    print("Evolution Timeline:")
    print(f"  Gen 0-{transition_total}: Transition (external -> internal fitness)")
    print(f"  Gen {transition_total}-{total_generations}: Pure endogenous evolution (40k gens)")
    print()
    
    # Initialize engine
    print("Initializing GenesisEngine...")
    engine = GenesisEngine(
        population_size=population_size,
        mutation_rate=mutation_rate,
        simulation_steps=10,
        transition_start_generation=transition_start,
        transition_total_generations=transition_total
    )
    print(f"  Engine initialized: {engine}")
    print()
    
    # Run evolution
    print("=" * 70)
    print("RUNNING EVOLUTION")
    print("=" * 70)
    print()
    print(f"{'Gen':>6} {'Pop':>5} {'Weight':>7} {'External':>9} {'Internal':>9} "
          f"{'Genome':>7} {'PFront':>7} {'Diversity':>10} {'Time (s)':>10}")
    print("-" * 70)
    
    start_time = time.time()
    last_log_time = start_time
    
    # Track Pareto front evolution for Hypothesis 2
    pareto_history = []
    
    for gen in range(total_generations):
        engine.run_cycle()
        
        # Enhanced logging
        if (gen + 1) % log_interval == 0 or gen == 0:
            stats = engine.statistics[-1]
            current_time = time.time()
            elapsed = current_time - last_log_time
            last_log_time = current_time
            
            # Calculate enhanced metrics
            pareto_metrics = calculate_pareto_front_metrics(engine)
            diversity_metrics = calculate_diversity_metrics(engine)
            
            # Store for analysis
            pareto_history.append({
                'generation': gen + 1,
                'front_size': pareto_metrics['front_size'],
                'metric_spans': pareto_metrics['metric_spans']
            })
            
            # Add to statistics
            stats['pareto_front_size'] = pareto_metrics['front_size']
            stats['genome_variance'] = diversity_metrics['genome_var']
            stats['linkage_variance'] = diversity_metrics['linkage_var']
            
            print(f"{gen + 1:6d} {stats['population_size']:5d} "
                  f"{stats['transition_weight']:7.2f} "
                  f"{stats['avg_external_score']:9.2f} "
                  f"{stats['avg_internal_score']:9.2f} "
                  f"{stats['avg_genome_length']:7.1f} "
                  f"{pareto_metrics['front_size']:7d} "
                  f"{diversity_metrics['genome_var']:10.2f} "
                  f"{elapsed:10.2f}")
        
        # Checkpointing
        if (gen + 1) % checkpoint_interval == 0:
            save_checkpoint(engine, gen + 1)
    
    total_time = time.time() - start_time
    print("-" * 70)
    print(f"Total time: {total_time:.2f} seconds ({total_time/60:.2f} minutes, {total_time/3600:.2f} hours)")
    print()
    
    # Save final data
    print("Saving final data...")
    final_data = {
        'statistics': engine.statistics,
        'pareto_history': pareto_history,
        'parameters': {
            'population_size': population_size,
            'mutation_rate': mutation_rate,
            'transition_total': transition_total,
            'total_generations': total_generations
        }
    }
    
    with open('phase5_50k_exploration.pkl', 'wb') as f:
        pickle.dump(final_data, f)
    
    print("  Saved: phase5_50k_exploration.pkl")
    print()
    
    # Hypothesis 2 Analysis: Pareto Front Expansion
    print("=" * 70)
    print("HYPOTHESIS 2 ANALYSIS: PARETO FRONT EXPANSION")
    print("=" * 70)
    print()
    
    # Compare early vs late Pareto fronts
    early_period = [p for p in pareto_history if 10000 <= p['generation'] <= 20000]
    late_period = [p for p in pareto_history if 40000 <= p['generation'] <= 50000]
    
    if early_period and late_period:
        # Average front size
        early_front_size = sum(p['front_size'] for p in early_period) / len(early_period)
        late_front_size = sum(p['front_size'] for p in late_period) / len(late_period)
        
        print(f"Pareto Front Size:")
        print(f"  Early (Gen 10k-20k): {early_front_size:.1f} agents")
        print(f"  Late (Gen 40k-50k):  {late_front_size:.1f} agents")
        print(f"  Change: {late_front_size - early_front_size:+.1f} ({((late_front_size/early_front_size - 1)*100):+.1f}%)")
        print()
        
        # Metric span analysis
        print("Metric Span Evolution:")
        metric_names = ['phenotype_len', 'genome_len', 'cost_inv', 
                        'expr_ratio', 'linkage_groups', 'age']
        
        for metric in metric_names:
            early_spans = [p['metric_spans'].get(metric, 0) for p in early_period]
            late_spans = [p['metric_spans'].get(metric, 0) for p in late_period]
            
            early_avg = sum(early_spans) / len(early_spans) if early_spans else 0
            late_avg = sum(late_spans) / len(late_spans) if late_spans else 0
            
            change_pct = ((late_avg / early_avg - 1) * 100) if early_avg > 0 else 0
            
            print(f"  {metric:20s}: {early_avg:8.2f} -> {late_avg:8.2f} ({change_pct:+6.1f}%)")
        
        print()
        
        # Verdict
        if late_front_size > early_front_size * 1.1:
            print("[HYPOTHESIS SUPPORTED] Pareto front expanded significantly")
        elif late_front_size < early_front_size * 0.9:
            print("[HYPOTHESIS REJECTED] Pareto front contracted")
        else:
            print("[HYPOTHESIS INCONCLUSIVE] Pareto front remained stable")
    
    print()
    print("=" * 70)
    print("PHASE 5 COMPLETE")
    print("=" * 70)
    print()
    print("Generated outputs:")
    print("  - phase5_50k_exploration.pkl (full data)")
    print("  - checkpoints/ directory (10k-gen intervals)")
    print()
    print("Next steps:")
    print("  1. Run analyze_genesis_run.py for detailed visualizations")
    print("  2. Analyze long-term patterns and attractors")
    print("  3. Compare with baseline 15k run")
    print()
    
    return True


if __name__ == '__main__':
    success = run_50k_exploration()
    sys.exit(0 if success else 1)
