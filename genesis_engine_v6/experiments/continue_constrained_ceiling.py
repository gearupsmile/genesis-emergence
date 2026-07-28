"""
continue_constrained_ceiling.py
Continues the Genesis V6 Constrained Ceiling Ablation Study from existing CSV data.
Appends remaining Control generations (9200-10000) and runs full Constrained condition (1-10000).
"""

import sys
import os
import csv
import random
import numpy as np

# Ensure project root is on sys.path
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if root_dir not in sys.path:
    sys.path.append(root_dir)

from genesis_engine_v6.src.v6_agent import V6Agent
from genesis_engine_v6.src.v6_substrate import EnvironmentGenome
from genesis_engine_v6.src.v6_speciation import assign_species
from genesis_engine_v6.src.v6_metrics import action_entropy, gac, ANNEX
from genesis_engine_v6.experiments.run_constrained_ceiling import V6CoevolutionOrchestrator
from genesis_engine_v6.experiments.plot_constrained_ceiling import generate_plot

def run_condition_continue(condition_name: str, max_nodes, generations: int = 10000,
                          log_interval: int = 100, start_log_gen: int = 0, seed: int = 42,
                          csv_writers=None, csv_files=None):
    print(f"\n=======================================================")
    print(f" Starting Genesis V6 Condition: {condition_name}")
    print(f" Max Nodes Cap: {max_nodes if max_nodes is not None else 'Unconstrained (Control)'}")
    print(f" Target Generations: {generations} | Logging starting at Gen > {start_log_gen} | Seed: {seed}")
    print(f"=======================================================")

    random.seed(seed)
    np.random.seed(seed)

    orchestrator = V6CoevolutionOrchestrator(
        num_envs=5,
        pop_size_per_env=20,
        max_nodes=max_nodes
    )

    annex_tracker = ANNEX()
    for env_id, sub in orchestrator.substrates.items():
        annex_tracker.record_environment(sub, agents_solved=True)

    species_list = []

    for gen in range(1, generations + 1):
        orchestrator.step(gen)

        if gen % log_interval == 0 or gen == 1:
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

            is_new = (gen > start_log_gen) or (gen == 1 and start_log_gen == 0)

            print(f"Gen {gen:05d} | {condition_name:<11} | Nodes: {avg_nodes:.2f} | "
                  f"Entropy: {avg_entropy:.3f} | GAC: {gac_val:.3f} | Species: {species_count} | "
                  f"ANNEX: {annex_tracker.count} | Edges: {avg_edges:.1f} {'[SAVED]' if is_new else '[SKIP HELD]'}", flush=True)

            if is_new:
                row = [gen, condition_name, f"{avg_nodes:.2f}", f"{avg_entropy:.4f}",
                       f"{gac_val:.4f}", species_count, annex_tracker.count, f"{avg_edges:.2f}"]
                if csv_writers:
                    for w in csv_writers:
                        w.writerow(row)
                if csv_files:
                    for f in csv_files:
                        f.flush()

def main():
    out_dirs = ['genesis_engine_v6/results', 'v6/results']
    csv_files = []
    writers = []

    for d in out_dirs:
        os.makedirs(d, exist_ok=True)
        path = os.path.join(d, 'constrained_ceiling.csv')
        f = open(path, 'a', newline='')  # APPEND mode!
        w = csv.writer(f)
        csv_files.append(f)
        writers.append(w)

    try:
        # Control: Fast forward 1-9100 (which is already saved in CSV) and log 9200-10000
        run_condition_continue("Control", max_nodes=None, generations=10000, log_interval=100,
                               start_log_gen=9100, seed=42, csv_writers=writers, csv_files=csv_files)

        # Constrained: Run 1-10000 (all new, save everything)
        run_condition_continue("Constrained", max_nodes=52, generations=10000, log_interval=100,
                               start_log_gen=0, seed=42, csv_writers=writers, csv_files=csv_files)

        print("\n[SUCCESS] Genesis V6 Constrained Ceiling Ablation Study completed successfully.")

    finally:
        for f in csv_files:
            f.close()

    # Generate final summary plot
    out_file = os.path.abspath('v6/results/constrained_ceiling_summary.png')
    csv_path = os.path.abspath('v6/results/constrained_ceiling.csv')
    generate_plot(csv_path, out_file)

if __name__ == "__main__":
    main()
