"""
analyze_transfer_shock.py - Analysis and Summary Plot Generator for Phase 2 Transfer Shock Study
"""

import sys
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Ensure project root is on sys.path
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if root_dir not in sys.path:
    sys.path.append(root_dir)

def generate_transfer_shock_plots():
    csv_path = os.path.join(root_dir, 'v6', 'results', 'transfer_shock.csv')
    output_png = os.path.join(root_dir, 'v6', 'results', 'transfer_shock_summary.png')

    if not os.path.exists(csv_path):
        print(f"Error: {csv_path} does not exist.")
        return

    df = pd.read_csv(csv_path)

    plt.style.use('dark_background')
    fig, axes = plt.subplots(2, 2, figsize=(14, 10), dpi=300)
    fig.suptitle('Genesis V6 Phase 2: Transfer Shock Experiment Summary', fontsize=16, fontweight='bold', y=0.98)

    conditions = df['Condition'].unique()
    colors = {
        'Condition A (V5 467 nodes)': '#1f77b4',       # Blue
        'Condition B (V6 Constrained 52 nodes)': '#ff7f0e', # Orange
        'Condition C (V4 123 nodes)': '#2ca02c',       # Green
        'Condition D (Naive 12 nodes)': '#d62728'        # Red
    }

    # 1. Adaptation Speed Bar Chart (Generations to 80% Performance)
    ax1 = axes[0, 0]
    speed_data = df.groupby('Condition')['AdaptationSpeed'].min()
    cond_names_short = [c.split(' (')[0] for c in speed_data.index]
    bar_colors = [colors.get(c, '#9467bd') for c in speed_data.index]
    bars = ax1.bar(cond_names_short, speed_data.values, color=bar_colors, alpha=0.85, edgecolor='white')

    ax1.set_title('Adaptation Speed (Lower = Faster to 80% Perf)', fontsize=12, fontweight='bold')
    ax1.set_ylabel('Generations to 80% Performance', fontsize=10)
    ax1.grid(True, linestyle='--', alpha=0.3, axis='y')
    for bar in bars:
        height = bar.get_height()
        ax1.annotate(f'{int(height)}',
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 3),  # 3 points vertical offset
                    textcoords="offset points",
                    ha='center', va='bottom', fontsize=9, fontweight='bold')

    # 2. Survival Rate Curves over Time
    ax2 = axes[0, 1]
    for cond in conditions:
        cond_df = df[df['Condition'] == cond].groupby('Generation')['SurvivalRate'].mean()
        label_short = cond.split(' (')[0] + (' (Constrained 52n)' if 'Constrained' in cond else '')
        ax2.plot(cond_df.index, cond_df.values, label=label_short, color=colors.get(cond, '#9467bd'), linewidth=2)
    ax2.set_title('Survival Rate over Time', fontsize=12, fontweight='bold')
    ax2.set_xlabel('Generations', fontsize=10)
    ax2.set_ylabel('Survival Rate', fontsize=10)
    ax2.set_ylim(-0.05, 1.05)
    ax2.grid(True, linestyle='--', alpha=0.3)
    ax2.legend(fontsize=8, loc='lower right')

    # 3. Action Entropy over Time (Behavioral Exploration)
    ax3 = axes[1, 0]
    for cond in conditions:
        cond_df = df[df['Condition'] == cond].groupby('Generation')['ActionEntropy'].mean()
        label_short = cond.split(' (')[0] + (' (Constrained 52n)' if 'Constrained' in cond else '')
        ax3.plot(cond_df.index, cond_df.values, label=label_short, color=colors.get(cond, '#9467bd'), linewidth=2)
    ax3.set_title('Behavioral Exploration (Action Entropy)', fontsize=12, fontweight='bold')
    ax3.set_xlabel('Generations', fontsize=10)
    ax3.set_ylabel('Action Entropy', fontsize=10)
    ax3.grid(True, linestyle='--', alpha=0.3)
    ax3.legend(fontsize=8, loc='upper right')

    # 4. ANNEX Accumulation (Novel Innovations Solved)
    ax4 = axes[1, 1]
    for cond in conditions:
        cond_df = df[df['Condition'] == cond].groupby('Generation')['ANNEX'].mean()
        label_short = cond.split(' (')[0] + (' (Constrained 52n)' if 'Constrained' in cond else '')
        ax4.plot(cond_df.index, cond_df.values, label=label_short, color=colors.get(cond, '#9467bd'), linewidth=2)
    ax4.set_title('ANNEX Accumulation (Novel Innovations)', fontsize=12, fontweight='bold')
    ax4.set_xlabel('Generations', fontsize=10)
    ax4.set_ylabel('Persisted Innovations', fontsize=10)
    ax4.grid(True, linestyle='--', alpha=0.3)
    ax4.legend(fontsize=8, loc='upper left')

    plt.tight_layout(rect=[0, 0, 1, 0.96])
    plt.savefig(output_png)
    plt.close()
    print(f"[SUCCESS] Transfer shock summary plot saved to:\n  {output_png}")

if __name__ == '__main__':
    generate_transfer_shock_plots()
