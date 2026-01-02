"""
Deep-Dive Analysis of Genesis Moment Run

This script analyzes the 15,000-generation run to understand:
- Multi-metric evolutionary trajectories
- Trade-offs and niche space exploration
- Population diversity over time
- Behavioral space exploration (novelty)

Focuses on post-transition period (generations 10,000-15,000).
"""

import sys
from pathlib import Path
import pickle
import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, str(Path(__file__).parent / 'genesis_engine_v2'))

from engine.genesis_engine import GenesisEngine


def load_or_generate_data():
    """Load existing run data or generate new 15k run."""
    data_file = Path("genesis_moment_data.pkl")
    
    if data_file.exists():
        print("Loading existing Genesis Moment data...")
        with open(data_file, 'rb') as f:
            statistics = pickle.load(f)
        print(f"  Loaded {len(statistics)} generations of data")
        return statistics
    else:
        print("No existing data found. Please run run_genesis_moment_test.py first.")
        print("Or generating new data...")
        
        # Generate new data
        engine = GenesisEngine(
            population_size=100,
            mutation_rate=0.1,
            simulation_steps=10,
            transition_start_generation=0,
            transition_total_generations=10000
        )
        
        print("Running 15,000 generations...")
        for gen in range(15000):
            engine.run_cycle()
            if (gen + 1) % 1000 == 0:
                print(f"  Generation {gen + 1}/15000")
        
        # Save data
        with open(data_file, 'wb') as f:
            pickle.dump(engine.statistics, f)
        
        print(f"Data saved to {data_file}")
        return engine.statistics


def plot_multi_metric_trajectories(statistics, start_gen=10000):
    """Plot all key metrics over post-transition period."""
    print("\n1. Plotting multi-metric trajectories...")
    
    post_transition = [s for s in statistics if s['generation'] >= start_gen]
    
    if len(post_transition) == 0:
        print("  No post-transition data available")
        return
    
    generations = [s['generation'] for s in post_transition]
    
    # Extract metrics
    external_scores = [s['avg_external_score'] for s in post_transition]
    internal_scores = [s['avg_internal_score'] for s in post_transition]
    final_scores = [s['avg_final_score'] for s in post_transition]
    genome_lengths = [s['avg_genome_length'] for s in post_transition]
    linkage_groups = [s['avg_linkage_groups'] for s in post_transition]
    pop_sizes = [s['population_size'] for s in post_transition]
    
    # Create multi-panel plot
    fig, axes = plt.subplots(3, 2, figsize=(14, 10))
    fig.suptitle('Post-Transition Evolutionary Trajectories (Gen 10,000-15,000)', fontsize=14)
    
    # External Score
    axes[0, 0].plot(generations, external_scores, 'b-', alpha=0.7)
    axes[0, 0].set_title('External Score (Bootstrap Fitness)')
    axes[0, 0].set_ylabel('Score')
    axes[0, 0].grid(True, alpha=0.3)
    
    # Internal Score
    axes[0, 1].plot(generations, internal_scores, 'r-', alpha=0.7)
    axes[0, 1].set_title('Internal Score (Pareto Distinction)')
    axes[0, 1].set_ylabel('Score')
    axes[0, 1].grid(True, alpha=0.3)
    
    # Final Score
    axes[1, 0].plot(generations, final_scores, 'g-', alpha=0.7)
    axes[1, 0].set_title('Final Score (100% Internal)')
    axes[1, 0].set_ylabel('Score')
    axes[1, 0].grid(True, alpha=0.3)
    
    # Genome Length
    axes[1, 1].plot(generations, genome_lengths, 'm-', alpha=0.7)
    axes[1, 1].set_title('Average Genome Length')
    axes[1, 1].set_ylabel('Genes')
    axes[1, 1].grid(True, alpha=0.3)
    
    # Linkage Groups
    axes[2, 0].plot(generations, linkage_groups, 'c-', alpha=0.7)
    axes[2, 0].set_title('Average Linkage Groups')
    axes[2, 0].set_ylabel('Groups')
    axes[2, 0].set_xlabel('Generation')
    axes[2, 0].grid(True, alpha=0.3)
    
    # Population Size
    axes[2, 1].plot(generations, pop_sizes, 'k-', alpha=0.7)
    axes[2, 1].set_title('Population Size')
    axes[2, 1].set_ylabel('Agents')
    axes[2, 1].set_xlabel('Generation')
    axes[2, 1].grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('analysis_multi_metric_trajectories.png', dpi=150)
    print("  Saved: analysis_multi_metric_trajectories.png")
    plt.close()


