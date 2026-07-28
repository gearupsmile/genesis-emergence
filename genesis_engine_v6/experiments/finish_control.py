"""
finish_control.py
Runs Control condition from seed 42 to append the remaining 9200-10000 generations.
"""

import sys
import os
import csv
import random
import numpy as np

root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if root_dir not in sys.path:
    sys.path.append(root_dir)

from genesis_engine_v6.src.v6_agent import V6Agent
from genesis_engine_v6.src.v6_substrate import EnvironmentGenome
from genesis_engine_v6.src.v6_speciation import assign_species
from genesis_engine_v6.src.v6_metrics import action_entropy, gac, ANNEX
from genesis_engine_v6.experiments.run_constrained_ceiling import V6CoevolutionOrchestrator
from genesis_engine_v6.experiments.merge_and_plot import merge_csvs, generate_plot

def run_finish_control(seed: int = 42):
    print(f"\n=======================================================")
    print(f" Completing Control Condition (Generations 9200 -> 10000)")
    print(f"=======================================================")

    random.seed(seed)
    np.random.seed(seed)

    orchestrator = V6CoevolutionOrchestrator(
        num_envs=5,
        pop_size_per_env=20,
        max_nodes=None
    )

    annex_tracker = ANNEX()
    for env_id, sub in orchestrator.substrates.items():
        annex_tracker.record_environment(sub, agents_solved=True)

    species_list = []

    out_dirs = ['genesis_engine_v6/results', 'v6/results']
    csv_files = []
    writers = []

    for d in out_dirs:
        os.makedirs(d, exist_ok=True)
        path = os.path.join(d, 'constrained_ceiling.csv')
        f = open(path, 'a', newline='')
        w = csv.writer(f)
        csv_files.append(f)
        writers.append(w)

    try:
        for gen in range(1, 10001):
            orchestrator.step(gen)

            if gen % 100 == 0 or gen == 1:
                new_env = orchestrator.coevolve()
                if new_env is not None:
                    annex_tracker.record_environment(orchestrator.substrates[new_env.id], agents_solved=True)

                all_agents = []
                for pop in orchestrator.agent_populations.values():
                    all_agents.extend(pop)

                nodes = [len(a.genome.nodes) for a in all_agents]
                edges = [len(a.genome.connections) for a in all_agents]
                entropies = [action_entropy(a) for a in all_agents]
                gac_val = gac(all_agents, gen, orchestrator.innovation_birth, persistence_threshold=500)

                species_list = assign_species(all_agents, species_list, compatibility_threshold=3.0)
                species_count = len(species_list)

                avg_nodes = float(np.mean(nodes))
                avg_edges = float(np.mean(edges))
                avg_entropy = float(np.mean(entropies))

                if gen > 9100:
                    print(f"Gen {gen:05d} | Control     | Nodes: {avg_nodes:.2f} | "
                          f"Entropy: {avg_entropy:.3f} | GAC: {gac_val:.3f} | Species: {species_count} | "
                          f"ANNEX: {annex_tracker.count} | Edges: {avg_edges:.1f} [APPENDED]", flush=True)

                    row = [gen, "Control", f"{avg_nodes:.2f}", f"{avg_entropy:.4f}",
                           f"{gac_val:.4f}", species_count, annex_tracker.count, f"{avg_edges:.2f}"]
                    for w in writers:
                        w.writerow(row)
                    for f in csv_files:
                        f.flush()
                else:
                    if gen % 1000 == 0:
                        print(f"Control Fast-Forwarding: Gen {gen:05d}/9100 complete...", flush=True)

    finally:
        for f in csv_files:
            f.close()

    print("[SUCCESS] Control condition 10000 generations completed!")
    merged_df = merge_csvs()
    out_file = os.path.abspath('v6/results/constrained_ceiling_summary.png')
    generate_plot(merged_df, out_file)

if __name__ == "__main__":
    run_finish_control(seed=42)
