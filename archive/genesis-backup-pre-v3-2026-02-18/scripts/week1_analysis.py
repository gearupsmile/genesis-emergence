"""
Week 1 Validation Analysis - Extract Metrics from 25k Run

Analyzes the 25k physics validation run to extract:
1. Gatekeeper rejection rate over time
2. Edge-of-viability diversity
3. Search space exploration patterns
"""

import pickle
import json
import statistics
from pathlib import Path


def analyze_25k_run():
    """Analyze the 25k validation run for Week 1 metrics."""
    
    checkpoint_file = Path("runs/25k_physics_v2_validation_20260106_160453/checkpoints/checkpoint_025000.pkl")
    
    if not checkpoint_file.exists():
        print(f"ERROR: Checkpoint not found: {checkpoint_file}")
        return
    
    print("Loading checkpoint data...")
    with open(checkpoint_file, 'rb') as f:
        data = pickle.load(f)
    
    # Extract data
    gac_history = data.get('gac_history', [])
    physics_stats = data.get('physics_stats', {})
    
    print(f"\nCheckpoint Data:")
    print(f"  Generation: {data.get('generation', 'Unknown')}")
    print(f"  Population: {data.get('population_size', 0)}")
    print(f"  GAC snapshots: {len(gac_history)}")
    
    # Physics Gatekeeper Stats
    print(f"\nPhysics Gatekeeper:")
    print(f"  Total checks: {physics_stats.get('total_checks', 0):,}")
    print(f"  Total violations: {physics_stats.get('total_violations', 0):,}")
    print(f"  Violation rate: {physics_stats.get('violation_rate', 0):.2%}")
    print(f"  Energy constant: {physics_stats.get('energy_constant', 0)}")
    
    # Calculate max viable genome length
    energy_const = physics_stats.get('energy_constant', 0.5)
    max_viable_length = (energy_const / 0.005) ** (1/1.5)
    print(f"  Max viable genome length: ~{max_viable_length:.1f} genes")
    
    # Analyze GAC trajectory
    if gac_history:
        print(f"\nGAC Trajectory:")
        print(f"  Initial mean GAC: {gac_history[0]['genome_length']['mean']:.1f}")
        print(f"  Final mean GAC: {gac_history[-1]['genome_length']['mean']:.1f}")
        print(f"  Final max GAC: {gac_history[-1]['genome_length']['max']:.1f}")
        
        # Edge-of-viability analysis (agents within 10% of limit)
        edge_threshold = max_viable_length * 0.9  # Within 10% of limit
        
        edge_diversity_over_time = []
        for snapshot in gac_history:
            gen = snapshot['generation']
            mean_gac = snapshot['genome_length']['mean']
            std_gac = snapshot['genome_length']['std']
            max_gac = snapshot['genome_length']['max']
            
            # If population is near edge, record diversity
            if mean_gac >= edge_threshold:
                edge_diversity_over_time.append({
                    'generation': gen,
                    'std_gac': std_gac,
                    'mean_gac': mean_gac,
                    'max_gac': max_gac
                })
        
        print(f"\nEdge-of-Viability Analysis:")
        print(f"  Edge threshold (90% of limit): {edge_threshold:.1f} genes")
        print(f"  Generations at edge: {len(edge_diversity_over_time)}")
        
        if edge_diversity_over_time:
            avg_edge_diversity = statistics.mean(e['std_gac'] for e in edge_diversity_over_time)
            print(f"  Average diversity at edge: {avg_edge_diversity:.2f}")
            print(f"  First edge gen: {edge_diversity_over_time[0]['generation']}")
            print(f"  Last edge gen: {edge_diversity_over_time[-1]['generation']}")
    
    # Calculate rejection rate
    total_gens = data.get('generation', 25000)
    total_checks = physics_stats.get('total_checks', 0)
    total_violations = physics_stats.get('total_violations', 0)
    
    avg_checks_per_gen = total_checks / total_gens if total_gens > 0 else 0
    avg_violations_per_gen = total_violations / total_gens if total_gens > 0 else 0
    avg_rejection_rate = (avg_violations_per_gen / avg_checks_per_gen * 100) if avg_checks_per_gen > 0 else 0
    
    print(f"\nRejection Rate Analysis:")
    print(f"  Average checks/generation: {avg_checks_per_gen:.1f}")
    print(f"  Average violations/generation: {avg_violations_per_gen:.1f}")
    print(f"  Average rejection rate: {avg_rejection_rate:.2f}%")
    
    return {
        'physics_stats': physics_stats,
        'max_viable_length': max_viable_length,
        'edge_threshold': edge_threshold,
        'edge_diversity_snapshots': edge_diversity_over_time,
        'avg_rejection_rate': avg_rejection_rate
    }


if __name__ == '__main__':
    analyze_25k_run()
