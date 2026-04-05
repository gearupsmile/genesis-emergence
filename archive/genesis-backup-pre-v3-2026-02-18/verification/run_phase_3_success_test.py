"""
Phase 3 Success Test - 2000 Generation Evolution

This script executes the Phase 3 success criterion:
"Show a clear, upward trend in the population's average external fitness 
score over 2000 cycles."

Test Parameters:
- Population: 100 agents
- Mutation Rate: 0.1
- Generations: 2000
- Logging: Every 100 generations
"""

import sys
from pathlib import Path
import time

sys.path.insert(0, str(Path(__file__).parent / 'genesis_engine_v2'))

from engine.genesis_engine import GenesisEngine


def create_sparkline(values, width=50):
    """Create a simple ASCII sparkline from values."""
    if not values:
        return ""
    
    min_val = min(values)
    max_val = max(values)
    range_val = max_val - min_val
    
    if range_val == 0:
        return "-" * width
    
    # Map values to height using simple ASCII characters
    chars = " .-:=+*#%@"
    sparkline = ""
    
    for val in values:
        normalized = (val - min_val) / range_val
        char_idx = int(normalized * (len(chars) - 1))
        sparkline += chars[char_idx]
    
    return sparkline


def run_phase_3_success_test():
    """Execute the Phase 3 success test."""
    print("=" * 70)
    print("PHASE 3 SUCCESS TEST - 2000 GENERATION EVOLUTION")
    print("=" * 70)
    print()
    
    # Test parameters
    population_size = 100
    mutation_rate = 0.1
    num_generations = 2000
    log_interval = 100
    
    print(f"Test Parameters:")
    print(f"  Population Size: {population_size}")
    print(f"  Mutation Rate: {mutation_rate}")
    print(f"  Generations: {num_generations}")
    print(f"  Logging Interval: Every {log_interval} generations")
    print()
    
    # Initialize engine
    print("Initializing GenesisEngine...")
    engine = GenesisEngine(
        population_size=population_size,
        mutation_rate=mutation_rate,
        simulation_steps=10
    )
    print(f"  Initial population: {len(engine.population)} agents")
    print(f"  World: {engine.world}")
    print()
    
    # Run evolution
    print("=" * 70)
    print("RUNNING EVOLUTION")
    print("=" * 70)
    print()
    print(f"{'Gen':>6} {'Pop':>5} {'Avg Fitness':>12} {'Max Fitness':>12} {'Avg Genome':>11} {'Time (s)':>10}")
    print("-" * 70)
    
    start_time = time.time()
    last_log_time = start_time
    
    for gen in range(num_generations):
        engine.run_cycle()
        
        # Log every log_interval generations
        if (gen + 1) % log_interval == 0 or gen == 0:
            stats = engine.statistics[-1]
            current_time = time.time()
            elapsed = current_time - last_log_time
            last_log_time = current_time
            
            print(f"{gen + 1:6d} {stats['population_size']:5d} "
                  f"{stats['avg_fitness']:12.2f} {stats['max_fitness']:12.2f} "
                  f"{stats['avg_genome_length']:11.1f} {elapsed:10.2f}")
    
    total_time = time.time() - start_time
    print("-" * 70)
    print(f"Total time: {total_time:.2f} seconds ({total_time/60:.2f} minutes)")
    print()
    
    # Analysis
    print("=" * 70)
    print("SUCCESS ANALYSIS")
    print("=" * 70)
    print()
    
    # Extract fitness data
    all_avg_fitness = [s['avg_fitness'] for s in engine.statistics]
    all_max_fitness = [s['max_fitness'] for s in engine.statistics]
    
    # Calculate statistics
    start_fitness = all_avg_fitness[0]
    end_fitness = all_avg_fitness[-1]
    fitness_change = end_fitness - start_fitness
    fitness_change_pct = (fitness_change / start_fitness * 100) if start_fitness > 0 else 0
    
    max_start = all_max_fitness[0]
    max_end = all_max_fitness[-1]
    
    print(f"Starting Average Fitness: {start_fitness:.2f}")
    print(f"Ending Average Fitness:   {end_fitness:.2f}")
    print(f"Change:                   {fitness_change:+.2f} ({fitness_change_pct:+.1f}%)")
    print()
    print(f"Starting Max Fitness:     {max_start:.2f}")
    print(f"Ending Max Fitness:       {max_end:.2f}")
    print()
    
    # Trend analysis
    # Sample every 50 generations for trend plot
    sample_interval = 50
    sampled_fitness = [all_avg_fitness[i] for i in range(0, len(all_avg_fitness), sample_interval)]
    
    print("Fitness Trend (every 50 generations):")
    sparkline = create_sparkline(sampled_fitness, width=min(len(sampled_fitness), 70))
    print(f"  {sparkline}")
    print(f"  Gen 0: {sampled_fitness[0]:.2f}  ->  Gen {num_generations}: {sampled_fitness[-1]:.2f}")
    print()
    
    # Determine trend
    # Calculate linear regression slope
    n = len(all_avg_fitness)
    x_mean = n / 2
    y_mean = sum(all_avg_fitness) / n
    
    numerator = sum((i - x_mean) * (all_avg_fitness[i] - y_mean) for i in range(n))
    denominator = sum((i - x_mean) ** 2 for i in range(n))
    slope = numerator / denominator if denominator != 0 else 0
    
    print(f"Trend Analysis:")
    print(f"  Linear regression slope: {slope:.6f}")
    print(f"  Interpretation: ", end="")
    
    if slope > 0.001:
        print("STRONG UPWARD TREND [PASS]")
        trend_result = "PASS"
    elif slope > 0:
        print("WEAK UPWARD TREND [PASS]")
        trend_result = "PASS (weak)"
    elif slope < -0.001:
        print("DOWNWARD TREND [FAIL]")
        trend_result = "FAIL"
    else:
        print("FLAT/NO TREND")
        trend_result = "INCONCLUSIVE"
    print()
    
    # Final verdict
    print("=" * 70)
    print("PHASE 3 SUCCESS CRITERION")
    print("=" * 70)
    print()
    print("Criterion: Show a clear, upward trend in average fitness over 2000 cycles")
    print()
    
    if trend_result.startswith("PASS"):
        print("[SUCCESS] Clear upward trend demonstrated!")
        print(f"  - Fitness increased from {start_fitness:.2f} to {end_fitness:.2f}")
        print(f"  - Improvement of {fitness_change_pct:.1f}%")
        print(f"  - Positive slope: {slope:.6f}")
        success = True
    else:
        print("[FAILURE] No clear upward trend")
        print(f"  - Slope: {slope:.6f}")
        success = False
    
    print()
    print("=" * 70)
    
    return success


if __name__ == '__main__':
    success = run_phase_3_success_test()
    sys.exit(0 if success else 1)
