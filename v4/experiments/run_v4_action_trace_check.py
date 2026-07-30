"""
run_v4_action_trace_check.py
============================
Closes the loop that V3 opened: V3 showed action-trace LZ complexity stayed
identical between real and sham even though chemistry diverged (S_mean 0.48 vs 0.0).

This script runs the same check for V4 -- where genome size and species count
DO diverge between real and sham. The question is whether that structural
divergence is functional (LZ diverges) or neutral (LZ stays flat).

Conditions:
  REAL:  V4 agents (CPPN/NEAT) in active Gray-Scott chemistry.
         Substrate steps each generation; V field evolves dynamically.
         Chemistry signal is alive -- agents can exploit spatial gradients.

  SHAM:  V4 agents in a FROZEN substrate.
         U=1, V=0 everywhere; substrate.step() is NEVER called.
         Agents receive no spatial chemistry signal -- pure random walk.
         Structural mutation (NEAT) still operates identically.

This is the exact analogue of the V3 sham control.

Seeds: 42, 123 (matching V3 validation runs)
Generations: 500 (matching V3 500-gen validation)
LZ computed from 100-step action traces every 50 generations.

Output:
  v4/results/action_trace_real_seed42.csv
  v4/results/action_trace_real_seed123.csv
  v4/results/action_trace_sham_seed42.csv
  v4/results/action_trace_sham_seed123.csv
  v4/results/v4_action_trace_lz_plot.png
  v4/results/v4_action_trace_report.txt
"""

import sys
import os
import csv
import random
import zlib
import numpy as np
from scipy.stats import mannwhitneyu

root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if root_dir not in sys.path:
    sys.path.append(root_dir)

from genesis_engine_v3.engine.structurally_evolvable_agent import AgentV4
from v5.src.cppn_environment import V5Substrate


# -----------------------------------------------------------------------
# LZ76 -- same implementation as v5/src/metrics.py (zlib compression ratio)
# -----------------------------------------------------------------------

def lz76(s: str) -> float:
    """Normalized LZ complexity via zlib compression ratio."""
    if not s:
        return 0.0
    b = s.encode('utf-8')
    if len(b) == 0:
        return 0.0
    return min(1.0, len(zlib.compress(b)) / len(b))


def get_action_trace(agent: AgentV4, substrate, steps: int = 100) -> str:
    """
    Run a clone of the agent for `steps` steps and return its action string.
    Uses a clone so as not to alter the live agent's state.
    """
    clone = AgentV4(agent.x, agent.y, agent.genome.copy())
    clone.energy = 1.0
    trace = []
    for _ in range(steps):
        action = clone.step(substrate)
        trace.append(action if action else 'I')
    return ''.join(trace)


def make_real_substrate(width: int, height: int, seed: int) -> V5Substrate:
    """Active Gray-Scott substrate -- chemistry is alive."""
    rng = np.random.RandomState(seed)
    f_map = np.full((height, width), 0.055, dtype=np.float32)
    k_map = np.full((height, width), 0.062, dtype=np.float32)
    u_map = rng.uniform(0.5, 1.0, (height, width)).astype(np.float32)
    v_map = rng.uniform(0.0, 0.5, (height, width)).astype(np.float32)
    return V5Substrate(width, height, f_map, k_map, u_map, v_map)


def make_sham_substrate(width: int, height: int) -> V5Substrate:
    """
    Frozen substrate -- U=1, V=0 everywhere, never stepped.
    Agents receive zero spatial gradient signal.
    This is the exact analogue of the V3 sham control.
    """
    f_map = np.full((height, width), 0.055, dtype=np.float32)
    k_map = np.full((height, width), 0.062, dtype=np.float32)
    u_map = np.ones((height, width), dtype=np.float32)
    v_map = np.zeros((height, width), dtype=np.float32)
    return V5Substrate(width, height, f_map, k_map, u_map, v_map)


# -----------------------------------------------------------------------
# Single condition run
# -----------------------------------------------------------------------

