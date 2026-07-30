"""
plot_shock_b_replication.py - Replication trajectory plot

Generates shock_b_trajectory.png:
  - 4 panels (one per condition)
  - Each panel: 5 lines (one per seed), survival over generations
  - Clear visual of whether each condition is consistent across seeds
"""

import os
import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.cm as cm
from matplotlib.gridspec import GridSpec
from matplotlib.lines import Line2D

root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if root_dir not in sys.path:
    sys.path.append(root_dir)

CONDITION_TITLES = {
    'Condition A (V5 467 nodes)':           'Condition A — V5 (467 nodes, unconstrained)',
    'Condition B (V6 Constrained 52 nodes)':'Condition B — V6-Constrained (52 nodes, 815 edges)',
    'Condition C (V4 123 nodes)':           'Condition C — V4 (123 nodes)',
    'Condition D (Naive 12 nodes)':         'Condition D — Naive (12 nodes)',
}

CONDITION_ORDER = list(CONDITION_TITLES.keys())

SEED_COLORS = {
    42:   '#4CC9F0',
    123:  '#F72585',
    456:  '#7209B7',
    789:  '#F77F00',
    1011: '#2EC4B6',
}

def setup_style():
    plt.rcParams.update({
        'figure.facecolor': '#0D1117',
        'axes.facecolor':   '#161B22',
        'axes.edgecolor':   '#30363D',
        'axes.labelcolor':  '#E6EDF3',
        'xtick.color':      '#8B949E',
        'ytick.color':      '#8B949E',
        'text.color':       '#E6EDF3',
        'grid.color':       '#21262D',
        'grid.alpha':       0.5,
        'font.family':      'DejaVu Sans',
        'axes.titlesize':   10,
        'axes.labelsize':   9,
        'xtick.labelsize':  8,
        'ytick.labelsize':  8,
    })

def main():
    output_dir = os.path.join(root_dir, 'v6', 'results')
    traj_path    = os.path.join(output_dir, 'shock_b_trajectory_data.csv')
    summary_path = os.path.join(output_dir, 'shock_b_replication_summary.csv')
    out_path     = os.path.join(output_dir, 'shock_b_trajectory.png')

    if not os.path.exists(traj_path):
        print(f'[ERROR] trajectory data not found: {traj_path}')
        print('Run run_shock_b_replication.py first.')
        sys.exit(1)

    df      = pd.read_csv(traj_path)
    summary = pd.read_csv(summary_path) if os.path.exists(summary_path) else None
    seeds   = sorted(df['Seed'].unique())

    setup_style()
    fig = plt.figure(figsize=(18, 14), facecolor='#0D1117')
    gs  = GridSpec(2, 2, figure=fig, hspace=0.45, wspace=0.30,
                   left=0.07, right=0.97, top=0.90, bottom=0.10)

    axes = [fig.add_subplot(gs[r, c]) for r in range(2) for c in range(2)]

    for ax_idx, cond in enumerate(CONDITION_ORDER):
        ax = axes[ax_idx]
        cond_df = df[df['Condition'] == cond]

        for seed in seeds:
            seed_df = cond_df[cond_df['Seed'] == seed].sort_values('Generation')
            if len(seed_df) == 0:
                continue
            color = SEED_COLORS.get(seed, '#888888')
            ax.plot(
                seed_df['Generation'].values,
                seed_df['SurvivalRate'].values,
                color=color, linewidth=1.8, alpha=0.85,
                label=f'Seed {seed}',
            )
            # Mark final point
            ax.scatter(
                seed_df['Generation'].values[-1],
                seed_df['SurvivalRate'].values[-1],
                color=color, s=40, zorder=5, edgecolors='white', linewidths=0.5
            )

        # Pass/fail band
        ax.axhline(1.0, color='#51CF66', linestyle='--', linewidth=0.8,
                   alpha=0.5, label='100% target (A/B/C)')
        ax.axhline(0.5, color='#FF6B6B', linestyle='--', linewidth=0.8,
                   alpha=0.5, label='50% fail threshold (D)')

        # Final survival annotations from summary
        if summary is not None:
            cond_sum = summary[summary['Condition'] == cond]
            for _, row in cond_sum.iterrows():
                color = SEED_COLORS.get(int(row['Seed']), '#888')
                flag_str = f" [{row['Flag']}]" if row['Flag'] != 'OK' else ''
                ax.annotate(
                    f"s{int(row['Seed'])}:{row['FinalSurvival']:.2f}{flag_str}",
                    xy=(5000, row['FinalSurvival']),
                    xytext=(4600, row['FinalSurvival']),
                    color=color, fontsize=6.5, va='center',
                )

        ax.set_xlim(0, 5200)
        ax.set_ylim(-0.05, 1.15)
        ax.set_xlabel('Generation', fontsize=9)
        ax.set_ylabel('Pre-Selection Survival Rate', fontsize=9)
        ax.set_title(CONDITION_TITLES.get(cond, cond), fontsize=10, pad=8)
        ax.grid(alpha=0.3)
        ax.legend(fontsize=7, loc='lower right', ncol=2)

    # Global legend for seeds
    legend_handles = [
        Line2D([0], [0], color=SEED_COLORS.get(s, '#888'), linewidth=2,
               label=f'Seed {s}')
        for s in seeds
    ]
    fig.legend(
        handles=legend_handles,
        loc='lower center', ncol=len(seeds),
        fontsize=9, facecolor='#21262D', edgecolor='#30363D',
        bbox_to_anchor=(0.5, 0.02)
    )

    # Title
    n_seeds = len(seeds)
    total_gens = len(df['Generation'].unique()) * n_seeds * 4
    fig.suptitle(
        f'Shock B (Barrier + Gap) Replication — Survival Trajectories\n'
        f'{n_seeds} Seeds x 4 Conditions x 5,000 Gens = {n_seeds*4*5000:,} Total Generations',
        fontsize=13, color='#E6EDF3', fontweight='bold', y=0.95
    )

    fig.savefig(out_path, dpi=160, bbox_inches='tight', facecolor='#0D1117')
    print(f'[SUCCESS] Plot saved: {out_path}')
    plt.close(fig)


if __name__ == '__main__':
    main()
