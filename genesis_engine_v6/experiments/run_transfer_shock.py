"""
run_transfer_shock.py - Main Experiment Runner for Phase 2 Transfer Shock Study

Tests the hypothesis:
Constrained agents (52 nodes, 815 edges) adapt faster to novel environments than:
- V5 agents (467 nodes, co-evolved)
- V4 agents (123 nodes, static environment)
- Naive agents (12 nodes, untrained)
"""

import sys
import os
import csv
import random
import numpy as np
from typing import List, Dict, Any

# Ensure project root is on sys.path
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if root_dir not in sys.path:
    sys.path.append(root_dir)

from genesis_engine_v6.src.v6_agent import V6Agent, create_condition_agent
from genesis_engine_v6.src.v6_transfer_shock_envs import (
    generate_shock_env_A,
    generate_shock_env_B,
    generate_shock_env_C,
    TransferShockSubstrate
)
from genesis_engine_v6.src.v6_transfer_metrics import (
    adaptation_speed,
    survival_rate,
    action_entropy,
    energy_efficiency,
    ANNEX
)

def run_single_transfer_shock_trial(
    condition_name: str,
    shock_spec: Dict[str, Any],
    writer: csv.DictWriter,
    file_obj,
    num_generations: int = 5000,
    log_interval: int = 500,
    pop_size: int = 20,
    seed: int = 42
) -> List[Dict[str, Any]]:
    """
    Executes one transfer shock trial for a specified condition and shock environment.
    Streams logged records to CSV immediately.
    """
    random.seed(seed)
    np.random.seed(seed)

    # Initialize substrate for shock environment
    substrate = TransferShockSubstrate(shock_spec, width=50, height=50)

    # Build initial population from founder condition agent
    founder = create_condition_agent(condition_name, seed=seed)
    max_nodes_cap = founder.max_nodes

    population = []
    for _ in range(pop_size):
        agent_copy = V6Agent(
            x=random.randint(0, 49),
            y=random.randint(0, 49),
            genome=founder.genome.copy(),
            lineage_id=founder.lineage_id,
            max_nodes=max_nodes_cap
        )
        population.append(agent_copy)

    innovation_birth: Dict[int, int] = {}
    for agent in population:
        for conn in agent.genome.connections.values():
            innovation_birth[conn.innovation_id] = 0

    trial_logs = []
    performance_curve = []

    for gen in range(1, num_generations + 1):
        # 1. Environment and agent simulation steps (20 steps per gen)
        for _ in range(20):
            substrate.step()
            for agent in population:
                agent.step(substrate)
                # Energy intake from environment V field
                agent.energy += substrate.V[int(agent.y), int(agent.x)] * 0.5

        # Record population average energy performance
        avg_energy = float(np.mean([a.energy for a in population]))
        performance_curve.append(avg_energy)

        # 2. Selection and Reproduction
        population.sort(key=lambda a: a.energy, reverse=True)
        survivors = population[:len(population) // 2]
        for a in survivors:
            a.energy = min(1.0, max(0.0, a.energy + 0.2))
            a.x = (a.x + random.choice([-1, 0, 1])) % substrate.width
            a.y = (a.y + random.choice([-1, 0, 1])) % substrate.height

        new_pop = list(survivors)
        while len(new_pop) < pop_size:
            parent = random.choice(survivors)
            child = parent.reproduce()

            for conn in child.genome.connections.values():
                if conn.innovation_id not in innovation_birth:
                    innovation_birth[conn.innovation_id] = gen

            new_pop.append(child)

        population = new_pop

        # 3. Logging at specified log interval or final gen
        if gen % log_interval == 0 or gen == num_generations:
            surv = survival_rate(population)
            all_actions = []
            for a in population:
                all_actions.extend(a.action_history)
            act_ent = action_entropy(all_actions)
            eng_eff = energy_efficiency(avg_energy, 0.05)
            annex_val = ANNEX(population, gen, innovation_birth)
            adapt_sp = adaptation_speed(performance_curve)

            avg_nodes = float(np.mean([len(a.genome.nodes) for a in population]))
            avg_edges = float(np.mean([len(a.genome.connections) for a in population]))

            record = {
                'Generation': gen,
                'Condition': condition_name,
                'Environment': shock_spec['name'],
                'SurvivalRate': round(surv, 4),
                'ActionEntropy': round(act_ent, 4),
                'EnergyEfficiency': round(eng_eff, 4),
                'ANNEX': round(annex_val, 4),
                'AdaptationSpeed': adapt_sp,
                'AvgNodes': round(avg_nodes, 2),
                'AvgEdges': round(avg_edges, 2)
            }
            trial_logs.append(record)
            writer.writerow(record)
            file_obj.flush()

            print(f"[{condition_name} | {shock_spec['name']}] Gen {gen:04d}/{num_generations} | "
                  f"SurvRate: {surv:.2f} | Entropy: {act_ent:.3f} | ANNEX: {annex_val:.0f} | "
                  f"AdaptSpeed: {adapt_sp} | Nodes: {avg_nodes:.1f} | Edges: {avg_edges:.1f}")

    return trial_logs

def main(num_generations: int = 5000, log_interval: int = 500, seed: int = 42):
    conditions = [
        'Condition A (V5 467 nodes)',
        'Condition B (V6 Constrained 52 nodes)',
        'Condition C (V4 123 nodes)',
        'Condition D (Naive 12 nodes)'
    ]

    shocks = [
        generate_shock_env_A(),
        generate_shock_env_B(),
        generate_shock_env_C()
    ]

    output_dir = os.path.join(root_dir, 'v6', 'results')
    os.makedirs(output_dir, exist_ok=True)
    csv_path = os.path.join(output_dir, 'transfer_shock.csv')

    headers = [
        'Generation', 'Condition', 'Environment', 'SurvivalRate',
        'ActionEntropy', 'EnergyEfficiency', 'ANNEX', 'AdaptationSpeed',
        'AvgNodes', 'AvgEdges'
    ]

    print("=" * 70)
    print(" Genesis V6 Phase 2: Transfer Shock Experiment Execution")
    print(f" Generations per trial: {num_generations} | Seed: {seed}")
    print("=" * 70)

    with open(csv_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        f.flush()

        for shock in shocks:
            for cond in conditions:
                run_single_transfer_shock_trial(
                    condition_name=cond,
                    shock_spec=shock,
                    writer=writer,
                    file_obj=f,
                    num_generations=num_generations,
                    log_interval=log_interval,
                    seed=seed
                )

    print("\n" + "=" * 70)
    print(f"[SUCCESS] Transfer shock experiment completed. Results saved to:\n  {csv_path}")
    print("=" * 70)

if __name__ == '__main__':
    main()
