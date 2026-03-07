"""
Generate Paper Figures (GECCO Submission)
Generates high-resolution PDF plots for the paper.
"""

import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
from pathlib import Path
import sys

# Add current dir to path
sys.path.insert(0, str(Path(__file__).parent))
from process_logs import load_baseline_data, align_and_aggregate

# Configure Plotting Style
plt.style.use('seaborn-v0_8-paper')
sns.set_context("paper", font_scale=1.5)
plt.rcParams['pdf.fonttype'] = 42
plt.rcParams['ps.fonttype'] = 42
plt.rcParams['font.family'] = 'serif' # Times New Roman-ish

COLORS = {
    'Genesis': '#d62728', # Red
    'Novelty': '#1f77b4', # Blue
    'MAP-Elites': '#2ca02c', # Green
    'Random': '#7f7f7f', # Gray
    'Fixed': '#ff7f0e' # Orange
}

def plot_figure_1_aggregated(output_dir):
    """
    Figure 1: Aggregated Timeseries (GAC, EPC, NND) for Full Genesis.
    3 Subplots.
    """
    print("Generating Figure 1...")
    # Load Genesis Data (Placeholder: Use Novelty data as proxy for now if Genesis files disjoint)
    # Ideally load actual Genesis logs. 
    # For now, let's create a dummy plot frame
    
    fig, axes = plt.subplots(3, 1, figsize=(10, 12), sharex=True)
    
    # Plot Logic Placeholder
    axes[0].set_ylabel("GAC (Genome)")
    axes[1].set_ylabel("EPC (Phenotype)")
    axes[2].set_ylabel("NND (Novelty)")
    axes[2].set_xlabel("Generation")
    
    plt.tight_layout()
    plt.savefig(output_dir / 'figure1_aggregated_timeseries.pdf')
    print("Saved Figure 1")

def plot_figure_2_comparison(output_dir):
    """
    Figure 2: Baseline Comparison (GAC over time).
    Genesis vs Fixed vs Random vs Novelty.
    """
    print("Generating Figure 2...")
    plt.figure(figsize=(10, 6))
    
    # Load Data
    results_dir = Path(__file__).parent.parent.parent / 'results' / 'baselines'
    
    baselines = {
        'Novelty': 'novelty_search',
        'Fixed': 'fixed_constraints',
        'Random': 'random_search',
        'MAP-Elites': 'map_elites' 
    }
    
    for label, name in baselines.items():
        df = load_baseline_data(name, results_dir)
        if not df.empty:
            stats = align_and_aggregate(df, 'gac', label)
            
            plt.plot(stats['generation'], stats['median'], label=label, color=COLORS.get(label, 'black'))
            plt.fill_between(stats['generation'], stats['p25'], stats['p75'], alpha=0.2, color=COLORS.get(label, 'black'))
            
    plt.xlabel("Generation")
    plt.ylabel("Genome Architecture Complexity (GAC)")
    plt.title("Evolutionary Trajectories Comparison")
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(output_dir / 'figure2_baseline_comparison.pdf')
    print("Saved Figure 2")

def create_figure_3_diagnostics(failure_dict, all_data_dict, output_dir):
    """
    Figure 3: Failure Mode Diagnostics.
    3 Subplots showing representative runs for each failure mode.
    """
    print("Generating Figure 3 (Diagnostics)...")
    fig, axes = plt.subplots(1, 3, figsize=(18, 5))
    
    modes = [
        ('metabolic_failure', 'Metabolic Overload', 'GAC vs EPC Divergence'),
        ('dominance_failure', 'Dominance Monopoly', 'NND Collapse (< 0.1)'),
        ('neutral_drift', 'Neutral Drift', 'Stagnation (Slopes ~ 0)')
    ]
    
    for i, (mode_key, title, subtitle) in enumerate(modes):
        ax = axes[i]
        run_ids = failure_dict.get(mode_key, [])
        
        if not run_ids:
            ax.text(0.5, 0.5, "No Runs Detected", ha='center', va='center')
            ax.set_title(f"{title}\n{subtitle}")
            continue
            
        # Pick first representative
        rep_id = run_ids[0]
        df = all_data_dict.get(rep_id, pd.DataFrame())
        
        if df.empty:
            continue
            
        # Plot Logic
        if mode_key == 'metabolic_failure':
            # Plot GAC and EPC on twin axes or normalized
            ax.plot(df['generation'], df['gac'], 'r-', label='GAC (Genome)')
            ax2 = ax.twinx()
            ax2.plot(df['generation'], df['epc'], 'b--', label='EPC (Phenotype)')
            
            ax.set_xlabel("Generation")
            ax.set_ylabel("GAC", color='r')
            ax2.set_ylabel("EPC", color='b')
            
        elif mode_key == 'dominance_failure':
            # Plot NND
            ax.plot(df['generation'], df['nnd'], 'g-', label='NND')
            ax.axhline(0.1, color='k', linestyle=':', label='Threshold (0.1)')
            ax.set_xlabel("Generation")
            ax.set_ylabel("Normalized Novelty Distance")
            
        elif mode_key == 'neutral_drift':
            # Plot all normalized? Or just raw
            # Normalize to start 0 for comparison
            ax.plot(df['generation'], df['gac'], label='GAC')
            ax.plot(df['generation'], df['epc'], label='EPC')
            ax.plot(df['generation'], df['nnd'], label='NND')
            ax.set_xlabel("Generation")
            ax.set_ylabel("Value")
            ax.legend()
            
        ax.set_title(f"{title}\n{subtitle}")
        ax.grid(True, alpha=0.3)
        
    plt.tight_layout()
    plt.savefig(output_dir / 'figure3_failure_mode_diagnostics.pdf')
    print("Saved Figure 3")

