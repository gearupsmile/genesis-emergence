"""
run_v6_phase3.py - Genesis V6 Phase 3: Fixed Metrics & Upgraded Transfer Shocks

Implements three corrected experiments:
  FIX #1: ANNEX decoupled from edge count (AnnexTracker, environment hashes)
  FIX #2: Action entropy cross-validated with trajectory + phenotype diversity
  FIX #3: Qualitatively different transfer shocks (Pressure Wave, Barrier, Sensor Blinding)

Usage:
    # Full run (5000 gens × 4 conditions × 3 shocks = 60,000 gens):
    python genesis_engine_v6/experiments/run_v6_phase3.py

    # Calibration test (500 gens — fast validation before full run):
    python genesis_engine_v6/experiments/run_v6_phase3.py --calibrate

    # Custom gens:
    python genesis_engine_v6/experiments/run_v6_phase3.py --gens 2000
"""

import sys
import os
import csv
import json
import random
import argparse
import datetime
import numpy as np
from typing import List, Dict, Any, Optional

# Ensure project root is on sys.path
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if root_dir not in sys.path:
    sys.path.append(root_dir)

from genesis_engine_v6.src.v6_agent import V6Agent, create_condition_agent
from genesis_engine_v6.src.v6_transfer_shock_envs import (
    PressureWaveSubstrate, generate_shock_env_A,
    BarrierSubstrate, generate_shock_env_B,
    SensorBlindingSubstrate, generate_shock_env_C,
)
from genesis_engine_v6.src.v6_transfer_metrics import (
    adaptation_speed,
    survival_rate,
    action_entropy,
    energy_efficiency,
    AnnexTracker,
)
from genesis_engine_v6.src.v6_behavioral_metrics import BehavioralMetrics


# ---------------------------------------------------------------------------
# Substrate factory
# ---------------------------------------------------------------------------

def build_substrate(shock_spec: Dict[str, Any], width: int = 50, height: int = 50):
    """Instantiate the correct substrate class from a shock spec dict."""
    sc = shock_spec.get('substrate_class', '')
    if sc == 'PressureWaveSubstrate':
        return PressureWaveSubstrate(width=width, height=height)
    elif sc == 'BarrierSubstrate':
        gap_half = shock_spec.get('gap_half', 3)
        return BarrierSubstrate(width=width, height=height, gap_half=gap_half)
    elif sc == 'SensorBlindingSubstrate':
        return SensorBlindingSubstrate(width=width, height=height)
    else:
        raise ValueError(f"Unknown substrate_class: {sc!r}")


# ---------------------------------------------------------------------------
# Patched agent step for special substrates
# ---------------------------------------------------------------------------

def agent_step_on_substrate(agent: V6Agent, substrate) -> str:
    """
    Execute one agent step, adapting to substrate type.

    - PressureWaveSubstrate: agent reads pressure gradients from U field.
    - BarrierSubstrate: wall collision logic applied before move commit.
    - SensorBlindingSubstrate: sensory dropout applied before CPPN activation.
    """
    h, w = substrate.U.shape
    x, y = int(agent.x), int(agent.y)

    # Compute raw gradients
    gu_x = float(substrate.U[y, (x + 1) % w] - substrate.U[y, (x - 1) % w])
    gu_y = float(substrate.U[(y + 1) % h, x] - substrate.U[(y - 1) % h, x])
    gv_x = float(substrate.V[y, (x + 1) % w] - substrate.V[y, (x - 1) % w])
    gv_y = float(substrate.V[(y + 1) % h, x] - substrate.V[(y - 1) % h, x])
    gs_x = float(substrate.S[y, (x + 1) % w] - substrate.S[y, (x - 1) % w])
    gs_y = float(substrate.S[(y + 1) % h, x] - substrate.S[(y - 1) % h, x])

    # Sensor blinding (Shock C)
    if hasattr(substrate, 'apply_sensory_dropout'):
        gu_x, gu_y, gv_x, gv_y, gs_x, gs_y = substrate.apply_sensory_dropout(
            (gu_x, gu_y, gv_x, gv_y, gs_x, gs_y)
        )

    inputs = (agent.x / w, agent.y / h, agent.energy, gu_x, gu_y, gv_x, gv_y, gs_x, gs_y)

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
        agent.energy -= 0.05
        if hasattr(substrate, 'deposit_secretion'):
            substrate.deposit_secretion(x, y, 0.5)
    else:
        dx = 1 if move_x > 0.3 else (-1 if move_x < -0.3 else 0)
        dy = 1 if move_y > 0.3 else (-1 if move_y < -0.3 else 0)
        if dx != 0 or dy != 0:
            new_x = (x + dx) % w
            new_y = (y + dy) % h

            # Barrier wall check (Shock B)
            if hasattr(substrate, 'apply_wall'):
                new_x, new_y = substrate.apply_wall(agent, new_x, new_y)

            agent.x = new_x
            agent.y = new_y
            action = 'M'
            agent.energy -= 0.01
        else:
            agent.energy -= 0.01

    # Record action
    if hasattr(agent, 'action_history'):
        agent.action_history.append(action)
        if len(agent.action_history) > 1000:
            agent.action_history.pop(0)

    return action


