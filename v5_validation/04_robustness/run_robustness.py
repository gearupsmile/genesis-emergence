import os
import sys
import json
import pickle
import random
import numpy as np
import scipy.stats as stats
import matplotlib.pyplot as plt

# Ensure root directory is on path
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if root_dir not in sys.path:
    sys.path.append(root_dir)

from genesis_engine_v3.engine.structurally_evolvable_agent import AgentV4
from v5.src.cppn_environment import V5Substrate

def apply_weight_noise(agent, sigma):
    noisy_agent = AgentV4(agent.x, agent.y, agent.genome.copy())
    if sigma > 0:
        for conn in noisy_agent.genome.connections.values():
            if conn.enabled:
                conn.weight += np.random.normal(0, sigma)
    if hasattr(noisy_agent.genome, '_topo_order'):
        delattr(noisy_agent.genome, '_topo_order')
    return noisy_agent

def run_episode_survival(agent, substrate_params, weight_noise_sigma, sensory_noise_sigma, steps=100):
    width, height, f_map, k_map, u_map, v_map = substrate_params
    
    # 1. Apply weight noise
    noisy_agent = apply_weight_noise(agent, weight_noise_sigma)
    noisy_agent.x = random.randint(0, width - 1)
    noisy_agent.y = random.randint(0, height - 1)
    noisy_agent.energy = 1.0
    
    substrate = V5Substrate(width, height, f_map, k_map, u_map, v_map)
    substrate.V = np.random.uniform(0.0, 0.5, (height, width)).astype(np.float32)
    substrate.U = np.random.uniform(0.5, 1.0, (height, width)).astype(np.float32)
    
    survival_time = steps
    for step in range(1, steps + 1):
        if noisy_agent.energy <= 0:
            survival_time = step - 1
            break
            
        # 2. Add sensory noise to fields passed to decide_action
        if sensory_noise_sigma > 0:
            noisy_U = np.clip(substrate.U + np.random.normal(0, sensory_noise_sigma, substrate.U.shape), 0, 1)
            noisy_V = np.clip(substrate.V + np.random.normal(0, sensory_noise_sigma, substrate.V.shape), 0, 1)
            noisy_S = np.clip(substrate.S + np.random.normal(0, sensory_noise_sigma, substrate.S.shape), 0, 1)
            action = noisy_agent.decide_action(noisy_U, noisy_V, noisy_S)
        else:
            action = noisy_agent.step(substrate)
            
        if action == 'S' and hasattr(substrate, 'deposit_secretion'):
            substrate.deposit_secretion(int(noisy_agent.x), int(noisy_agent.y), 0.5)
            
        # Physics update
        substrate.step()
        noisy_agent.energy += substrate.V[int(noisy_agent.y)%substrate.height, int(noisy_agent.x)%substrate.width] * 0.5
        noisy_agent.energy -= 0.02
        
    return survival_time

