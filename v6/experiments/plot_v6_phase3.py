"""
plot_v6_phase3.py - Publication-ready Phase 3 visualization

4-panel figure:
  Panel 1: Survival Rate by Condition × Shock (grouped bar)
  Panel 2: ANNEX Step Function over Generations (line, should show steps not flat 815)
  Panel 3: Entropy vs Trajectory Diversity scatter (noise vs genuine classification)
  Panel 4: Phenotype Diversity by Condition (bar, final gen)

Usage:
    python v6/experiments/plot_v6_phase3.py
    python v6/experiments/plot_v6_phase3.py --input v6/results/phase3_results.csv
"""

import os
import sys
import argparse
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.gridspec import GridSpec

root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if root_dir not in sys.path:
    sys.path.append(root_dir)


# ---------------------------------------------------------------------------
# Styling
# ---------------------------------------------------------------------------

CONDITION_COLORS = {
    'Condition A (V5 467 nodes)':          '#4CC9F0',   # Cyan-blue
    'Condition B (V6 Constrained 52 nodes)': '#F72585', # Hot pink
    'Condition C (V4 123 nodes)':           '#7209B7',  # Purple
    'Condition D (Naive 12 nodes)':         '#F77F00',  # Orange
}

CONDITION_SHORT = {
    'Condition A (V5 467 nodes)':          'A: V5 (467n)',
    'Condition B (V6 Constrained 52 nodes)': 'B: V6-C (52n)',
    'Condition C (V4 123 nodes)':           'C: V4 (123n)',
    'Condition D (Naive 12 nodes)':         'D: Naive (12n)',
}

SHOCK_LABELS = {
    'Shock A (Pressure Wave)': 'A: Pressure\nWave',
    'Shock B (Barrier + Gap)': 'B: Barrier\n+ Gap',
    'Shock C (Sensor Blinding)': 'C: Sensor\nBlinding',
}

VERDICT_COLORS = {
    'NOISE':          '#FF6B6B',
    'GENUINE':        '#51CF66',
    'LOW_COMPLEXITY': '#868E96',
}

VERDICT_MARKERS = {
    'NOISE':          'x',
    'GENUINE':        'o',
    'LOW_COMPLEXITY': 's',
}


def setup_style():
    plt.rcParams.update({
        'figure.facecolor': '#0D1117',
        'axes.facecolor': '#161B22',
        'axes.edgecolor': '#30363D',
        'axes.labelcolor': '#E6EDF3',
        'xtick.color': '#8B949E',
        'ytick.color': '#8B949E',
        'text.color': '#E6EDF3',
        'grid.color': '#21262D',
        'grid.alpha': 0.6,
        'font.family': 'DejaVu Sans',
        'axes.titlesize': 11,
        'axes.labelsize': 9,
        'xtick.labelsize': 8,
        'ytick.labelsize': 8,
        'legend.fontsize': 8,
        'legend.facecolor': '#21262D',
        'legend.edgecolor': '#30363D',
    })


# ---------------------------------------------------------------------------
# Panel 1: Survival Rate grouped bar
# ---------------------------------------------------------------------------

def plot_survival_rate(ax, df):
    conditions = list(CONDITION_SHORT.keys())
    conditions = [c for c in conditions if c in df['Condition'].unique()]
    shocks = df['Environment'].unique()

    final_df = df.groupby(['Condition', 'Environment'])['SurvivalRate'].last().reset_index()

    n_shocks = len(shocks)
    n_conds = len(conditions)
    bar_w = 0.18
    group_w = bar_w * n_conds + 0.08

    for ci, cond in enumerate(conditions):
        offsets = np.arange(n_shocks) * group_w + ci * bar_w
        vals = []
        for shock in shocks:
            row = final_df[(final_df['Condition'] == cond) & (final_df['Environment'] == shock)]
            vals.append(float(row['SurvivalRate'].values[0]) if len(row) > 0 else 0.0)

        bars = ax.bar(
            offsets, vals, bar_w,
            color=CONDITION_COLORS.get(cond, '#888'),
            label=CONDITION_SHORT.get(cond, cond),
            alpha=0.9, edgecolor='#0D1117', linewidth=0.5,
        )

    shock_labels = [SHOCK_LABELS.get(s, s) for s in shocks]
    xtick_pos = np.arange(n_shocks) * group_w + (n_conds - 1) * bar_w / 2
    ax.set_xticks(xtick_pos)
    ax.set_xticklabels(shock_labels, fontsize=8)
    ax.set_ylim(0, 1.15)
    ax.set_ylabel('Final Survival Rate', fontsize=9)
    ax.set_title('Panel 1: Survival Rate by Condition × Shock\n(Target: Condition D < 0.2 in Shocks B & C)', fontsize=10)
    ax.axhline(0.2, color='#FF6B6B', linestyle='--', linewidth=1.0, alpha=0.7, label='D crash threshold')
    ax.legend(fontsize=7, ncol=2, loc='upper right')
    ax.grid(axis='y', alpha=0.3)
    ax.set_xlim(-0.1, n_shocks * group_w)


