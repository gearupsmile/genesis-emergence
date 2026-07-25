"""
run_constrained_ceiling.py - Main Experiment Runner for Genesis V6 Constrained Ceiling Ablation Study

Tests the hypothesis: Is structural-behavioral lag in V5 a necessary complexification phase,
or do agents continue to complexify behaviorally when structural growth is capped at 52 nodes?
"""

import sys
import os
import csv
import random
import numpy as np
from typing import List, Dict, Optional

# Ensure project root is on sys.path
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if root_dir not in sys.path:
    sys.path.append(root_dir)

from genesis_engine_v6.src.v6_agent import V6Agent
from genesis_engine_v6.src.v6_substrate import V6Substrate, EnvironmentGenome, CPPNEnvironment
from genesis_engine_v6.src.v6_speciation import Species, assign_species
from genesis_engine_v6.src.v6_metrics import action_entropy, gac, ANNEX
from v5.src.coevolution import POETMinimalCriteria, GoalSwitching

class V6CoevolutionOrchestrator:
    """
    Co-evolutionary orchestrator supporting node-constrained agent evolution.
    """
    def __init__(self, num_envs: int = 5, pop_size_per_env: int = 20, max_nodes: Optional[int] = None):
        self.num_envs = num_envs
        self.pop_size_per_env = pop_size_per_env
        self.max_nodes = max_nodes
        self.environments = []
        self.substrates = {}
        self.agent_populations = {}
        self.innovation_birth: Dict[int, int] = {}
        self.total_transfers = 0
        self.total_mutations = 0

        # Create initial environments and agents
        for _ in range(num_envs):
            env = EnvironmentGenome()
            self.environments.append(env)
            self.substrates[env.id] = env.build_substrate()

            pop = [
                V6Agent(
                    x=random.randint(0, 49),
                    y=random.randint(0, 49),
                    max_nodes=self.max_nodes
                )
                for _ in range(pop_size_per_env)
            ]
            self.agent_populations[env.id] = pop

    def step(self, generation: int):
        """Advances simulation by 1 generation."""
        for env in self.environments:
            sub = self.substrates[env.id]
            pop = self.agent_populations[env.id]
            env.age += 1

            # Execute simulation steps for this generation
            for _ in range(20):
                sub.step()
                for agent in pop:
                    agent.step(sub)
                    # Energy intake from environment
                    agent.energy += sub.V[int(agent.y), int(agent.x)] * 0.5

            # Selection and reproduction within population
            pop.sort(key=lambda a: a.energy, reverse=True)
            env.fitness = np.mean([a.energy for a in pop])

            survivors = pop[:len(pop) // 2]
            for a in survivors:
                a.energy = min(1.0, max(0.0, a.energy + 0.2))
                a.x = (a.x + random.choice([-1, 0, 1])) % sub.width
                a.y = (a.y + random.choice([-1, 0, 1])) % sub.height

            new_pop = list(survivors)
            while len(new_pop) < self.pop_size_per_env:
                parent = random.choice(survivors)
                child = parent.reproduce()

                # Record birth generation for new innovations
                for conn in child.genome.connections.values():
                    if conn.innovation_id not in self.innovation_birth:
                        self.innovation_birth[conn.innovation_id] = generation

                # Hypermutation steps
                for _ in range(4):
                    child.mutate()
                    for conn in child.genome.connections.values():
                        if conn.innovation_id not in self.innovation_birth:
                            self.innovation_birth[conn.innovation_id] = generation

                new_pop.append(child)

            self.agent_populations[env.id] = new_pop

    def coevolve(self):
        """Handles agent transfer and environmental replacement."""
        # 1. Transfer top agents
        for src_env in self.environments:
            for tgt_env in self.environments:
                if src_env.id == tgt_env.id:
                    continue
                src_pop = self.agent_populations[src_env.id]
                best_agent = sorted(src_pop, key=lambda a: a.energy, reverse=True)[0]

                if GoalSwitching.should_transfer(best_agent, self.substrates[src_env.id], self.substrates[tgt_env.id]):
                    transferred = V6Agent(
                        x=best_agent.x,
                        y=best_agent.y,
                        genome=best_agent.genome.copy(),
                        lineage_id=best_agent.lineage_id,
                        max_nodes=self.max_nodes
                    )
                    self.agent_populations[tgt_env.id].append(transferred)
                    self.total_transfers += 1

        # Trim population sizes
        for env_id in self.agent_populations:
            pop = self.agent_populations[env_id]
            if len(pop) > self.pop_size_per_env:
                pop.sort(key=lambda a: a.energy, reverse=True)
                self.agent_populations[env_id] = pop[:self.pop_size_per_env]

        # 2. Environment replacement
        self.environments.sort(key=lambda e: e.fitness)
        worst_env = self.environments[0]
        best_env = self.environments[-1]

        mutated_env = best_env.copy()
        mutated_env.mutate()

        all_agents = []
        for pop in self.agent_populations.values():
            all_agents.extend(pop)

        if POETMinimalCriteria.is_viable(mutated_env, all_agents):
            self.environments[0] = mutated_env
            self.substrates[mutated_env.id] = mutated_env.build_substrate()
            self.agent_populations[mutated_env.id] = self.agent_populations.pop(worst_env.id)
            self.total_mutations += 1
            return mutated_env
        return None


def run_condition(condition_name: str, max_nodes: Optional[int], generations: int = 10000,
                  log_interval: int = 1000, pop_size_per_env: int = 20, num_envs: int = 5, seed: int = 42,
                  csv_writers: List = None, csv_files: List = None):

    """
    Runs a single experimental condition (Control vs Constrained).
    """
    print(f"\n=======================================================")
    print(f" Starting Genesis V6 Condition: {condition_name}")
    print(f" Max Nodes Cap: {max_nodes if max_nodes is not None else 'Unconstrained (Control)'}")
    print(f" Generations: {generations} | Seed: {seed}")
    print(f"=======================================================")

    random.seed(seed)
    np.random.seed(seed)

    orchestrator = V6CoevolutionOrchestrator(
        num_envs=num_envs,
        pop_size_per_env=pop_size_per_env,
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

            # Collect global pool of agents
            all_agents = []
            for pop in orchestrator.agent_populations.values():
                all_agents.extend(pop)

            # Metrics calculation
            nodes = [len(a.genome.nodes) for a in all_agents]
            edges = [len(a.genome.connections) for a in all_agents]
            entropies = [action_entropy(a) for a in all_agents]
            gac_val = gac(all_agents, gen, orchestrator.innovation_birth, persistence_threshold=500)

            # Speciation calculation
            species_list = assign_species(all_agents, species_list, compatibility_threshold=3.0)
            species_count = len(species_list)

            avg_nodes = float(np.mean(nodes))
            avg_edges = float(np.mean(edges))
            avg_entropy = float(np.mean(entropies))

            print(f"Gen {gen:05d} | {condition_name:<11} | Nodes: {avg_nodes:.2f} | "
                  f"Entropy: {avg_entropy:.3f} | GAC: {gac_val:.3f} | Species: {species_count} | "
                  f"ANNEX: {annex_tracker.count} | Edges: {avg_edges:.1f}", flush=True)

            row = [gen, condition_name, f"{avg_nodes:.2f}", f"{avg_entropy:.4f}",
                   f"{gac_val:.4f}", species_count, annex_tracker.count, f"{avg_edges:.2f}"]

            if csv_writers:
                for w in csv_writers:
                    w.writerow(row)
            if csv_files:
                for f in csv_files:
                    f.flush()



def main(generations: int = 10000, log_interval: int = 1000, pop_size_per_env: int = 20, seed: int = 42):
    out_dirs = ['genesis_engine_v6/results', 'v6/results']
    csv_files = []
    writers = []

    for d in out_dirs:
        os.makedirs(d, exist_ok=True)
        path = os.path.join(d, 'constrained_ceiling.csv')
        f = open(path, 'w', newline='')
        w = csv.writer(f)
        w.writerow(['Generation', 'Condition', 'AvgNodes', 'ActionEntropy', 'GAC', 'SpeciesCount', 'ANNEX', 'AvgEdges'])
        csv_files.append(f)
        writers.append(w)

    try:
        # Condition 1: Control (Unconstrained)
        run_condition("Control", max_nodes=None, generations=generations, log_interval=log_interval,
                      pop_size_per_env=pop_size_per_env, seed=seed, csv_writers=writers, csv_files=csv_files)

        # Condition 2: Constrained (Max 52 Nodes)
        run_condition("Constrained", max_nodes=52, generations=generations, log_interval=log_interval,
                      pop_size_per_env=pop_size_per_env, seed=seed, csv_writers=writers, csv_files=csv_files)


        print("\n[SUCCESS] Genesis V6 Constrained Ceiling Ablation Study completed successfully.")

    finally:
        for f in csv_files:
            f.close()


if __name__ == "__main__":
    main(generations=10000, log_interval=1000, pop_size_per_env=20, seed=42)
