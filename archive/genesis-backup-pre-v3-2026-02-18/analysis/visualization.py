"""
Visualization Module for Phase 6 Deep Probe Analysis

Generates 5 critical plots for PNCT metrics analysis:
1. GAC Trajectory (genome length over time)
2. EPC Trajectory (LZ complexity & instruction diversity)
3. NND Distribution (novelty distances by epoch)
4. Correlation Heatmap (GAC vs EPC vs NND)
5. 3D Phase Space (trajectory through metric space)
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib import cm
from mpl_toolkits.mplot3d import Axes3D
import seaborn as sns
from pathlib import Path


def plot_gac_trajectory(data, output_dir=None):
    """
    Plot GAC (Genome Architecture Complexity) trajectory.
    
    Shows genome length mean with 10th/90th percentile bands.
    """
    gac = data['gac']
    
    if not gac:
        print("No GAC data available")
        return
    
    generations = [d['generation'] for d in gac]
    means = [d['genome_mean'] for d in gac]
    
    fig, ax = plt.subplots(figsize=(12, 6))
    
    ax.plot(generations, means, 'b-', linewidth=2, label='Mean Genome Length')
    ax.fill_between(generations, means, alpha=0.3)
    
    ax.set_xlabel('Generation', fontsize=12)
    ax.set_ylabel('Genome Length (genes)', fontsize=12)
    ax.set_title('GAC Trajectory: Genome Complexity Over Time', fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3)
    ax.legend()
    
    plt.tight_layout()
    
    if output_dir:
        plt.savefig(Path(output_dir) / 'gac_trajectory.png', dpi=300, bbox_inches='tight')
        print(f"  Saved: gac_trajectory.png")
    
    plt.close()


def plot_epc_trajectory(data, output_dir=None):
    """
    Plot EPC (Expressed Phenotype Complexity) trajectory.
    
    Shows LZ complexity and instruction diversity over time.
    """
    epc = data['epc']
    
    if not epc:
        print("No EPC data available")
        return
    
    generations = [d['generation'] for d in epc]
    lz_means = [d['lz_mean'] for d in epc]
    div_means = [d['diversity_mean'] for d in epc]
    
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
    
    # LZ Complexity
    ax1.plot(generations, lz_means, 'r-', linewidth=2, label='LZ Complexity')
    ax1.set_ylabel('LZ Complexity', fontsize=12)
    ax1.set_title('EPC Trajectory: Phenotypic Complexity Over Time', fontsize=14, fontweight='bold')
    ax1.grid(True, alpha=0.3)
    ax1.legend()
    
    # Instruction Diversity
    ax2.plot(generations, div_means, 'g-', linewidth=2, label='Instruction Diversity')
    ax2.set_xlabel('Generation', fontsize=12)
    ax2.set_ylabel('Instruction Diversity', fontsize=12)
    ax2.grid(True, alpha=0.3)
    ax2.legend()
    
    plt.tight_layout()
    
    if output_dir:
        plt.savefig(Path(output_dir) / 'epc_trajectory.png', dpi=300, bbox_inches='tight')
        print(f"  Saved: epc_trajectory.png")
    
    plt.close()


def plot_nnd_distribution(data, output_dir=None):
    """
    Plot NND (Normalized Novelty Distance) distribution.
    
    Box plots showing novelty at each epoch (1k-generation intervals).
    """
    nnd = data['nnd']
    
    if not nnd:
        print("No NND data available")
        return
    
    # Group by epoch (every 1000 generations)
    epochs = {}
    for d in nnd:
        epoch = d['generation'] // 1000
        if epoch not in epochs:
            epochs[epoch] = []
        epochs[epoch].append(d['mean_nnd'])
    
    if not epochs:
        print("Insufficient NND data for distribution plot")
        return
    
    epoch_labels = sorted(epochs.keys())
    epoch_data = [epochs[e] for e in epoch_labels]
    
    fig, ax = plt.subplots(figsize=(14, 6))
    
    bp = ax.boxplot(epoch_data, labels=[f"{e}k" for e in epoch_labels], patch_artist=True)
    
    for patch in bp['boxes']:
        patch.set_facecolor('lightblue')
        patch.set_alpha(0.7)
    
    ax.set_xlabel('Epoch (thousands of generations)', fontsize=12)
    ax.set_ylabel('Normalized Novelty Distance', fontsize=12)
    ax.set_title('NND Distribution: Novelty Across Evolutionary Epochs', fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3, axis='y')
    
    plt.tight_layout()
    
    if output_dir:
        plt.savefig(Path(output_dir) / 'nnd_distribution.png', dpi=300, bbox_inches='tight')
        print(f"  Saved: nnd_distribution.png")
    
    plt.close()


def plot_correlation_heatmap(data, output_dir=None):
    """
    Plot correlation heatmap between GAC, EPC, and NND metrics.
    """
    gac = data['gac']
    epc = data['epc']
    nnd = data['nnd']
    
    if not (gac and epc and nnd):
        print("Insufficient data for correlation heatmap")
        return
    
    # Align data by generation
    gac_dict = {d['generation']: d['genome_mean'] for d in gac}
    epc_lz_dict = {d['generation']: d['lz_mean'] for d in epc}
    epc_div_dict = {d['generation']: d['diversity_mean'] for d in epc}
    nnd_dict = {d['generation']: d['mean_nnd'] for d in nnd}
    
    # Find common generations
    common_gens = set(gac_dict.keys()) & set(epc_lz_dict.keys()) & set(nnd_dict.keys())
    common_gens = sorted(common_gens)
    
    if len(common_gens) < 10:
        print("Insufficient aligned data for correlation")
        return
    
    # Build correlation matrix
    gac_vals = [gac_dict[g] for g in common_gens]
    epc_lz_vals = [epc_lz_dict[g] for g in common_gens]
    epc_div_vals = [epc_div_dict.get(g, 0) for g in common_gens]
    nnd_vals = [nnd_dict[g] for g in common_gens]
    
    data_matrix = np.array([gac_vals, epc_lz_vals, epc_div_vals, nnd_vals])
    corr_matrix = np.corrcoef(data_matrix)
    
    labels = ['GAC\n(Genome)', 'EPC\n(LZ)', 'EPC\n(Diversity)', 'NND\n(Novelty)']
    
    fig, ax = plt.subplots(figsize=(10, 8))
    
    sns.heatmap(corr_matrix, annot=True, fmt='.3f', cmap='coolwarm', 
                xticklabels=labels, yticklabels=labels, 
                vmin=-1, vmax=1, center=0, ax=ax, cbar_kws={'label': 'Correlation'})
    
    ax.set_title('Metric Correlation Heatmap', fontsize=14, fontweight='bold')
    
    plt.tight_layout()
    
    if output_dir:
        plt.savefig(Path(output_dir) / 'correlation_heatmap.png', dpi=300, bbox_inches='tight')
        print(f"  Saved: correlation_heatmap.png")
    
    plt.close()


def plot_3d_phase_space(data, output_dir=None):
    """
    Plot 3D phase space trajectory through (GAC, EPC, NND) space.
    """
    gac = data['gac']
    epc = data['epc']
    nnd = data['nnd']
    
    if not (gac and epc and nnd):
        print("Insufficient data for 3D phase space")
        return
    
    # Align data
    gac_dict = {d['generation']: d['genome_mean'] for d in gac}
    epc_dict = {d['generation']: d['lz_mean'] for d in epc}
    nnd_dict = {d['generation']: d['mean_nnd'] for d in nnd}
    
    common_gens = set(gac_dict.keys()) & set(epc_dict.keys()) & set(nnd_dict.keys())
    common_gens = sorted(common_gens)
    
    if len(common_gens) < 5:
        print("Insufficient aligned data for 3D plot")
        return
    
    gac_vals = np.array([gac_dict[g] for g in common_gens])
    epc_vals = np.array([epc_dict[g] for g in common_gens])
    nnd_vals = np.array([nnd_dict[g] for g in common_gens])
    
    fig = plt.figure(figsize=(12, 10))
    ax = fig.add_subplot(111, projection='3d')
    
    # Color by time
    colors = cm.viridis(np.linspace(0, 1, len(common_gens)))
    
    ax.scatter(gac_vals, epc_vals, nnd_vals, c=colors, s=50, alpha=0.6)
    ax.plot(gac_vals, epc_vals, nnd_vals, 'k-', alpha=0.3, linewidth=1)
    
    # Mark start and end
    ax.scatter([gac_vals[0]], [epc_vals[0]], [nnd_vals[0]], 
               c='green', s=200, marker='o', label='Start', edgecolors='black', linewidths=2)
    ax.scatter([gac_vals[-1]], [epc_vals[-1]], [nnd_vals[-1]], 
               c='red', s=200, marker='*', label='End', edgecolors='black', linewidths=2)
    
    ax.set_xlabel('GAC (Genome Length)', fontsize=11)
    ax.set_ylabel('EPC (LZ Complexity)', fontsize=11)
    ax.set_zlabel('NND (Novelty)', fontsize=11)
    ax.set_title('3D Phase Space: Evolutionary Trajectory', fontsize=14, fontweight='bold')
    ax.legend()
    
    plt.tight_layout()
    
    if output_dir:
        plt.savefig(Path(output_dir) / 'phase_space_3d.png', dpi=300, bbox_inches='tight')
        print(f"  Saved: phase_space_3d.png")
    
    plt.close()


def generate_all_plots(data, output_dir):
    """Generate all 5 critical plots."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    print("Generating visualizations...")
    plot_gac_trajectory(data, output_dir)
    plot_epc_trajectory(data, output_dir)
    plot_nnd_distribution(data, output_dir)
    plot_correlation_heatmap(data, output_dir)
    plot_3d_phase_space(data, output_dir)
    print("All visualizations complete!")


if __name__ == '__main__':
    import sys
    sys.path.insert(0, str(Path(__file__).parent))
    from phase6_analyzer import DeepProbeAnalyzer
    
    if len(sys.argv) < 2:
        print("Usage: python visualization.py <run_directory>")
        sys.exit(1)
    
    analyzer = DeepProbeAnalyzer(sys.argv[1])
    data = analyzer.load_and_process()
    
    output_dir = Path(sys.argv[1]) / "visualizations"
    generate_all_plots(data, output_dir)
