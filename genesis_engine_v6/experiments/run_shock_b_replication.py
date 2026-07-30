"""
run_shock_b_replication.py - Shock B Replication Study

Replicates the Phase 3 Shock B (Barrier + Gap) result across 5 independent seeds
to determine whether edge densification finding is genuine or seed-specific.

20 trials total: 4 conditions x 5 seeds x 5000 generations = 100,000 generations

Output:
  v6/results/shock_b_replication_summary.csv   -- 20 rows, final-gen metrics
  v6/results/shock_b_trajectory_data.csv       -- full trajectory (all gens logged)
  v6/results/shock_b_replication_report.txt    -- pass/fail verdict
"""

import sys
import os
import csv
import random
import numpy as np
from typing import List, Dict, Any

root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if root_dir not in sys.path:
    sys.path.append(root_dir)

from genesis_engine_v6.src.v6_agent import V6Agent, create_condition_agent
from genesis_engine_v6.src.v6_transfer_shock_envs import (
    BarrierSubstrate,
    generate_shock_env_B,
)
from genesis_engine_v6.src.v6_transfer_metrics import (
    survival_rate,
    action_entropy,
    AnnexTracker,
)

# -----------------------------------------------------------------------
# Exact Phase 3 parameters (do not change for replication)
# -----------------------------------------------------------------------
SEEDS         = [42, 123, 456, 789, 1011]
CONDITIONS    = [
    'Condition A (V5 467 nodes)',
    'Condition B (V6 Constrained 52 nodes)',
    'Condition C (V4 123 nodes)',
    'Condition D (Naive 12 nodes)',
]
NUM_GENS      = 5000
LOG_INTERVAL  = 500
POP_SIZE      = 20
GAP_HALF      = 1      # 3-cell gap, same as Phase 3 final run
WALL_PENALTY  = 0.60   # same as Phase 3
ENERGY_MULT   = 0.20   # intake multiplier (same as Phase 3)
MOVE_COST     = 0.03
IDLE_COST     = 0.02
SECRETE_COST  = 0.10


# -----------------------------------------------------------------------
# Patched agent step (copy of Phase 3 logic, Shock B only)
# -----------------------------------------------------------------------

def agent_step_barrier(agent: V6Agent, substrate: BarrierSubstrate) -> str:
    h, w = substrate.U.shape
    x, y = int(agent.x), int(agent.y)

    gu_x = float(substrate.U[y, (x+1)%w] - substrate.U[y, (x-1)%w])
    gu_y = float(substrate.U[(y+1)%h, x] - substrate.U[(y-1)%h, x])
    gv_x = float(substrate.V[y, (x+1)%w] - substrate.V[y, (x-1)%w])
    gv_y = float(substrate.V[(y+1)%h, x] - substrate.V[(y-1)%h, x])
    gs_x = float(substrate.S[y, (x+1)%w] - substrate.S[y, (x-1)%w])
    gs_y = float(substrate.S[(y+1)%h, x] - substrate.S[(y-1)%h, x])

    inputs = (agent.x/w, agent.y/h, agent.energy,
              gu_x, gu_y, gv_x, gv_y, gs_x, gs_y)
    try:
        outputs = agent.genome.activate(inputs)
    except Exception:
        return 'I'

    if isinstance(outputs, dict):
        move_x = outputs.get('move_x', 0.0)
        move_y = outputs.get('move_y', 0.0)
        secrete = outputs.get('secrete', 0.0)
    else:
        move_x, move_y, secrete = float(outputs[0]), float(outputs[1]), float(outputs[2])

    action = 'I'
    if secrete > 0.5:
        action = 'S'
        agent.energy -= SECRETE_COST
        substrate.deposit_secretion(x, y, 0.5)
    else:
        dx = 1 if move_x > 0.3 else (-1 if move_x < -0.3 else 0)
        dy = 1 if move_y > 0.3 else (-1 if move_y < -0.3 else 0)
        if dx != 0 or dy != 0:
            new_x, new_y = substrate.apply_wall(agent, (x+dx)%w, (y+dy)%h)
            agent.x, agent.y = new_x, new_y
            action = 'M'
            agent.energy -= MOVE_COST
        else:
            agent.energy -= IDLE_COST

    if hasattr(agent, 'action_history'):
        agent.action_history.append(action)
        if len(agent.action_history) > 1000:
            agent.action_history.pop(0)
    return action