# ---------------------------------------------------------------------------
# Panel 2: ANNEX Step Function over Generations
# ---------------------------------------------------------------------------

def plot_annex_step_function(ax, df):
    conditions = [c for c in CONDITION_SHORT.keys() if c in df['Condition'].unique()]

    for cond in conditions:
        for shock_env in df['Environment'].unique():
            sub = df[(df['Condition'] == cond) & (df['Environment'] == shock_env)].sort_values('Generation')
            if len(sub) == 0:
                continue
            ax.step(
                sub['Generation'].values,
                sub['ANNEX'].values,
                where='post',
                color=CONDITION_COLORS.get(cond, '#888'),
                linewidth=1.5,
                alpha=0.7,
                label=f"{CONDITION_SHORT.get(cond, cond)}" if shock_env == df['Environment'].unique()[0] else None,
            )

    ax.set_xlabel('Generation', fontsize=9)
    ax.set_ylabel('ANNEX Count (Novel Envs Solved)', fontsize=9)
    ax.set_title('Panel 2: ANNEX Step Function Over Generations\n(Should NOT be flat 815 — look for step increases)', fontsize=10)
    ax.legend(fontsize=7, loc='upper left')
    ax.grid(alpha=0.3)


# ---------------------------------------------------------------------------
# Panel 3: Entropy vs Trajectory Diversity scatter
# ---------------------------------------------------------------------------

def plot_entropy_scatter(ax, df):
    final_df = df.groupby(['Condition', 'Environment']).last().reset_index()

    for _, row in final_df.iterrows():
        cond = row.get('Condition', '')
        verdict = row.get('EntropyVerdict', 'LOW_COMPLEXITY')
        entropy = float(row.get('ActionEntropy', 0))
        traj_div = float(row.get('TrajDiversity', 0))

        color = CONDITION_COLORS.get(cond, '#888')
        marker = VERDICT_MARKERS.get(verdict, 'o')

        ax.scatter(
            entropy, traj_div,
            c=color, marker=marker,
            s=80, alpha=0.85,
            edgecolors='white', linewidths=0.5,
        )

    # Legend: conditions
    cond_patches = [
        mpatches.Patch(color=CONDITION_COLORS.get(c, '#888'), label=CONDITION_SHORT.get(c, c))
        for c in CONDITION_SHORT if c in df['Condition'].unique()
    ]
    verdict_handles = [
        plt.Line2D([0], [0], marker=VERDICT_MARKERS[v], color='white',
                   markerfacecolor='#888', markersize=6, label=v, linestyle='None')
        for v in VERDICT_MARKERS
    ]
    ax.legend(handles=cond_patches + verdict_handles, fontsize=6.5, ncol=2)

    # Noise zone shading
    ax.axhline(1.5, color='#FF6B6B', linestyle=':', linewidth=1.0, alpha=0.6)
    ax.axvline(1.0, color='#FF6B6B', linestyle=':', linewidth=1.0, alpha=0.6)
    ax.text(0.5, 0.5, 'NOISE\nZONE', color='#FF6B6B', fontsize=8, alpha=0.5,
            transform=ax.transAxes, ha='center', va='center')

    ax.set_xlabel('Action Entropy (bits)', fontsize=9)
    ax.set_ylabel('Trajectory Diversity (DTW)', fontsize=9)
    ax.set_title('Panel 3: Entropy vs Trajectory Diversity\n(x: NOISE | o: GENUINE | s: LOW_COMPLEXITY)', fontsize=10)
    ax.grid(alpha=0.3)