def create_figure_4_carp_dynamics(success_ids, all_data_dict, output_dir):
    """
    Figure 4: CARP Dynamics (Lambda vs Viability).
    Plots Lambda(t) and V(t) for 3 successful runs.
    """
    print("Generating Figure 4 (CARP Dynamics)...")
    
    # Select up to 3 runs
    selected = success_ids[:3]
    if not selected:
        print(" [WARN] No successful runs found for Fig 4")
        return
        
    fig, axes = plt.subplots(len(selected), 1, figsize=(10, 4 * len(selected)), sharex=True)
    if len(selected) == 1: axes = [axes]
    
    for i, run_id in enumerate(selected):
        ax = axes[i]
        df = all_data_dict.get(run_id)
        
        # Check if we have lambda/viability columns
        # If logging didn't include them, we might be out of luck or need to mock columns for layout test
        has_carp = 'lambda' in df.columns and 'viability' in df.columns
        
        if not has_carp:
            # Fallback or Skip
            ax.text(0.5, 0.5, "CARP Data Not Logged", ha='center')
            continue
            
        # Lambda (Constraint Severity) - Left Axis
        l1 = ax.plot(df['generation'], df['lambda'], 'b-', label='Constraint $\lambda(t)$')
        ax.set_ylabel("$\lambda(t)$", color='b')
        ax.tick_params(axis='y', labelcolor='b')
        
        # Viability - Right Axis
        ax2 = ax.twinx()
        l2 = ax2.plot(df['generation'], df['viability'], 'g--', label='Viability $V(t)$')
        ax2.set_ylabel("Viability $V(t)$", color='g')
        ax2.tick_params(axis='y', labelcolor='g')
        
        # Reference Line
        ax2.axhline(0.8, color='k', linestyle=':', alpha=0.5, label='Target $V=0.8$')
        
        # Legend
        lns = l1 + l2
        labs = [l.get_label() for l in lns]
        ax.legend(lns, labs, loc='upper right')
        
        ax.set_title(f"Run {run_id}: Regulatory Dynamics")
        ax.grid(True, alpha=0.3)
        
    if len(selected) > 0:
        axes[-1].set_xlabel("Generation")
        
    plt.tight_layout()
    plt.savefig(output_dir / 'figure4_carp_dynamics.pdf')
    print("Saved Figure 4")

def main():
    root = Path(__file__).parent.parent.parent
    output_dir = root / 'analysis' / 'figures'
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. Load Data
    print("Loading Experimental Data...")
    all_runs = {}
    
    baselines = ['novelty_search', 'map_elites', 'random_search', 'fixed_constraints']
    results_dir = root / 'results' / 'baselines'
    
    for base in baselines:
        df = load_baseline_data(base, results_dir)
        if not df.empty:
            # Split by seed to create individual run entries
            # Run ID format: {baseline}_seed_{seed}
            for seed in df['seed'].unique():
                run_id = f"{base}_seed_{seed}"
                run_df = df[df['seed'] == seed].copy()
                all_runs[run_id] = run_df
                
    print(f"Loaded {len(all_runs)} runs.")
    
    # 2. Classify
    from process_logs import classify_failure_modes
    failures = classify_failure_modes(all_runs)
    
    # Print Classification Summary
    print("\nFailure Mode Classification:")
    for k, v in failures.items():
        print(f"  {k}: {len(v)} runs ({v})")
    
    # 3. Plot
    plot_figure_1_aggregated(output_dir)
    plot_figure_2_comparison(output_dir)
    create_figure_3_diagnostics(failures, all_runs, output_dir)
    create_figure_4_carp_dynamics(failures.get('success', []), all_runs, output_dir)

if __name__ == '__main__':
    main()
