"""
run_condition_e.py - Condition E: Random Dense Network Control

Tests whether the Phase 3 Condition B result (100% survival in Shock B) is due to:
  (a) Edge density ALONE -- random 52-node, 815-edge network survives at 1.00, OR
  (b) Training regime -- compensatory evolution UNDER CONSTRAINT is necessary

Condition E: 52 nodes, 815 edges, randomly initialized, NO node cap (max_nodes=None)
Condition B: 52 nodes, 815 edges, randomly initialized, max_nodes=52 (cap enforced)

The genomes start IDENTICALLY (same topology, same seed). The difference is:
- Condition B: mutation is blocked from adding nodes above 52. Evolution must
  route adaptation through edge rewiring alone.
- Condition E: mutation is FREE to add nodes. If E evolves more nodes and survives,
  density alone is not the mechanism -- the cap forced a different evolutionary path.
  If E survives at 1.00 without adding nodes, density alone is sufficient.

Single seed (42), 5000 generations, Shock B, exact Phase 3 parameters.

Output:
  v6/results/condition_e_trajectory.csv    -- gen-by-gen metrics
  v6/results/condition_e_result.txt        -- verdict + comparison table
"""

import sys
import os
import csv
import random
import numpy as np
from typing import List

root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if root_dir not in sys.path:
    sys.path.append(root_dir)

from genesis_engine_v6.src.v6_agent import V6Agent, build_agent_with_target_topology
from genesis_engine_v6.src.v6_transfer_shock_envs import BarrierSubstrate
from genesis_engine_v6.src.v6_transfer_metrics import survival_rate, action_entropy, AnnexTracker

# -----------------------------------------------------------------------
# Exact Phase 3 / Replication parameters
# -----------------------------------------------------------------------
SEED         = 42
NUM_GENS     = 5000
LOG_INTERVAL = 500
POP_SIZE     = 20
GAP_HALF     = 1       # 3-cell gap, same as Phase 3 final run
MOVE_COST    = 0.03
IDLE_COST    = 0.02
SECRETE_COST = 0.10
ENERGY_MULT  = 0.20    # intake = get_energy_at() * (ENERGY_MULT / 0.5)

# Known Condition B result from replication (seed 42) for direct comparison
CONDITION_B_KNOWN = {
    'FinalSurvival': 1.00,
    'FinalNodes':    52.0,
    'FinalEdges':    815.0,
    'ANNEX':         1,
    'Description':   'Evolved under node cap (max_nodes=52) -- confirmed 1.00 survival',
}


# -----------------------------------------------------------------------
# Reuse Phase 3 agent step logic (copy -- no import dependency on runner)
# -----------------------------------------------------------------------

def agent_step(agent: V6Agent, substrate: BarrierSubstrate) -> str:
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


def energy_intake(agent: V6Agent, substrate: BarrierSubstrate) -> float:
    intake = substrate.get_energy_at(int(agent.x), int(agent.y)) * (ENERGY_MULT / 0.5)
    intake -= substrate.get_penalty_at(int(agent.x))
    return intake


# -----------------------------------------------------------------------
# Main experiment
# -----------------------------------------------------------------------

