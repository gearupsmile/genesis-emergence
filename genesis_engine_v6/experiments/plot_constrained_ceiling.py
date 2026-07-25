"""
plot_constrained_ceiling.py - Plotting script for Genesis V6 Constrained Ceiling Ablation Study
Plots:
1. Average Nodes
2. Action Entropy
3. Genetic Activity Coefficient (GAC)
4. Species Count
"""

import os
import pandas as pd
import matplotlib.pyplot as plt

def generate_summary_plots(csv_path: str = 'v6/results/constrained_ceiling.csv',
                           output_png: str = 'v6/results/constrained_ceiling_summary.png'):
    if not os.path.exists(csv_path):
        print(f"Error: {csv_path} not found.")
        return

    df = pd.read_csv(csv_path)

    # Separate control and constrained
    df_control = df[df['Condition'] == 'Control']
    df_constrained = df[df['Condition'] == 'Constrained']

    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle('Genesis V6: Constrained Ceiling Ablation Study (10,000 Generations)', fontsize=16, fontweight='bold')

    # Color scheme
    color_control = '#1f77b4'       # Blue
    color_constrained = '#d62728'   # Red

    # 1. Average Nodes
    ax1 = axes[0, 0]
    ax1.plot(df_control['Generation'], df_control['AvgNodes'], label='Control (Unconstrained)', color=color_control, linewidth=2)
    ax1.plot(df_constrained['Generation'], df_constrained['AvgNodes'], label='Constrained (Max 52)', color=color_constrained, linewidth=2, linestyle='--')
    ax1.axhline(y=52, color='gray', linestyle=':', label='Ceiling (52 Nodes)')
    ax1.set_title('Average Genome Nodes')
    ax1.set_xlabel('Generations')
    ax1.set_ylabel('Node Count')
    ax1.legend()
    ax1.grid(True, alpha=0.3)

    # 2. Action Entropy
    ax2 = axes[0, 1]
    ax2.plot(df_control['Generation'], df_control['ActionEntropy'], label='Control (Unconstrained)', color=color_control, linewidth=2)
    ax2.plot(df_constrained['Generation'], df_constrained['ActionEntropy'], label='Constrained (Max 52)', color=color_constrained, linewidth=2, linestyle='--')
    ax2.set_title('Action Entropy (Shannon)')
    ax2.set_xlabel('Generations')
    ax2.set_ylabel('Entropy (bits)')
    ax2.legend()
    ax2.grid(True, alpha=0.3)

    # 3. GAC
    ax3 = axes[1, 0]
    ax3.plot(df_control['Generation'], df_control['GAC'], label='Control (Unconstrained)', color=color_control, linewidth=2)
    ax3.plot(df_constrained['Generation'], df_constrained['GAC'], label='Constrained (Max 52)', color=color_constrained, linewidth=2, linestyle='--')
    ax3.set_title('Genetic Activity Coefficient (GAC)')
    ax3.set_xlabel('Generations')
    ax3.set_ylabel('Persisting Edits Ratio (>500 gens)')
    ax3.legend()
    ax3.grid(True, alpha=0.3)

    # 4. Species Count
    ax4 = axes[1, 1]
    ax4.plot(df_control['Generation'], df_control['SpeciesCount'], label='Control (Unconstrained)', color=color_control, linewidth=2)
    ax4.plot(df_constrained['Generation'], df_constrained['SpeciesCount'], label='Constrained (Max 52)', color=color_constrained, linewidth=2, linestyle='--')
    ax4.set_title('Active Species Count')
    ax4.set_xlabel('Generations')
    ax4.set_ylabel('Species')
    ax4.legend()
    ax4.grid(True, alpha=0.3)

    plt.tight_layout()
    os.makedirs(os.path.dirname(output_png), exist_ok=True)
    plt.savefig(output_png, dpi=300)
    print(f"[SUCCESS] Summary plot saved to {output_png}")

if __name__ == "__main__":
    generate_summary_plots()