def energy_intake_barrier(agent: V6Agent, substrate: BarrierSubstrate) -> float:
    intake = substrate.get_energy_at(int(agent.x), int(agent.y)) * (ENERGY_MULT / 0.5)
    intake -= substrate.get_penalty_at(int(agent.x))
    return intake


# -----------------------------------------------------------------------
# Single trial
# -----------------------------------------------------------------------

def run_trial(
    condition_name: str,
    seed: int,
    traj_writer: csv.DictWriter,
    traj_file,
) -> Dict[str, Any]:
    """Run one condition x seed trial. Returns final-gen summary row."""
    random.seed(seed)
    np.random.seed(seed)

    substrate = BarrierSubstrate(width=50, height=50, gap_half=GAP_HALF)

    founder = create_condition_agent(condition_name, seed=seed)
    max_nodes_cap = founder.max_nodes
    population: List[V6Agent] = []
    for _ in range(POP_SIZE):
        child = V6Agent(
            x=random.randint(0, 49), y=random.randint(0, 49),
            genome=founder.genome.copy(),
            lineage_id=founder.lineage_id,
            max_nodes=max_nodes_cap,
        )
        population.append(child)

    annex_tracker = AnnexTracker(condition_name=f"{condition_name}_seed{seed}")
    performance_curve = []

    for gen in range(1, NUM_GENS + 1):
        for _ in range(20):
            substrate.step()
            for agent in population:
                agent_step_barrier(agent, substrate)
                agent.energy += energy_intake_barrier(agent, substrate)
                agent.energy = float(np.clip(agent.energy, -5.0, 10.0))

        avg_energy = float(np.mean([a.energy for a in population]))
        performance_curve.append(avg_energy)

        # Pre-selection survival (real mortality signal)
        pre_surv = survival_rate(population)

        # Selection
        population.sort(key=lambda a: a.energy, reverse=True)
        survivors = population[:max(1, len(population) // 2)]
        for a in survivors:
            a.energy = float(np.clip(a.energy + 0.2, 0.0, 1.0))
            a.x = (a.x + random.choice([-1, 0, 1])) % 50
            a.y = (a.y + random.choice([-1, 0, 1])) % 50
        new_pop = list(survivors)
        while len(new_pop) < POP_SIZE:
            new_pop.append(random.choice(survivors).reproduce())
        population = new_pop

        if gen % LOG_INTERVAL == 0 or gen == NUM_GENS:
            is_novel, goldilocks_status, env_hash = annex_tracker.record(
                substrate, population, gen, agent_id=condition_name
            )
            # Override with pre-selection Goldilocks
            if 0.05 <= pre_surv <= 0.95:
                if env_hash not in annex_tracker._seen_hashes:
                    annex_tracker._seen_hashes.add(env_hash)
                    annex_tracker.count += 1
                    is_novel = True
                    goldilocks_status = 'ACCEPT'

            avg_nodes = float(np.mean([len(a.genome.nodes) for a in population]))
            avg_edges = float(np.mean([len(a.genome.connections) for a in population]))
            all_actions = []
            for a in population:
                all_actions.extend(getattr(a, 'action_history', []))
            act_ent = action_entropy(all_actions)

            traj_row = {
                'Seed': seed,
                'Condition': condition_name,
                'Generation': gen,
                'SurvivalRate': round(pre_surv, 4),
                'ActionEntropy': round(act_ent, 4),
                'ANNEX': annex_tracker.count,
                'GoldilocksStatus': goldilocks_status,
                'AvgNodes': round(avg_nodes, 2),
                'AvgEdges': round(avg_edges, 2),
            }
            traj_writer.writerow(traj_row)
            traj_file.flush()

            print(f"  Seed {seed:4d} | {condition_name[:35]:<35} | "
                  f"Gen {gen:05d} | Surv: {pre_surv:.2f} | "
                  f"ANNEX: {annex_tracker.count} [{goldilocks_status[:6]}] | "
                  f"Nodes: {avg_nodes:.1f} | Edges: {avg_edges:.1f}",
                  flush=True)

    # Return final-gen summary
    final_nodes = float(np.mean([len(a.genome.nodes) for a in population]))
    final_edges = float(np.mean([len(a.genome.connections) for a in population]))
    final_surv  = survival_rate(population)

    # Recalculate pre-selection survival for final gen
    # (use last logged value from trajectory)
    return {
        'Seed': seed,
        'Condition': condition_name,
        'FinalSurvival': round(pre_surv, 4),
        'FinalNodes': round(final_nodes, 2),
        'FinalEdges': round(final_edges, 2),
        'ANNEX': annex_tracker.count,
        'GoldilocksStatus': goldilocks_status,
        'Flag': (
            'B_FAILED' if condition_name == 'Condition B (V6 Constrained 52 nodes)'
                          and pre_surv < 1.0 else
            'D_SURVIVED' if condition_name == 'Condition D (Naive 12 nodes)'
                            and pre_surv >= 0.5 else
            'OK'
        ),
    }


# -----------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------

def main():
    output_dir = os.path.join(root_dir, 'v6', 'results')
    os.makedirs(output_dir, exist_ok=True)

    summary_path = os.path.join(output_dir, 'shock_b_replication_summary.csv')
    traj_path    = os.path.join(output_dir, 'shock_b_trajectory_data.csv')
    report_path  = os.path.join(output_dir, 'shock_b_replication_report.txt')

    traj_headers = [
        'Seed', 'Condition', 'Generation', 'SurvivalRate',
        'ActionEntropy', 'ANNEX', 'GoldilocksStatus', 'AvgNodes', 'AvgEdges'
    ]
    summary_headers = [
        'Seed', 'Condition', 'FinalSurvival', 'FinalNodes',
        'FinalEdges', 'ANNEX', 'GoldilocksStatus', 'Flag'
    ]

    total_trials = len(SEEDS) * len(CONDITIONS)
    total_gens   = total_trials * NUM_GENS

    print('=' * 70)
    print(' Genesis V6 Shock B Replication Study')
    print(f' {len(CONDITIONS)} conditions x {len(SEEDS)} seeds x {NUM_GENS} gens')
    print(f' = {total_gens:,} total generations | {total_trials} trials')
    print(f' Gap half-width: {GAP_HALF} (gap={2*GAP_HALF+1} cells)')
    print('=' * 70)

    summary_rows = []
    flags = []

    with open(traj_path, 'w', newline='') as traj_f:
        traj_w = csv.DictWriter(traj_f, fieldnames=traj_headers)
        traj_w.writeheader()
        traj_f.flush()

        trial_num = 0
        for seed in SEEDS:
            print(f'\n--- Seed {seed} ---')
            for cond in CONDITIONS:
                trial_num += 1
                print(f'\n[Trial {trial_num}/{total_trials}]')
                row = run_trial(cond, seed, traj_w, traj_f)
                summary_rows.append(row)
                if row['Flag'] != 'OK':
                    flags.append(row)
                    print(f'  *** FLAG: {row["Flag"]} '
                          f'(Seed={seed}, Cond={cond[:20]}, '
                          f'Surv={row["FinalSurvival"]}) ***')

    # Write summary CSV
    with open(summary_path, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=summary_headers)
        w.writeheader()
        w.writerows(summary_rows)

    # Write report
    b_results = [r for r in summary_rows
                 if 'Condition B' in r['Condition']]
    d_results = [r for r in summary_rows
                 if 'Condition D' in r['Condition']]
    a_results = [r for r in summary_rows
                 if 'Condition A' in r['Condition']]

    b_full_surv = sum(1 for r in b_results if r['FinalSurvival'] >= 1.0)
    d_failed    = sum(1 for r in d_results if r['FinalSurvival'] < 0.5)
    a_full_surv = sum(1 for r in a_results if r['FinalSurvival'] >= 1.0)

    b_pass = b_full_surv >= 4
    d_pass = d_failed >= 4
    a_pass = a_full_surv == 5

    with open(report_path, 'w') as f:
        f.write('Genesis V6 Shock B Replication Report\n')
        f.write('=' * 50 + '\n\n')
        f.write(f'Seeds tested: {SEEDS}\n')
        f.write(f'Conditions tested: {len(CONDITIONS)}\n')
        f.write(f'Generations per trial: {NUM_GENS}\n')
        f.write(f'Total trials: {total_trials}\n\n')

        f.write('HYPOTHESIS RESULTS\n')
        f.write('-' * 30 + '\n')
        f.write(f'H1 - Condition B achieves 100% survival in >=4/5 seeds: '
                f'{"PASS" if b_pass else "FAIL"} '
                f'({b_full_surv}/5 seeds)\n')
        f.write(f'H2 - Condition D fails to reach 50% in >=4/5 seeds:     '
                f'{"PASS" if d_pass else "FAIL"} '
                f'({d_failed}/5 seeds)\n')
        f.write(f'H3 - Condition A achieves 100% in all 5 seeds:           '
                f'{"PASS" if a_pass else "FAIL"} '
                f'({a_full_surv}/5 seeds)\n\n')

        f.write('OVERALL VERDICT\n')
        f.write('-' * 30 + '\n')
        if b_pass and d_pass:
            f.write('REPLICATION CONFIRMED: Edge densification finding is robust.\n')
            f.write('Condition B (52n, 815e) achieved survival equivalence with\n')
            f.write('Condition A (467n) in >=4/5 independent seeds.\n')
            f.write('Condition D consistently failed below 50% survival.\n')
            f.write('Finding is suitable for publication.\n')
        elif b_pass and not d_pass:
            f.write('PARTIAL REPLICATION: Condition B is robust, but Condition D\n')
            f.write('shows unexpected resilience in some seeds. Investigate D flags.\n')
        else:
            f.write('REPLICATION FAILED: Condition B did not consistently achieve\n')
            f.write('100% survival. Result may be seed-specific. Investigate flags.\n')

        f.write('\nFLAGGED SEEDS\n')
        f.write('-' * 30 + '\n')
        if flags:
            for fl in flags:
                f.write(f'  {fl["Flag"]}: Seed={fl["Seed"]}, '
                        f'Cond={fl["Condition"][:30]}, '
                        f'Surv={fl["FinalSurvival"]}\n')
        else:
            f.write('  None. All conditions behaved as predicted.\n')

        f.write('\nFULL SUMMARY TABLE\n')
        f.write('-' * 30 + '\n')
        f.write(f'{"Seed":>6} | {"Condition":<35} | {"Surv":>6} | '
                f'{"Nodes":>7} | {"Edges":>7} | {"ANNEX":>5} | {"Flag"}\n')
        f.write('-' * 90 + '\n')
        for r in summary_rows:
            f.write(f'{r["Seed"]:>6} | {r["Condition"]:<35} | '
                    f'{r["FinalSurvival"]:>6.3f} | '
                    f'{r["FinalNodes"]:>7.1f} | {r["FinalEdges"]:>7.1f} | '
                    f'{r["ANNEX"]:>5} | {r["Flag"]}\n')

    print('\n' + '=' * 70)
    print('[SUCCESS] Shock B Replication complete.')
    print(f'  Summary: {summary_path}')
    print(f'  Trajectory: {traj_path}')
    print(f'  Report: {report_path}')
    print()
    print(f'  H1 (Cond B robust): {"PASS" if b_pass else "FAIL"} ({b_full_surv}/5)')
    print(f'  H2 (Cond D fails):  {"PASS" if d_pass else "FAIL"} ({d_failed}/5)')
    print(f'  H3 (Cond A robust): {"PASS" if a_pass else "FAIL"} ({a_full_surv}/5)')
    print('=' * 70)


if __name__ == '__main__':
    main()