def main():
    print("--- Running Robustness to Perturbations Validation ---")
    fixed_path = os.path.join(root_dir, "v5_validation", "checkpoints", "fixed_agents.pkl")
    coevolved_path = os.path.join(root_dir, "v5_validation", "checkpoints", "coevolved_agents.pkl")
    
    if not (os.path.exists(fixed_path) and os.path.exists(coevolved_path)):
        print("ERROR: Checkpoint files not found! Please run the experiments first.")
        sys.exit(1)
        
    with open(fixed_path, "rb") as f:
        fixed_agents = pickle.load(f)
    with open(coevolved_path, "rb") as f:
        coevolved_populations = pickle.load(f)
        
    coevolved_agents = []
    for pop in coevolved_populations.values():
        coevolved_agents.extend(pop)
        
    # Sub-sample 5 agents from each group
    random.seed(42)
    np.random.seed(42)
    sample_fixed = random.sample(fixed_agents, 5)
    sample_coevolved = random.sample(coevolved_agents, 5)
    
    # Substrate configuration (Standard Gray-Scott)
    width, height = 50, 50
    f_map = np.full((height, width), 0.055, dtype=np.float32)
    k_map = np.full((height, width), 0.062, dtype=np.float32)
    u_map = np.full((height, width), 1.0, dtype=np.float32)
    v_map = np.full((height, width), 0.4, dtype=np.float32)
    substrate_params = (width, height, f_map, k_map, u_map, v_map)
    
    # Noise combinations: (weight_sigma, sensory_sigma)
    noise_scenarios = [
        (0.0, 0.0),
        (0.1, 0.05),
        (0.2, 0.1),
        (0.3, 0.1)
    ]
    
    results = {
        "fixed": {},
        "coevolved": {}
    }
    
    max_noise_fixed_surv = []
    max_noise_coevolved_surv = []
    
    for w_sigma, s_sigma in noise_scenarios:
        scenario_name = f"W:{w_sigma}_S:{s_sigma}"
        print(f"Testing scenario: {scenario_name}...")
        
        # Test Fixed agents
        fixed_survivals = []
        for agent in sample_fixed:
            # 6 episodes per agent to get 30 episodes total
            for _ in range(6):
                s_t = run_episode_survival(agent, substrate_params, w_sigma, s_sigma)
                fixed_survivals.append(s_t)
                
        # Test Co-evolved agents
        coevolved_survivals = []
        for agent in sample_coevolved:
            for _ in range(6):
                s_t = run_episode_survival(agent, substrate_params, w_sigma, s_sigma)
                coevolved_survivals.append(s_t)
                
        results["fixed"][scenario_name] = {
            "mean": float(np.mean(fixed_survivals)),
            "std": float(np.std(fixed_survivals))
        }
        results["coevolved"][scenario_name] = {
            "mean": float(np.mean(coevolved_survivals)),
            "std": float(np.std(coevolved_survivals))
        }
        
        print(f"  -> Fixed Mean: {np.mean(fixed_survivals):.1f} | Co-evolved Mean: {np.mean(coevolved_survivals):.1f}")
        
        if w_sigma == 0.3 and s_sigma == 0.1:
            max_noise_fixed_surv = fixed_survivals
            max_noise_coevolved_surv = coevolved_survivals
            
    # T-test at maximum noise scenario
    t_stat, p_val = stats.ttest_ind(max_noise_coevolved_surv, max_noise_fixed_surv, equal_var=False)
    results["max_noise_t_stat"] = float(t_stat)
    results["max_noise_p_value"] = float(p_val)
    
    conclusion = ""
    if p_val < 0.05 and np.mean(max_noise_coevolved_surv) > np.mean(max_noise_fixed_surv):
        conclusion = "Co-evolved agents are significantly more robust to noise than fixed-env agents (p < 0.05), validating the decoupling hypothesis."
    else:
        conclusion = "No significant difference in robustness between the two groups under max noise."
        
    results["conclusion"] = conclusion
    
    results_path = os.path.join(root_dir, "v5_validation", "04_robustness", "results.json")
    with open(results_path, "w") as f:
        json.dump(results, f, indent=4)
        
    # Generate bar chart
    scenarios = [f"W:{w}\nS:{s}" for w, s in noise_scenarios]
    fixed_means = [results["fixed"][f"W:{w}_S:{s}"]["mean"] for w, s in noise_scenarios]
    fixed_stds = [results["fixed"][f"W:{w}_S:{s}"]["std"] for w, s in noise_scenarios]
    coevolved_means = [results["coevolved"][f"W:{w}_S:{s}"]["mean"] for w, s in noise_scenarios]
    coevolved_stds = [results["coevolved"][f"W:{w}_S:{s}"]["std"] for w, s in noise_scenarios]
    
    x = np.arange(len(scenarios))
    width = 0.35
    
    plt.figure(figsize=(10, 6))
    plt.bar(x - width/2, fixed_means, width, yerr=fixed_stds, label='Fixed-Env', color='gray', capsize=5)
    plt.bar(x + width/2, coevolved_means, width, yerr=coevolved_stds, label='Co-Evolved', color='blue', capsize=5)
    
    plt.ylabel('Mean Survival Time (Steps)')
    plt.title('Robustness to Structural and Sensory Perturbations')
    plt.xticks(x, scenarios)
    plt.legend()
    plt.ylim(0, 110)
    plt.grid(axis='y', alpha=0.3)
    
    plot_path = os.path.join(root_dir, "v5_validation", "04_robustness", "robustness_plot.png")
    plt.savefig(plot_path)
    plt.close()
    
    print(f"Results saved to {results_path}")
    print(f"Plot saved to {plot_path}")

if __name__ == "__main__":
    main()
