import os, sys, json, pickle, random
import numpy as np
import scipy.stats as stats
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if root_dir not in sys.path:
    sys.path.append(root_dir)
from genesis_engine_v3.engine.structurally_evolvable_agent import AgentV4

def dtw(t1, t2):
    n, m = len(t1), len(t2)
    mat = np.full((n+1, m+1), np.inf)
    mat[0, 0] = 0.0
    for i in range(1, n+1):
        for j in range(1, m+1):
            cost = np.hypot(t1[i-1][0]-t2[j-1][0], t1[i-1][1]-t2[j-1][1])
            mat[i, j] = cost + min(mat[i-1, j], mat[i, j-1], mat[i-1, j-1])
    return mat[n, m]

def cliffs_delta(x, y):
    n1, n2 = len(x), len(y)
    c = sum(1 for v1 in x for v2 in y if v1 > v2) - sum(1 for v1 in x for v2 in y if v1 < v2)
    return c / (n1 * n2)

def run_episode(agent, env, steps=100):
    sub = env.build_substrate(50, 50)
    clone = AgentV4(random.randint(0, 49), random.randint(0, 49), agent.genome.copy())
    clone.energy = 1.0
    traj, acts = [], []
    for _ in range(steps):
        traj.append((clone.x, clone.y))
        act = clone.step(sub)
        acts.append(act)
        if clone.energy > 0:
            clone.energy += sub.V[int(clone.y)%50, int(clone.x)%50] * 0.5
        clone.energy -= 0.02
    return traj, acts, max(0.0, clone.energy)

def main():
    print("--- Running Behavioral Metrics ---")
    root = root_dir
    with open(os.path.join(root, "v5_validation", "checkpoints", "fixed_agents.pkl"), "rb") as f:
        fixed_agents = pickle.load(f)
    with open(os.path.join(root, "v5_validation", "checkpoints", "coevolved_agents.pkl"), "rb") as f:
        coev_pop = pickle.load(f)
    coevolved_agents = []
    for pop in coev_pop.values():
        coevolved_agents.extend(pop)
    with open(os.path.join(root, "v5_validation", "checkpoints", "coevolved_envs.pkl"), "rb") as f:
        envs = pickle.load(f)
    test_env = envs[0]
    ref_traj = [(i*50/99, i*50/99) for i in range(100)]

    random.seed(42)
    np.random.seed(42)

    metrics = {"fixed_env": {"dtw": [], "action_entropy": [], "energy_efficiency": []},
               "coevolved": {"dtw": [], "action_entropy": [], "energy_efficiency": []}}

    for grp_name, agents in [("fixed_env", fixed_agents), ("coevolved", coevolved_agents)]:
        for ep in range(100):
            agent = random.choice(agents)
            traj, acts, final_e = run_episode(agent, test_env)
            metrics[grp_name]["dtw"].append(dtw(traj, ref_traj))
            acts_arr = np.array(acts)
            unique, counts = np.unique(acts_arr, return_counts=True)
            probs = counts / len(acts_arr)
            entropy = -sum(p*np.log2(p) for p in probs) if len(probs) > 0 else 0.0
            metrics[grp_name]["action_entropy"].append(entropy)
            metrics[grp_name]["energy_efficiency"].append(final_e / max(1e-8, 1.0))
        print(f"{grp_name}: 100 episodes done")

    results = {}
    for metric_name in ["dtw", "action_entropy", "energy_efficiency"]:
        x, y = metrics["fixed_env"][metric_name], metrics["coevolved"][metric_name]
        if len(np.unique(x)) > 1 and len(np.unique(y)) > 1:
            u_stat, p_val = stats.mannwhitneyu(x, y, alternative='two-sided')
        else:
            u_stat, p_val = 0.0, 1.0
        cd = cliffs_delta(x, y)
        results[metric_name] = {
            "fixed_mean": float(np.mean(x)), "fixed_std": float(np.std(x)),
            "coevolved_mean": float(np.mean(y)), "coevolved_std": float(np.std(y)),
            "mannwhitney_u": float(u_stat), "p_value": float(p_val),
            "cliffs_delta": float(cd)
        }
        print(f"  {metric_name}: fixed={np.mean(x):.3f}±{np.std(x):.3f}, "
              f"coev={np.mean(y):.3f}±{np.std(y):.3f}, p={p_val:.5e}, d={cd:.3f}")

    out_dir = os.path.join(root, "v5_validation", "02_behavioral_metrics")
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "results.json"), "w") as f:
        json.dump(results, f, indent=4)

    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    labels_map = {"dtw": "DTW Distance", "action_entropy": "Action Entropy", "energy_efficiency": "Energy Efficiency"}
    for idx, mn in enumerate(["dtw", "action_entropy", "energy_efficiency"]):
        data = [metrics["fixed_env"][mn], metrics["coevolved"][mn]]
        bp = axes[idx].boxplot(data, tick_labels=["Fixed", "Coevolved"], patch_artist=True)
        for patch, color in zip(bp['boxes'], ['lightblue', 'lightgreen']):
            patch.set_facecolor(color)
        axes[idx].set_title(labels_map[mn])
        axes[idx].grid(axis='y', alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, "metrics_plots.png"))
    plt.close()
    print("Test 2 complete.")

if __name__ == "__main__":
    main()