def run_condition(
    seed: int,
    condition: str,   # 'real' or 'sham'
    generations: int = 500,
    log_interval: int = 50,
    pop_size: int = 20,
    width: int = 50,
    height: int = 50,
    trace_steps: int = 100,
) -> list:
    """
    Run one condition (real or sham) and return list of log dicts.
    """
    random.seed(seed)
    np.random.seed(seed)

    is_sham = (condition == 'sham')

    substrate = (make_sham_substrate(width, height)
                 if is_sham else make_real_substrate(width, height, seed))

    population = [
        AgentV4(random.randint(0, width-1), random.randint(0, height-1))
        for _ in range(pop_size)
    ]

    logs = []

    print(f'  [{condition.upper()} seed={seed}] Starting {generations} gens '
          f'(log every {log_interval})', flush=True)

    for gen in range(1, generations + 1):
        # 20 micro-steps per generation (matching V4 baseline runner)
        for _ in range(20):
            if not is_sham:
                substrate.step()          # Real: chemistry evolves
            # Sham: substrate.step() never called -> chemistry frozen
            for agent in population:
                agent.step(substrate)
                agent.energy += float(
                    substrate.V[int(agent.y) % height, int(agent.x) % width]
                ) * 0.5

        # Selection
        population.sort(key=lambda a: a.energy, reverse=True)
        survivors = population[:pop_size // 2]
        for a in survivors:
            a.energy = min(1.0, max(0.0, a.energy + 0.2))
            a.x = (a.x + random.choice([-1, 0, 1])) % width
            a.y = (a.y + random.choice([-1, 0, 1])) % height

        new_pop = list(survivors)
        while len(new_pop) < pop_size:
            new_pop.append(random.choice(survivors).reproduce())
        population = new_pop

        if gen % log_interval == 0 or gen == generations:
            lz_scores = []
            nodes_list, edges_list, species_set = [], [], set()

            for agent in population:
                trace = get_action_trace(agent, substrate, steps=trace_steps)
                lz_scores.append(lz76(trace))
                nodes_list.append(len(agent.genome.nodes))
                edges_list.append(len(agent.genome.connections))
                # Species proxy: round avg weight to 1 decimal
                species_set.add(round(
                    sum(c.weight for c in agent.genome.connections.values()) /
                    max(1, len(agent.genome.connections)), 1
                ))

            avg_lz    = float(np.mean(lz_scores))
            std_lz    = float(np.std(lz_scores))
            avg_nodes = float(np.mean(nodes_list))
            avg_edges = float(np.mean(edges_list))
            num_species = len(species_set)

            row = {
                'gen':         gen,
                'condition':   condition,
                'seed':        seed,
                'avg_lz':      round(avg_lz, 6),
                'std_lz':      round(std_lz, 6),
                'avg_nodes':   round(avg_nodes, 3),
                'avg_edges':   round(avg_edges, 3),
                'num_species': num_species,
            }
            logs.append(row)

            print(f'    Gen {gen:04d} | LZ: {avg_lz:.4f} +/- {std_lz:.4f} | '
                  f'Nodes: {avg_nodes:.1f} | Edges: {avg_edges:.1f} | '
                  f'Species proxy: {num_species}',
                  flush=True)

    return logs


# -----------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------

def main():
    output_dir = os.path.join(root_dir, 'v4', 'results')
    os.makedirs(output_dir, exist_ok=True)

    seeds      = [42, 123]
    conditions = ['real', 'sham']
    all_logs   = {}

    print('=' * 65)
    print(' V4 Action-Trace LZ76 Check: Real vs Sham')
    print(' Closing the loop opened by V3 sham control.')
    print(' V3 result: LZ76 identical (0.068) despite chemistry divergence.')
    print(' V4 question: Does structural divergence correspond to LZ divergence?')
    print('=' * 65)

    for seed in seeds:
        for cond in conditions:
            print(f'\n--- Seed {seed} | Condition: {cond.upper()} ---')
            logs = run_condition(seed=seed, condition=cond)
            all_logs[(seed, cond)] = logs

            csv_path = os.path.join(output_dir,
                                    f'action_trace_{cond}_seed{seed}.csv')
            with open(csv_path, 'w', newline='') as f:
                w = csv.DictWriter(f, fieldnames=list(logs[0].keys()))
                w.writeheader()
                w.writerows(logs)
            print(f'  Saved: {csv_path}')

    # -------------------------------------------------------------------
    # Statistical comparison (final generation, both seeds pooled)
    # -------------------------------------------------------------------
    real_lz_final, sham_lz_final = [], []
    for seed in seeds:
        # Use all logged LZ values (not just final gen) for richer comparison
        real_lz_final.extend([r['avg_lz'] for r in all_logs[(seed, 'real')]])
        sham_lz_final.extend([r['avg_lz'] for r in all_logs[(seed, 'sham')]])

    real_final_only = [all_logs[(s, 'real')][-1]['avg_lz'] for s in seeds]
    sham_final_only = [all_logs[(s, 'sham')][-1]['avg_lz'] for s in seeds]

    stat, pval = mannwhitneyu(real_lz_final, sham_lz_final,
                              alternative='two-sided')

    real_mean = float(np.mean(real_final_only))
    sham_mean = float(np.mean(sham_final_only))
    delta     = real_mean - sham_mean
    diverged  = abs(delta) > 0.05 and pval < 0.05

    # -------------------------------------------------------------------
    # Report
    # -------------------------------------------------------------------
    report_lines = [
        'V4 Action-Trace LZ76 Check: Real vs Sham',
        '=' * 55,
        '',
        'Background:',
        '  V3 showed: LZ76 = 0.068 +/- 0.000 for BOTH real and sham.',
        '  Structural divergence existed in V3 (genome size, species)',
        '  but action traces were identical -- neutral complexification.',
        '',
        '  V4 shows structural divergence (nodes + species count increase).',
        '  Question: Is the V4 structural divergence FUNCTIONAL or NEUTRAL?',
        '',
        'Protocol:',
        '  Real: AgentV4 + active Gray-Scott (substrate.step() each gen)',
        '  Sham: AgentV4 + frozen substrate (U=1, V=0, never stepped)',
        '  Seeds: 42, 123 | Gens: 500 | LZ trace: 100 steps per agent',
        '',
        'Results:',
    ]

    for seed in seeds:
        r = all_logs[(seed, 'real')]
        s = all_logs[(seed, 'sham')]
        report_lines += [
            f'  Seed {seed}:',
            f'    Real  -- LZ final: {r[-1]["avg_lz"]:.4f} | '
            f'Nodes: {r[-1]["avg_nodes"]:.1f} | Edges: {r[-1]["avg_edges"]:.1f}',
            f'    Sham  -- LZ final: {s[-1]["avg_lz"]:.4f} | '
            f'Nodes: {s[-1]["avg_nodes"]:.1f} | Edges: {s[-1]["avg_edges"]:.1f}',
        ]

    report_lines += [
        '',
        'Statistical Test (Mann-Whitney U, pooled across seeds and timepoints):',
        f'  Real LZ mean: {float(np.mean(real_lz_final)):.4f}',
        f'  Sham LZ mean: {float(np.mean(sham_lz_final)):.4f}',
        f'  Delta (real - sham): {delta:+.4f}',
        f'  U statistic: {stat:.1f}',
        f'  p-value: {pval:.4f}',
        '',
        'VERDICT:',
    ]

    if diverged:
        verdict = 'FUNCTIONAL'
        report_lines += [
            f'  V4 action traces DIVERGE between real and sham (p={pval:.4f}).',
            f'  Delta = {delta:+.4f}.',
            '  The V4 structural divergence (genome size, species count)',
            '  CORRESPONDS to genuine policy divergence.',
            '  Interpretation: CPPN + speciation unlocks functional',
            '  behavioural complexification, not just neutral genotype bloat.',
        ]
    else:
        verdict = 'NEUTRAL'
        report_lines += [
            f'  V4 action traces DO NOT diverge (p={pval:.4f}, delta={delta:+.4f}).',
            '  The V4 structural divergence (genome size, species count)',
            '  is NEUTRAL -- genotype complexifies without policy change.',
            '  Interpretation: Structure-function lag persists in V4.',
            '  CPPN developmental encoding does not escape neutral complexification.',
            '',
            '  This matches the V3 result: structural divergence without',
            '  corresponding behavioural divergence.',
        ]

    report_lines += [
        '',
        f'Summary: V4 action traces [{("DO" if diverged else "do NOT")}] '
        f'diverge between real and sham conditions.',
    ]

    report_text = '\n'.join(report_lines)
    print('\n' + report_text)

    report_path = os.path.join(output_dir, 'v4_action_trace_report.txt')
    with open(report_path, 'w') as f:
        f.write(report_text)

    # -------------------------------------------------------------------
    # Plot
    # -------------------------------------------------------------------
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        from matplotlib.gridspec import GridSpec

        plt.rcParams.update({
            'figure.facecolor': '#0D1117', 'axes.facecolor': '#161B22',
            'axes.edgecolor': '#30363D', 'axes.labelcolor': '#E6EDF3',
            'xtick.color': '#8B949E', 'ytick.color': '#8B949E',
            'text.color': '#E6EDF3', 'grid.color': '#21262D',
            'grid.alpha': 0.5, 'font.family': 'DejaVu Sans',
        })

        fig = plt.figure(figsize=(16, 10), facecolor='#0D1117')
        gs  = GridSpec(2, 2, figure=fig, hspace=0.45, wspace=0.32,
                       left=0.08, right=0.96, top=0.88, bottom=0.09)

        colors = {'real': '#4CC9F0', 'sham': '#F72585'}
        seed_markers = {42: 'o', 123: 's'}

        # Panel 1 & 2: LZ over generations (one per seed)
        for pi, seed in enumerate(seeds):
            ax = fig.add_subplot(gs[0, pi])
            for cond in ['real', 'sham']:
                logs = all_logs[(seed, cond)]
                gens   = [r['gen'] for r in logs]
                lz_avg = [r['avg_lz'] for r in logs]
                lz_std = [r['std_lz'] for r in logs]
                ax.plot(gens, lz_avg, color=colors[cond],
                        linewidth=2.0, marker=seed_markers[seed],
                        markersize=5, label=cond.capitalize())
                ax.fill_between(
                    gens,
                    [m - s for m, s in zip(lz_avg, lz_std)],
                    [m + s for m, s in zip(lz_avg, lz_std)],
                    color=colors[cond], alpha=0.15
                )
            ax.set_title(f'Seed {seed}: LZ76 Action-Trace Complexity', fontsize=10)
            ax.set_xlabel('Generation', fontsize=9)
            ax.set_ylabel('LZ76 Complexity (compression ratio)', fontsize=9)
            ax.legend(fontsize=8)
            ax.grid(alpha=0.3)
            # Annotate verdict
            ax.text(0.05, 0.92, f'V3 baseline: 0.068 (identical)',
                    transform=ax.transAxes, fontsize=7.5,
                    color='#8B949E', style='italic')

        # Panel 3: Genome size over generations (both seeds, both conditions)
        ax3 = fig.add_subplot(gs[1, 0])
        for seed in seeds:
            for cond in ['real', 'sham']:
                logs = all_logs[(seed, cond)]
                gens  = [r['gen'] for r in logs]
                nodes = [r['avg_nodes'] for r in logs]
                ls = '-' if cond == 'real' else '--'
                ax3.plot(gens, nodes, color=colors[cond],
                         linestyle=ls, linewidth=1.5,
                         marker=seed_markers[seed], markersize=4,
                         label=f'{cond} s{seed}')
        ax3.set_title('Avg Node Count (structural divergence check)', fontsize=10)
        ax3.set_xlabel('Generation', fontsize=9)
        ax3.set_ylabel('Average Nodes per Agent', fontsize=9)
        ax3.legend(fontsize=7, ncol=2)
        ax3.grid(alpha=0.3)

        # Panel 4: Final-gen comparison box/bar
        ax4 = fig.add_subplot(gs[1, 1])
        bar_data = {
            'Real s42': all_logs[(42, 'real')][-1]['avg_lz'],
            'Sham s42': all_logs[(42, 'sham')][-1]['avg_lz'],
            'Real s123': all_logs[(123, 'real')][-1]['avg_lz'],
            'Sham s123': all_logs[(123, 'sham')][-1]['avg_lz'],
        }
        bar_colors = [colors['real'], colors['sham'],
                      colors['real'], colors['sham']]
        bars = ax4.bar(range(len(bar_data)), list(bar_data.values()),
                       color=bar_colors, alpha=0.85,
                       edgecolor='#0D1117', linewidth=0.5)
        for bar, val in zip(bars, bar_data.values()):
            ax4.text(bar.get_x() + bar.get_width()/2,
                     bar.get_height() + 0.002,
                     f'{val:.4f}', ha='center', va='bottom', fontsize=8)
        ax4.set_xticks(range(len(bar_data)))
        ax4.set_xticklabels(list(bar_data.keys()), fontsize=8, rotation=15)
        ax4.set_ylabel('LZ76 (final gen)', fontsize=9)
        ax4.set_title(
            f'Final-gen LZ76 Comparison\nVerdict: {verdict} '
            f'(p={pval:.3f}, delta={delta:+.4f})', fontsize=10
        )
        ax4.axhline(0.068, color='#F77F00', linestyle='--',
                    linewidth=1.0, alpha=0.7, label='V3 baseline (0.068)')
        ax4.legend(fontsize=8)
        ax4.grid(axis='y', alpha=0.3)

        fig.suptitle(
            'V4 Action-Trace LZ76 Check: Real vs Sham\n'
            f'Verdict: {verdict} | p={pval:.4f} | '
            f'Real={real_mean:.4f} | Sham={sham_mean:.4f}',
            fontsize=12, color='#E6EDF3', fontweight='bold', y=0.95
        )

        plot_path = os.path.join(output_dir, 'v4_action_trace_lz_plot.png')
        fig.savefig(plot_path, dpi=150, bbox_inches='tight',
                    facecolor='#0D1117')
        plt.close(fig)
        print(f'\n[SUCCESS] Plot saved: {plot_path}')
    except Exception as e:
        print(f'\n[WARNING] Plot failed: {e}')

    print(f'\n[SUCCESS] Report saved: {report_path}')
    print(f'\nVERDICT: {verdict}')


if __name__ == '__main__':
    main()
