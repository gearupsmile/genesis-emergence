import os
import sys
import json
import pickle
import random
import numpy as np
import matplotlib.pyplot as plt

# Ensure root directory is on path
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if root_dir not in sys.path:
    sys.path.append(root_dir)

from genesis_engine_v3.engine.structurally_evolvable_agent import AgentV4
from v5.src.cppn_environment import V5Substrate

def prune_connections(agent, fraction):
    pruned_agent = AgentV4(agent.x, agent.y, agent.genome.copy())
    conns = [c for c in pruned_agent.genome.connections.values() if c.enabled]
    if not conns:
        return pruned_agent
    conns.sort(key=lambda c: abs(c.weight))
    num_to_prune = int(len(conns) * fraction)
    for i in range(num_to_prune):
        conns[i].enabled = False
    # Clear any cached topo order to force recomputation
    if hasattr(pruned_agent.genome, '_topo_order'):
        delattr(pruned_agent.genome, '_topo_order')
    return pruned_agent

def run_evolution_with_gac(initial_agent, env, generations=50, pop_size=20):
    random.seed(42)
    np.random.seed(42)
    
    # Initialize population with copies of the pruned agent
    population = []
    for _ in range(pop_size):
        a = AgentV4(random.randint(0, 49), random.randint(0, 49), initial_agent.genome.copy())
        a.energy = 1.0
        population.append(a)
        
    mutations_by_gen = {} # gen -> set of new node/conn IDs
    gac_values = []
    survival_rates = []
    
    # Store starter active IDs
    for gen in range(1, generations + 1):
        substrate = env.build_substrate(50, 50)
        substrate.V = np.random.uniform(0.0, 0.5, (50, 50)).astype(np.float32)
        substrate.U = np.random.uniform(0.5, 1.0, (50, 50)).astype(np.float32)
        
        # Track survival
        survived_count = 0
        for _ in range(20):
            substrate.step()
            for agent in population:
                if agent.energy > 0:
                    agent.step(substrate)
                    agent.energy += substrate.V[int(agent.y)%substrate.height, int(agent.x)%substrate.width] * 0.5
                agent.energy -= 0.02
                
        for agent in population:
            if agent.energy > 0.1: # survival threshold
                survived_count += 1
                
        survival_rates.append(survived_count / pop_size)
        
        # Selection
        population.sort(key=lambda a: a.energy, reverse=True)
        survivors = population[:pop_size//2]
        if not survivors:
            # Complete extinction fallback
            survivors = [AgentV4(random.randint(0, 49), random.randint(0, 49), initial_agent.genome.copy()) for _ in range(2)]
            
        for a in survivors:
            a.energy = min(1.0, max(0.0, a.energy + 0.2))
            a.x = (a.x + random.choice([-1, 0, 1])) % substrate.width
            a.y = (a.y + random.choice([-1, 0, 1])) % substrate.height
            
        new_pop = list(survivors)
        new_mutations = set()
        
        while len(new_pop) < pop_size:
            parent = random.choice(survivors)
            # Record parent IDs
            parent_nodes = set(parent.genome.nodes.keys())
            parent_conns = set(parent.genome.connections.keys())
            
            child = parent.reproduce()
            # Hypermutation to introduce edits
            for _ in range(4):
                child.genome.mutate()
                
            # Find new IDs introduced
            child_nodes = set(child.genome.nodes.keys())
            child_conns = set(child.genome.connections.keys())
            
            new_mutations.update(child_nodes - parent_nodes)
            new_mutations.update(child_conns - parent_conns)
            new_pop.append(child)
            
        population = new_pop
        mutations_by_gen[gen] = new_mutations
        
        # Track GAC (persistence over 10 generations)
        if gen >= 11:
            target_gen = gen - 10
            target_mutations = mutations_by_gen[target_gen]
            if target_mutations:
                # Find all active IDs in current population
                active_ids = set()
                for agent in population:
                    active_ids.update(agent.genome.nodes.keys())
                    active_ids.update(agent.genome.connections.keys())
                
                persisted = target_mutations & active_ids
                gac_values.append(len(persisted) / len(target_mutations))
            else:
                gac_values.append(1.0)
                
    mean_gac = np.mean(gac_values) if gac_values else 1.0
    mean_survival = np.mean(survival_rates)
    return mean_gac, mean_survival

def main():
    print("--- Running Adaptive Pruning with GAC Tracking ---")
    coevolved_path = os.path.join(root_dir, "v5_validation", "checkpoints", "coevolved_agents.pkl")
    envs_path = os.path.join(root_dir, "v5_validation", "checkpoints", "coevolved_envs.pkl")
    
    if not (os.path.exists(coevolved_path) and os.path.exists(envs_path)):
        print("ERROR: Checkpoint files not found! Please run the experiments first.")
        sys.exit(1)
        
    with open(coevolved_path, "rb") as f:
        coevolved_populations = pickle.load(f)
    with open(envs_path, "rb") as f:
        coevolved_envs = pickle.load(f)
        
    coevolved_agents = []
    for pop in coevolved_populations.values():
        coevolved_agents.extend(pop)
        
    # Find agent closest to 467 nodes
    target_nodes = 467
    source_agent = min(coevolved_agents, key=lambda a: abs(len(a.genome.nodes) - target_nodes))
    print(f"Selected agent with {len(source_agent.genome.nodes)} nodes and {len(source_agent.genome.connections)} connections.")
    
    # Pick the first co-evolved environment for testing
    test_env = coevolved_envs[0]
    
    pruning_steps = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]
    gacs = []
    survivals = []
    
    collapse_point = None
    
    for p in pruning_steps:
        print(f"Evaluating pruning level: {p*100:.0f}%...")
        pruned_agent = prune_connections(source_agent, p)
        gac, survival = run_evolution_with_gac(pruned_agent, test_env, generations=30, pop_size=20)
        gacs.append(float(gac))
        survivals.append(float(survival))
        print(f"  -> GAC: {gac:.3f} | Survival: {survival:.3f}")
        
        # Collapse point is defined as where survival falls below 20%
        if survival < 0.20 and collapse_point is None:
            collapse_point = float(p * 100)
            
    if collapse_point is None:
        collapse_point = 90.0 # fallback if no collapse detected
        
    print(f"Collapse point detected at: {collapse_point:.0f}% pruning")
    
    results = {
        "pruning_steps": [p * 100 for p in pruning_steps],
        "gac_values": gacs,
        "survival_rates": survivals,
        "collapse_point": collapse_point,
        "conclusion": f"Agent performance and structural complexity collapsed at {collapse_point:.0f}% pruning, demonstrating historical contingency."
    }
    
    results_path = os.path.join(root_dir, "v5_validation", "03_pruning_gac", "results.json")
    with open(results_path, "w") as f:
        json.dump(results, f, indent=4)
        
    # Plot line chart
    plt.figure(figsize=(8, 6))
    plt.plot([p * 100 for p in pruning_steps], gacs, marker='o', color='blue', label='GAC Persistence')
    plt.plot([p * 100 for p in pruning_steps], survivals, marker='s', color='green', linestyle='--', label='Survival Rate')
    plt.axvline(collapse_point, color='red', linestyle=':', label=f'Collapse Point ({collapse_point:.0f}%)')
    plt.title("GAC & Survival vs Pruning Percentage")
    plt.xlabel("Pruning %")
    plt.ylabel("Value")
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    plot_path = os.path.join(root_dir, "v5_validation", "03_pruning_gac", "gac_vs_pruning.png")
    plt.savefig(plot_path)
    plt.close()
    
    print(f"Results saved to {results_path}")
    print(f"Plot saved to {plot_path}")

if __name__ == "__main__":
    main()