def main():
    random.seed(SEED)
    np.random.seed(SEED)

    output_dir = os.path.join(root_dir, 'v6', 'results')
    os.makedirs(output_dir, exist_ok=True)
    traj_path   = os.path.join(output_dir, 'condition_e_trajectory.csv')
    result_path = os.path.join(output_dir, 'condition_e_result.txt')

    print('=' * 70)
    print(' Condition E: Random Dense Network Control')
    print(' 52 nodes, 815 edges, NO node cap, seed 42, 5000 gens, Shock B')
    print('=' * 70)
    print()
    print(' QUESTION: Does edge density ALONE produce 100% survival,')
    print('           or does compensatory training under constraint matter?')
    print()
    print(' Condition B (known): 52n, 815e, max_nodes=52 -> Surv=1.00 (5/5 seeds)')
    print(' Condition E (test):  52n, 815e, max_nodes=None -> ?')
    print()

    # Create Condition E founder:
    # Same topology as Condition B (same seed, same node/edge counts),
    # but max_nodes=None so evolution is FREE to add nodes.
    founder_e = build_agent_with_target_topology(
        target_nodes=52,
        target_edges=815,
        max_nodes=None,   # <-- KEY DIFFERENCE from Condition B
        seed=SEED,
    )
    initial_nodes = len(founder_e.genome.nodes)
    initial_edges = len(founder_e.genome.connections)

    print(f' Founder topology: {initial_nodes} nodes, {initial_edges} edges')
    print(f' max_nodes: None (unconstrained)')
    print()

    # Build population from founder
    population: List[V6Agent] = []
    for _ in range(POP_SIZE):
        child = V6Agent(
            x=random.randint(0, 49),
            y=random.randint(0, 49),
            genome=founder_e.genome.copy(),
            lineage_id=founder_e.lineage_id,
            max_nodes=None,
        )
        population.append(child)

    substrate = BarrierSubstrate(width=50, height=50, gap_half=GAP_HALF)
    annex_tracker = AnnexTracker(condition_name='Condition_E')
    performance_curve = []

    traj_headers = [
        'Generation', 'SurvivalRate', 'ActionEntropy',
        'ANNEX', 'GoldilocksStatus', 'AvgNodes', 'AvgEdges',
    ]

    with open(traj_path, 'w', newline='') as traj_f:
        writer = csv.DictWriter(traj_f, fieldnames=traj_headers)
        writer.writeheader()

        goldilocks_status = 'PENDING'

        for gen in range(1, NUM_GENS + 1):
            for _ in range(20):
                substrate.step()
                for agent in population:
                    agent_step(agent, substrate)
                    agent.energy += energy_intake(agent, substrate)
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
                    substrate, population, gen, agent_id='Condition_E'
                )
                # Override with pre-selection Goldilocks check
                if 0.05 <= pre_surv <= 0.95:
                    if env_hash not in annex_tracker._seen_hashes:
                        annex_tracker._seen_hashes.add(env_hash)
                        annex_tracker.count += 1
                        goldilocks_status = 'ACCEPT'

                avg_nodes = float(np.mean([len(a.genome.nodes) for a in population]))
                avg_edges = float(np.mean([len(a.genome.connections) for a in population]))
                all_actions = []
                for a in population:
                    all_actions.extend(getattr(a, 'action_history', []))
                act_ent = action_entropy(all_actions)

                writer.writerow({
                    'Generation':      gen,
                    'SurvivalRate':    round(pre_surv, 4),
                    'ActionEntropy':   round(act_ent, 4),
                    'ANNEX':           annex_tracker.count,
                    'GoldilocksStatus': goldilocks_status,
                    'AvgNodes':        round(avg_nodes, 2),
                    'AvgEdges':        round(avg_edges, 2),
                })
                traj_f.flush()

                print(f'  Gen {gen:05d}/{NUM_GENS} | '
                      f'Surv: {pre_surv:.2f} | '
                      f'ANNEX: {annex_tracker.count} [{goldilocks_status[:6]}] | '
                      f'Nodes: {avg_nodes:.1f} | Edges: {avg_edges:.1f}',
                      flush=True)

    # Final metrics
    final_nodes = float(np.mean([len(a.genome.nodes) for a in population]))
    final_edges = float(np.mean([len(a.genome.connections) for a in population]))

    # -----------------------------------------------------------------------
    # Verdict
    # -----------------------------------------------------------------------
    surv_e = pre_surv  # final gen pre-selection survival

    if surv_e >= 1.00:
        verdict = 'DENSITY_SUFFICIENT'
        explanation = (
            'Condition E achieved 1.00 survival.\n'
            'Edge density alone -- without compensatory training history -- is\n'
            'sufficient to match Condition B performance in the Shock B environment.\n'
            'MECHANISM: Edge density is the unit of evolvability, regardless of how\n'
            'it was produced.'
        )
    elif surv_e >= 0.50:
        verdict = 'DENSITY_PARTIAL'
        explanation = (
            f'Condition E achieved {surv_e:.2f} survival (below Condition B 1.00,\n'
            f'above Condition D ~0.40 average).\n'
            f'Density helps but is not sufficient alone. The training regime\n'
            f'(compensatory evolution under constraint) contributes additional\n'
            f'benefit beyond raw edge count.'
        )
    else:
        verdict = 'REGIME_NECESSARY'
        explanation = (
            f'Condition E FAILED ({surv_e:.2f} survival).\n'
            f'Random dense initialization (52n, 815e, no cap) does NOT replicate\n'
            f'Condition B performance (1.00 survival).\n'
            f'MECHANISM: The compensatory training history under a node cap is\n'
            f'necessary. Dense edges produced by constraint-driven evolution have\n'
            f'qualitatively different functional properties than randomly initialized\n'
            f'dense edges.'
        )

    node_growth = final_nodes - initial_nodes
    growth_note = (
        f'Nodes grew {initial_nodes:.0f} -> {final_nodes:.1f} '
        f'(+{node_growth:.1f}) -- evolution used the freedom to add nodes.'
        if node_growth > 2 else
        f'Nodes stable {initial_nodes:.0f} -> {final_nodes:.1f} '
        f'-- evolution did NOT exploit the freedom to add nodes.'
    )

    report = f"""Condition E Result: Random Dense Network Control
=================================================
Experiment design:
  Condition B (control): 52 nodes, 815 edges, max_nodes=52, seed 42
  Condition E (test):    52 nodes, 815 edges, max_nodes=None, seed 42
  Environment: Shock B (Barrier + Gap, gap=3 cells)
  Generations: {NUM_GENS}

Results:
  Condition E final survival:  {surv_e:.3f}
  Condition B known survival:  {CONDITION_B_KNOWN['FinalSurvival']:.3f}
  Condition D mean survival:   0.380 (avg across 5 seeds from replication)

  Condition E final nodes:  {final_nodes:.1f}  (started at {initial_nodes})
  Condition E final edges:  {final_edges:.1f}  (started at {initial_edges})
  Node growth note: {growth_note}

  ANNEX: {annex_tracker.count}
  Goldilocks: {goldilocks_status}

VERDICT: {verdict}
{'-' * 50}
{explanation}

Comparison Table:
  Condition | Nodes (start->end) | Edges       | Survival | Mechanism
  --------- | ------------------ | ----------- | -------- | ---------
  B (known) | 52 -> 52 (FROZEN)  | 815 (fixed) | 1.00     | Node cap + dense edges
  E (this)  | {initial_nodes} -> {final_nodes:.0f}{' '*max(0,12-len(str(int(final_nodes))))}| {final_edges:.0f}{' '*max(0,12-len(str(int(final_edges))))}| {surv_e:.2f}     | Random dense, no cap
  D (known) | 12 -> ~150 (10x)   | ~450        | 0.20-0.55| Naive, unconstrained

Implication for publication:
"""

    if verdict == 'DENSITY_SUFFICIENT':
        report += (
            '  The finding generalizes: EDGE DENSITY is the mechanism.\n'
            '  The specific training history (node cap) is not necessary.\n'
            '  Claim: "52-node, 815-edge networks survive Shock B at 100%\n'
            '  regardless of how the density was produced."\n'
            '  This strengthens the finding -- density is a transferable property.'
        )
    elif verdict == 'DENSITY_PARTIAL':
        report += (
            '  The training regime provides additional benefit.\n'
            '  Density helps, but constraint-driven evolution produces\n'
            '  functionally superior networks for this environment.\n'
            '  Claim: "Edge density is necessary but not sufficient;\n'
            '  compensatory evolution under constraint is required for\n'
            '  full survival equivalence with larger networks."'
        )
    else:
        report += (
            '  The training regime is essential.\n'
            '  Compensatory evolution under a node cap produces networks\n'
            '  qualitatively different from randomly initialized dense networks.\n'
            '  Claim: "The evolvability reserve is a product of the evolutionary\n'
            '  process, not just the topology -- constraint-driven evolution\n'
            '  encodes adaptive structure that random initialization cannot replicate."'
        )

    with open(result_path, 'w') as f:
        f.write(report)

    print()
    print('=' * 70)
    print(f'[SUCCESS] Condition E complete.')
    print(f'  Trajectory: {traj_path}')
    print(f'  Report:     {result_path}')
    print()
    print(f'  VERDICT: {verdict}')
    print(f'  Condition E survival: {surv_e:.3f}')
    print(f'  Condition B survival: {CONDITION_B_KNOWN["FinalSurvival"]:.3f}')
    print(f'  Node growth: {initial_nodes} -> {final_nodes:.1f}')
    print('=' * 70)


if __name__ == '__main__':
    main()