# ---------------------------------------------------------------------------
# Panel 4: Phenotype Diversity by Condition
# ---------------------------------------------------------------------------

def plot_phenotype_diversity(ax, df):
    conditions = [c for c in CONDITION_SHORT.keys() if c in df['Condition'].unique()]
    final_df = df.groupby('Condition')['PhenotypeDiversity'].last()

    vals = [float(final_df.get(c, 0)) for c in conditions]
    colors = [CONDITION_COLORS.get(c, '#888') for c in conditions]
    labels = [CONDITION_SHORT.get(c, c) for c in conditions]

    bars = ax.barh(labels, vals, color=colors, alpha=0.9, edgecolor='#0D1117', linewidth=0.5)

    for bar, val in zip(bars, vals):
        ax.text(
            val + 0.001, bar.get_y() + bar.get_height() / 2,
            f'{val:.3f}', va='center', fontsize=8, color='#E6EDF3'
        )

    ax.set_xlabel('Phenotype Diversity (mean pairwise distance)', fontsize=9)
    ax.set_title('Panel 4: Phenotype Diversity by Condition\n(Higher = more behavioral variety; noise = low diversity)', fontsize=10)
    ax.grid(axis='x', alpha=0.3)
    ax.set_xlim(0, max(vals) * 1.2 if vals else 1.0)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', default=None, help='CSV file to plot')
    parser.add_argument('--output', default=None, help='Output PNG path')
    args = parser.parse_args()

    # Find input CSV
    if args.input:
        csv_path = args.input
    else:
        candidates = [
            os.path.join(root_dir, 'v6', 'results', 'phase3_results.csv'),
            os.path.join(root_dir, 'v6', 'results', 'phase3_calibration.csv'),
        ]
        csv_path = next((p for p in candidates if os.path.exists(p)), None)
        if csv_path is None:
            print('[ERROR] No phase3_results.csv found. Run run_v6_phase3.py first.')
            sys.exit(1)

    print(f'Loading: {csv_path}')
    df = pd.read_csv(csv_path)
    print(f'  {len(df)} rows | {df["Condition"].nunique()} conditions | '
          f'{df["Environment"].nunique()} environments | '
          f'Max gen: {df["Generation"].max()}')

    setup_style()
    fig = plt.figure(figsize=(18, 12), facecolor='#0D1117')
    gs = GridSpec(2, 2, figure=fig, hspace=0.42, wspace=0.32,
                  left=0.07, right=0.97, top=0.91, bottom=0.08)

    ax1 = fig.add_subplot(gs[0, 0])
    ax2 = fig.add_subplot(gs[0, 1])
    ax3 = fig.add_subplot(gs[1, 0])
    ax4 = fig.add_subplot(gs[1, 1])

    plot_survival_rate(ax1, df)
    plot_annex_step_function(ax2, df)
    plot_entropy_scatter(ax3, df)
    plot_phenotype_diversity(ax4, df)

    max_gen = df['Generation'].max()
    fig.suptitle(
        f'Genesis V6 Phase 3 — Fixed Metrics & Upgraded Transfer Shocks\n'
        f'(Max Gen: {max_gen} | Source: {os.path.basename(csv_path)})',
        fontsize=13, color='#E6EDF3', fontweight='bold', y=0.97
    )

    out_dir = os.path.join(root_dir, 'v6', 'results')
    os.makedirs(out_dir, exist_ok=True)

    if args.output:
        out_path = args.output
    else:
        tag = 'calibration' if 'calibration' in csv_path else 'full'
        out_path = os.path.join(out_dir, f'phase3_summary_{tag}.png')

    fig.savefig(out_path, dpi=160, bbox_inches='tight', facecolor='#0D1117')
    print(f'\n[SUCCESS] Plot saved: {out_path}')
    plt.close(fig)


if __name__ == '__main__':
    main()