def plot_trade_off_analysis(statistics, start_gen=10000):
    """Plot 2D scatter plots to visualize niche space exploration."""
    print("\n2. Plotting trade-off analysis...")
    
    post_transition = [s for s in statistics if s['generation'] >= start_gen]
    
    if len(post_transition) == 0:
        print("  No post-transition data available")
        return
    
    # Extract metrics
    external_scores = [s['avg_external_score'] for s in post_transition]
    internal_scores = [s['avg_internal_score'] for s in post_transition]
    genome_lengths = [s['avg_genome_length'] for s in post_transition]
    linkage_groups = [s['avg_linkage_groups'] for s in post_transition]
    
    # Color by generation (to show temporal progression)
    generations = [s['generation'] for s in post_transition]
    colors = np.array(generations)
    
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    fig.suptitle('Trade-off Analysis: Niche Space Exploration', fontsize=14)
    
    # External vs Internal
    scatter1 = axes[0, 0].scatter(external_scores, internal_scores, c=colors, 
                                   cmap='viridis', alpha=0.6, s=20)
    axes[0, 0].set_xlabel('External Score')
    axes[0, 0].set_ylabel('Internal Score')
    axes[0, 0].set_title('External vs Internal Fitness')
    axes[0, 0].grid(True, alpha=0.3)
    
    # Genome Length vs Linkage Groups
    scatter2 = axes[0, 1].scatter(genome_lengths, linkage_groups, c=colors,
                                   cmap='viridis', alpha=0.6, s=20)
    axes[0, 1].set_xlabel('Genome Length')
    axes[0, 1].set_ylabel('Linkage Groups')
    axes[0, 1].set_title('Complexity vs Organization')
    axes[0, 1].grid(True, alpha=0.3)
    
    # Genome Length vs Internal Score
    scatter3 = axes[1, 0].scatter(genome_lengths, internal_scores, c=colors,
                                   cmap='viridis', alpha=0.6, s=20)
    axes[1, 0].set_xlabel('Genome Length')
    axes[1, 0].set_ylabel('Internal Score')
    axes[1, 0].set_title('Complexity vs Distinction')
    axes[1, 0].grid(True, alpha=0.3)
    
    # Linkage Groups vs Internal Score
    scatter4 = axes[1, 1].scatter(linkage_groups, internal_scores, c=colors,
                                   cmap='viridis', alpha=0.6, s=20)
    axes[1, 1].set_xlabel('Linkage Groups')
    axes[1, 1].set_ylabel('Internal Score')
    axes[1, 1].set_title('Organization vs Distinction')
    axes[1, 1].grid(True, alpha=0.3)
    
    # Add colorbar
    cbar = plt.colorbar(scatter1, ax=axes, orientation='horizontal', 
                        pad=0.05, aspect=40)
    cbar.set_label('Generation')
    
    plt.tight_layout()
    plt.savefig('analysis_trade_off_space.png', dpi=150)
    print("  Saved: analysis_trade_off_space.png")
    plt.close()


def calculate_diversity_metrics(statistics, start_gen=10000):
    """Calculate and plot population diversity metrics."""
    print("\n3. Calculating diversity metrics...")
    
    post_transition = [s for s in statistics if s['generation'] >= start_gen]
    
    if len(post_transition) == 0:
        print("  No post-transition data available")
        return
    
    generations = [s['generation'] for s in post_transition]
    
    # Calculate variance in key metrics (proxy for diversity)
    # Note: We only have population averages, so we'll track variance of averages over time
    
    # Rolling window variance
    window_size = 100
    genome_variance = []
    internal_variance = []
    
    genome_lengths = [s['avg_genome_length'] for s in post_transition]
    internal_scores = [s['avg_internal_score'] for s in post_transition]
    
    for i in range(len(post_transition)):
        if i < window_size:
            genome_variance.append(0)
            internal_variance.append(0)
        else:
            window_genomes = genome_lengths[i-window_size:i]
            window_internals = internal_scores[i-window_size:i]
            
            genome_var = np.var(window_genomes)
            internal_var = np.var(window_internals)
            
            genome_variance.append(genome_var)
            internal_variance.append(internal_var)
    
    # Plot diversity metrics
    fig, axes = plt.subplots(2, 1, figsize=(12, 8))
    fig.suptitle('Population Diversity Metrics (Rolling 100-gen window)', fontsize=14)
    
    axes[0].plot(generations, genome_variance, 'b-', alpha=0.7)
    axes[0].set_title('Genome Length Variance')
    axes[0].set_ylabel('Variance')
    axes[0].grid(True, alpha=0.3)
    
    axes[1].plot(generations, internal_variance, 'r-', alpha=0.7)
    axes[1].set_title('Internal Score Variance')
    axes[1].set_ylabel('Variance')
    axes[1].set_xlabel('Generation')
    axes[1].grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('analysis_diversity_metrics.png', dpi=150)
    print("  Saved: analysis_diversity_metrics.png")
    plt.close()
    
    # Print summary
    print(f"\n  Diversity Summary:")
    print(f"    Avg Genome Variance: {np.mean(genome_variance[window_size:]):.2f}")
    print(f"    Avg Internal Variance: {np.mean(internal_variance[window_size:]):.2f}")