def compute_energy_intake(agent: V6Agent, substrate) -> float:
    """Compute energy intake for agent from substrate (substrate-type-aware)."""
    if hasattr(substrate, 'get_energy_at'):
        intake = substrate.get_energy_at(int(agent.x), int(agent.y))
    else:
        intake = float(substrate.V[int(agent.y) % substrate.height,
                                   int(agent.x) % substrate.width]) * 0.5
    # Extra penalty on barrier wrong-side
    if hasattr(substrate, 'get_penalty_at'):
        intake -= substrate.get_penalty_at(int(agent.x))
    return intake


# ---------------------------------------------------------------------------
# Single trial runner
# ---------------------------------------------------------------------------

def run_single_trial(
    condition_name: str,
    shock_spec: Dict[str, Any],
    writer: csv.DictWriter,
    file_obj,
    annex_log_dir: str,
    num_generations: int = 5000,
    log_interval: int = 100,
    pop_size: int = 20,
    seed: int = 42,
    verbose: bool = True,
) -> List[Dict[str, Any]]:
    """
    Run one transfer shock trial with corrected metrics.
    Streams results to CSV in real-time.
    """
    random.seed(seed)
    np.random.seed(seed)

    # Build substrate
    substrate = build_substrate(shock_spec, width=50, height=50)

    # Build population from founder condition
    founder = create_condition_agent(condition_name, seed=seed)
    max_nodes_cap = founder.max_nodes

    population: List[V6Agent] = []
    for _ in range(pop_size):
        child = V6Agent(
            x=random.randint(0, 49),
            y=random.randint(0, 49),
            genome=founder.genome.copy(),
            lineage_id=founder.lineage_id,
            max_nodes=max_nodes_cap,
        )
        population.append(child)

    # AnnexTracker — completely independent of agent architecture
    annex_tracker = AnnexTracker(condition_name=condition_name, persistence_threshold=500)

    # Behavioral metrics evaluator
    behavior_eval = BehavioralMetrics(traj_steps=20, traj_sample=8)

    performance_curve: List[float] = []
    trial_logs: List[Dict[str, Any]] = []

    print(f"\n" + "-"*70)
    print(f"  [{condition_name}] x [{shock_spec['name']}] | {num_generations} gens")
    print("-"*70)

    for gen in range(1, num_generations + 1):
        # 20 environment + agent steps per generation
        for _ in range(20):
            substrate.step()
            for agent in population:
                agent_step_on_substrate(agent, substrate)
                agent.energy += compute_energy_intake(agent, substrate)
                agent.energy = float(np.clip(agent.energy, -5.0, 10.0))

        avg_energy = float(np.mean([a.energy for a in population]))
        performance_curve.append(avg_energy)

        # Selection and reproduction
        population.sort(key=lambda a: a.energy, reverse=True)
        survivors = population[:max(1, len(population) // 2)]
        for a in survivors:
            a.energy = float(np.clip(a.energy + 0.2, 0.0, 1.0))
            a.x = (a.x + random.choice([-1, 0, 1])) % 50
            a.y = (a.y + random.choice([-1, 0, 1])) % 50

        new_pop = list(survivors)
        while len(new_pop) < pop_size:
            parent = random.choice(survivors)
            child = parent.reproduce()
            new_pop.append(child)
        population = new_pop

        # Logging
        if gen % log_interval == 0 or gen == num_generations:
            # Corrected ANNEX — environment hash, Goldilocks filter
            is_novel, goldilocks_status, env_hash = annex_tracker.record(
                substrate, population, gen,
                agent_id=condition_name
            )

            # Survival metrics
            surv = survival_rate(population)
            all_actions: List[str] = []
            for a in population:
                all_actions.extend(getattr(a, 'action_history', []))
            act_ent = action_entropy(all_actions)
            eng_eff = energy_efficiency(avg_energy, 0.05)
            adapt_sp = adaptation_speed(performance_curve)

            # Behavioral cross-validation
            bm = behavior_eval.evaluate(population, substrate, act_ent)

            avg_nodes = float(np.mean([len(a.genome.nodes) for a in population]))
            avg_edges = float(np.mean([len(a.genome.connections) for a in population]))

            record = {
                'Generation': gen,
                'Condition': condition_name,
                'Environment': shock_spec['name'],
                'EnvHash': env_hash,
                'SurvivalRate': round(surv, 4),
                'ActionEntropy': round(act_ent, 4),
                'EnergyEfficiency': round(eng_eff, 4),
                'ANNEX': annex_tracker.count,          # Step function count
                'GoldilocksStatus': goldilocks_status,  # ACCEPT/REJECT_TOO_EASY/REJECT_TOO_HARD
                'ANNEX_Increment': is_novel,
                'AdaptationSpeed': adapt_sp,
                'TrajDiversity': bm['TrajDiversity'],
                'PhenotypeDiversity': bm['PhenotypeDiversity'],
                'EntropyVerdict': bm['EntropyVerdict'],
                'AvgNodes': round(avg_nodes, 2),
                'AvgEdges': round(avg_edges, 2),
            }
            trial_logs.append(record)
            writer.writerow(record)
            file_obj.flush()

            if verbose:
                print(
                    f"  Gen {gen:05d}/{num_generations} | "
                    f"Surv: {surv:.2f} | Ent: {act_ent:.3f} [{bm['EntropyVerdict'][:5]}] | "
                    f"ANNEX: {annex_tracker.count} [{goldilocks_status[:6]}] | "
                    f"TrajDiv: {bm['TrajDiversity']:.2f} | "
                    f"Nodes: {avg_nodes:.1f} | Edges: {avg_edges:.1f}",
                    flush=True
                )

    # Save ANNEX increment log for this trial
    trial_tag = f"{condition_name.replace(' ', '_').replace('(', '').replace(')', '')}_{shock_spec['id']}"
    annex_log_path = os.path.join(annex_log_dir, f"annex_log_{trial_tag}.json")
    os.makedirs(annex_log_dir, exist_ok=True)
    with open(annex_log_path, 'w') as f:
        json.dump(annex_tracker.get_log(), f, indent=2)

    increments = annex_tracker.get_increments_only()
    print(f"  [OK] Trial complete. ANNEX={annex_tracker.count} | "
          f"{len(increments)} genuine novel environments | Log: {annex_log_path}")

    return trial_logs


# ---------------------------------------------------------------------------
# Main experiment
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description='Genesis V6 Phase 3 Experiment Runner')
    parser.add_argument('--calibrate', action='store_true',
                        help='Run calibration test (500 gens) before full run')
    parser.add_argument('--gens', type=int, default=5000,
                        help='Generations per trial (default: 5000)')
    parser.add_argument('--log-interval', type=int, default=100,
                        help='Logging interval in generations (default: 100)')
    parser.add_argument('--seed', type=int, default=42, help='Random seed')
    parser.add_argument('--pop-size', type=int, default=20, help='Population size')
    args = parser.parse_args()

    conditions = [
        'Condition A (V5 467 nodes)',
        'Condition B (V6 Constrained 52 nodes)',
        'Condition C (V4 123 nodes)',
        'Condition D (Naive 12 nodes)',
    ]

    shocks = [
        generate_shock_env_A(),
        generate_shock_env_B(gap_half=3),
        generate_shock_env_C(),
    ]

    output_dir = os.path.join(root_dir, 'v6', 'results')
    os.makedirs(output_dir, exist_ok=True)

    annex_log_dir = os.path.join(output_dir, 'annex_logs')

    headers = [
        'Generation', 'Condition', 'Environment', 'EnvHash',
        'SurvivalRate', 'ActionEntropy', 'EnergyEfficiency',
        'ANNEX', 'GoldilocksStatus', 'ANNEX_Increment',
        'AdaptationSpeed',
        'TrajDiversity', 'PhenotypeDiversity', 'EntropyVerdict',
        'AvgNodes', 'AvgEdges',
    ]

    # ---- Calibration test ----
    if args.calibrate:
        print('\n' + '=' * 70)
        print('  CALIBRATION TEST — 500 generations × 4 conditions × 3 shocks')
        print('  Goal: Verify Condition D crashes in Shock B and Shock C')
        print('=' * 70)

        cal_path = os.path.join(output_dir, 'phase3_calibration.csv')
        with open(cal_path, 'w', newline='') as f:
            w = csv.DictWriter(f, fieldnames=headers)
            w.writeheader()
            for shock in shocks:
                for cond in conditions:
                    run_single_trial(
                        condition_name=cond,
                        shock_spec=shock,
                        writer=w,
                        file_obj=f,
                        annex_log_dir=annex_log_dir,
                        num_generations=500,
                        log_interval=100,
                        pop_size=args.pop_size,
                        seed=args.seed,
                    )

        print(f'\n[OK] Calibration complete -> {cal_path}')
        print('Check: Condition D SurvivalRate in Shock B and Shock C should be <0.3')
        print('If Condition D survives, narrow the gap or increase dropout rate.')
        return

    # ---- Full run ----
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    csv_path = os.path.join(output_dir, f'phase3_results_{timestamp}.csv')
    latest_path = os.path.join(output_dir, 'phase3_results.csv')

    print('\n' + '=' * 70)
    print('  Genesis V6 Phase 3: Fixed Metrics & Upgraded Transfer Shocks')
    print(f'  {args.gens} gens x {len(conditions)} conditions x {len(shocks)} shocks')
    print(f'  = {args.gens * len(conditions) * len(shocks):,} total generations')
    print(f'  Seed: {args.seed} | Pop size: {args.pop_size}')
    print('=' * 70)

    with open(csv_path, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=headers)
        w.writeheader()

        for shock in shocks:
            for cond in conditions:
                run_single_trial(
                    condition_name=cond,
                    shock_spec=shock,
                    writer=w,
                    file_obj=f,
                    annex_log_dir=annex_log_dir,
                    num_generations=args.gens,
                    log_interval=args.log_interval,
                    pop_size=args.pop_size,
                    seed=args.seed,
                )

    # Copy to latest
    import shutil
    shutil.copy2(csv_path, latest_path)

    print('\n' + '=' * 70)
    print('[SUCCESS] Phase 3 complete.')
    print(f'  Timestamped results: {csv_path}')
    print(f'  Latest results:      {latest_path}')
    print(f'  ANNEX logs:          {annex_log_dir}/')
    print('=' * 70)


if __name__ == '__main__':
    main()
