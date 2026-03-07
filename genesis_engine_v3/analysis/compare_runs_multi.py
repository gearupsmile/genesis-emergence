"""
Multi-Run Comparison Analysis
Aggregates results from multiple seeds, plots mean +/- 95% CI, and runs t-tests.
"""
import os
import argparse
import pandas as pd
import numpy as np
import glob
import scipy.stats as stats_lib

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def load_data(base_dir: str) -> pd.DataFrame:
    all_files = glob.glob(os.path.join(base_dir, "**", "*.csv"), recursive=True)
    if not all_files:
        print(f"Warning: No CSV files in {base_dir}")
        return pd.DataFrame()
    dfs = []
    for f in all_files:
        try:
            dfs.append(pd.read_csv(f))
        except Exception as e:
            print(f"Error reading {f}: {e}")
    return pd.concat(dfs, ignore_index=True) if dfs else pd.DataFrame()


def plot_ci(ax, df_r, df_s, col, title, ylabel, checkpoints):
    def agg(df):
        g = df.groupby('gen')[col]
        mn = g.mean()
        ci = 1.96 * g.std().fillna(0) / np.sqrt(g.count().clip(lower=1))
        return mn, ci

    rm, rc = agg(df_r)
    sm, sc = agg(df_s)

    ax.plot(rm.index, rm, color='steelblue', lw=1.8, label='Real')
    ax.fill_between(rm.index, rm - rc, rm + rc, color='steelblue', alpha=0.2)
    ax.plot(sm.index, sm, color='tomato', lw=1.8, ls='--', label='Sham')
    ax.fill_between(sm.index, sm - sc, sm + sc, color='tomato', alpha=0.2)
    for cp in checkpoints:
        ax.axvline(cp, color='grey', ls=':', alpha=0.4)
    ax.set_title(title); ax.set_ylabel(ylabel); ax.set_xlabel('Generation')
    ax.legend(); ax.grid(True, alpha=0.3)


def run_analysis(real_dir, sham_dir, output_file, stats_flag):
    print(f"Loading REAL  from {real_dir}...")
    df_r = load_data(real_dir)
    print(f"Loading SHAM  from {sham_dir}...")
    df_s = load_data(sham_dir)

    if df_r.empty or df_s.empty:
        print("ERROR: missing data"); return

    max_gen = min(df_r['gen'].max(), df_s['gen'].max())
    checkpoints = sorted({int(max_gen * p) for p in [0.1, 0.25, 0.5, 0.75, 1.0]})
    n_seeds_r = df_r['gen'].value_counts().max()
    print(f"Max gen: {max_gen} | ~{n_seeds_r} seeds per gen-checkpoint")

    cols_meta = [
        ('s_mean',       'Secretion Field (S)',              'Mean S'),
        ('avg_fitness',  'Avg Fitness (Resource Energy)',     'Energy'),
        ('avg_lz',       'Behavioral Complexity (LZ)',        'LZ Score'),
        ('archive_size', 'AIS Archive Size',                  'Entries'),
    ]

    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle(f'Real vs Sham — {max_gen:,} gens, {n_seeds_r} seeds  (95% CI shaded)',
                 fontsize=15, fontweight='bold')

    for (col, title, ylabel), ax in zip(cols_meta, axes.flat):
        if col in df_r.columns:
            plot_ci(ax, df_r, df_s, col, title, ylabel, checkpoints)
        else:
            ax.text(0.5, 0.5, f"'{col}' not in data", ha='center', va='center',
                    transform=ax.transAxes)

    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    plt.savefig(output_file, dpi=150)
    print(f"Plot saved -> {output_file}")

    if stats_flag:
        print("\n=== Statistical Analysis (Welch t-test) ===")
        for cp in checkpoints:
            print(f"\n  [Gen {cp:>6}]")
            for col, title, _ in cols_meta:
                if col not in df_r.columns:
                    continue
                rv = df_r[df_r['gen'] == cp][col].values
                sv = df_s[df_s['gen'] == cp][col].values
                if len(rv) < 2 or len(sv) < 2:
                    print(f"    {col:<16}: insufficient data"); continue
                _, p = stats_lib.ttest_ind(rv, sv, equal_var=False)
                sig = '**' if p < 0.05 else ('*' if p < 0.1 else '')
                print(f"    {col:<16}: Real={rv.mean():.4f}  Sham={sv.mean():.4f}"
                      f"  p={p:.3e} {sig}")
        print()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--real",   required=True)
    parser.add_argument("--sham",   required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--stats",  action='store_true')
    args = parser.parse_args()
    run_analysis(args.real, args.sham, args.output, args.stats)