def analyze_behavioral_space(statistics, start_gen=10000):
    """Analyze behavioral space exploration using metric profiles."""
    print("\n4. Analyzing behavioral space exploration...")
    
    post_transition = [s for s in statistics if s['generation'] >= start_gen]
    
    if len(post_transition) == 0:
        print("  No post-transition data available")
        return
    
    # Create 4D metric profiles (we have 4 main metrics)
    profiles = []
    generations = []
    
    for s in post_transition:
        profile = [
            s['avg_external_score'],
            s['avg_internal_score'],
            s['avg_genome_length'],
            s['avg_linkage_groups']
        ]
        profiles.append(profile)
        generations.append(s['generation'])
    
    profiles = np.array(profiles)
    
    # Normalize each dimension
    for i in range(profiles.shape[1]):
        col = profiles[:, i]
        profiles[:, i] = (col - col.min()) / (col.max() - col.min() + 1e-10)
    
    # Simple PCA-like analysis: compute distances from initial state
    initial_profile = profiles[0]
    distances = [np.linalg.norm(p - initial_profile) for p in profiles]
    
    # Plot behavioral space exploration
    fig, axes = plt.subplots(2, 1, figsize=(12, 8))
    fig.suptitle('Behavioral Space Exploration', fontsize=14)
    
    # Distance from initial state
    axes[0].plot(generations, distances, 'g-', alpha=0.7)
    axes[0].set_title('Distance from Initial Behavioral State')
    axes[0].set_ylabel('Euclidean Distance')
    axes[0].grid(True, alpha=0.3)
    
    # Cumulative exploration (sum of distances)
    cumulative = np.cumsum(np.abs(np.diff([0] + distances)))
    axes[1].plot(generations, cumulative, 'purple', alpha=0.7)
    axes[1].set_title('Cumulative Behavioral Exploration')
    axes[1].set_ylabel('Cumulative Distance')
    axes[1].set_xlabel('Generation')
    axes[1].grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('analysis_behavioral_space.png', dpi=150)
    print("  Saved: analysis_behavioral_space.png")
    plt.close()
    
    # Novelty detection: significant jumps in distance
    novelty_events = []
    threshold = np.mean(distances) + 2 * np.std(distances)
    
    for i, (gen, dist) in enumerate(zip(generations, distances)):
        if dist > threshold:
            novelty_events.append({'generation': gen, 'distance': dist})
    
    print(f"\n  Behavioral Space Summary:")
    print(f"    Final distance from initial state: {distances[-1]:.3f}")
    print(f"    Total exploration: {cumulative[-1]:.3f}")
    print(f"    Novelty events (>2σ): {len(novelty_events)}")
    if novelty_events:
        print(f"    Example events:")
        for event in novelty_events[:3]:
            print(f"      Gen {event['generation']}: distance={event['distance']:.3f}")


def run_analysis():
    """Run complete analysis pipeline."""
    print("=" * 70)
    print("DEEP-DIVE ANALYSIS OF GENESIS MOMENT RUN")
    print("=" * 70)
    
    # Load data
    statistics = load_or_generate_data()
    
    if len(statistics) < 10000:
        print("\nInsufficient data for post-transition analysis")
        return
    
    print(f"\nAnalyzing {len(statistics)} generations")
    print(f"Post-transition period: Gen 10,000-{statistics[-1]['generation']}")
    print()
    
    # Run analyses
    plot_multi_metric_trajectories(statistics)
    plot_trade_off_analysis(statistics)
    calculate_diversity_metrics(statistics)
    analyze_behavioral_space(statistics)
    
    print("\n" + "=" * 70)
    print("ANALYSIS COMPLETE")
    print("=" * 70)
    print("\nGenerated plots:")
    print("  1. analysis_multi_metric_trajectories.png")
    print("  2. analysis_trade_off_space.png")
    print("  3. analysis_diversity_metrics.png")
    print("  4. analysis_behavioral_space.png")
    print()


if __name__ == '__main__':
    try:
        import matplotlib
        run_analysis()
    except ImportError:
        print("ERROR: matplotlib is required for this analysis")
        print("Install with: pip install matplotlib")
        sys.exit(1)
