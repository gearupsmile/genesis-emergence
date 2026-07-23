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

def run_evaluation(agents, env, steps=100):
    substrate = env.build_substrate(50, 50)
    clones = []
    for a in agents:
        clone = AgentV4(random.randint(0, 49), random.randint(0, 49), a.genome.copy())
        clone.energy = 1.0
        clones.append(clone)
    for _ in range(steps):
        substrate.step()
        for clone in clones:
            if clone.energy > 0:
                clone.step(substrate)
                clone.energy += substrate.V[int(clone.y) % substrate.height, int(clone.x) % substrate.width] * 0.5
            clone.energy -= 0.02
    return np.array([max(0.0, c.energy) for c in clones])

def main():
    print("--- Running PATA-EC Validation ---")
    root = root_dir
    with open(os.path.join(root, "v5_validation", "checkpoints", "fixed_agents.pkl"), "rb") as f:
        fixed_agents = pickle.load(f)
    with open(os.path.join(root, "v5_validation", "checkpoints", "coevolved_agents.pkl"), "rb") as f:
        coevolved_populations = pickle.load(f)
    with open(os.path.join(root, "v5_validation", "checkpoints", "coevolved_envs.pkl"), "rb") as f:
        coevolved_envs = pickle.load(f)

    coevolved_agents = []
    for pop in coevolved_populations.values():
        coevolved_agents.extend(pop)

    print(f"Loaded {len(fixed_agents)} fixed-env agents (avg nodes: {np.mean([len(a.genome.nodes) for a in fixed_agents]):.1f})")
    print(f"Loaded {len(coevolved_agents)} co-evolved agents (avg nodes: {np.mean([len(a.genome.nodes) for a in coevolved_agents]):.1f})")
    print(f"Loaded {len(coevolved_envs)} co-evolved environments.")

    groups = {
        "fixed_env": fixed_agents,
        "coevolved": coevolved_agents,
    }

    all_results = {}
    valid_env_indices = list(range(len(coevolved_envs)))

    for group_name, group_agents in groups.items():
        env_perf = {}
        for idx, env in enumerate(coevolved_envs):
            perf = run_evaluation(group_agents, env, steps=100)
            std_p = np.std(perf)
            if std_p >= 0.05:
                env_perf[idx] = perf

        if len(env_perf) < 2:
            env_perf = {idx: run_evaluation(group_agents, env, steps=100) for idx, env in enumerate(coevolved_envs)}

        correlations = []
        env_ids = list(env_perf.keys())
        for i in range(len(env_ids)):
            for j in range(i + 1, len(env_ids)):
                corr, _ = stats.spearmanr(env_perf[env_ids[i]], env_perf[env_ids[j]])
                if not np.isnan(corr):
                    correlations.append(corr)

        mean_corr = np.mean(correlations) if correlations else 0.0
        if len(correlations) > 1:
            t_stat, p_val = stats.ttest_1samp(correlations, 0.0)
        else:
            t_stat, p_val = 0.0, 1.0

        print(f"{group_name}: Mean Spearman r={mean_corr:.4f}, p={p_val:.5e}")

        conclusion = ""
        if p_val < 0.05 and abs(mean_corr) < 0.5:
            conclusion = "Environments demand distinct behaviors (low cross-env correlation)"
        elif mean_corr > 0.8:
            conclusion = "High cross-environment correlation - environments are functionally similar"
        else:
            conclusion = "Moderate or insignificant divergence"

        all_results[group_name] = {
            "correlations": correlations,
            "mean_correlation": float(mean_corr),
            "p_value": float(p_val),
            "conclusion": conclusion
        }

    # Cross-group: subsample to equal sizes, compare rank-ordering within each environment
    cross_corrs = []
    n_sample = min(len(fixed_agents), len(coevolved_agents))
    for idx in valid_env_indices:
        fixed_perf = run_evaluation(fixed_agents, coevolved_envs[idx], steps=100)
        coev_perf = run_evaluation(coevolved_agents, coevolved_envs[idx], steps=100)
        fixed_sorted = np.sort(fixed_perf)[-n_sample:]
        coev_sorted = np.sort(coev_perf)[-n_sample:]
        corr, _ = stats.spearmanr(fixed_sorted, coev_sorted)
        if not np.isnan(corr):
            cross_corrs.append(corr)
    cross_mean = np.mean(cross_corrs) if cross_corrs else 0.0
    all_results["cross_group"] = {
        "correlations": cross_corrs,
        "mean_correlation": float(cross_mean),
        "note": "Spearman correlation between fixed and coevolved agent rankings within each environment (subsampled to equal size)"
    }
    print(f"Cross-group within-env corr: mean={cross_mean:.4f}")

    out_dir = os.path.join(root, "v5_validation", "01_pata_ec")
    os.makedirs(out_dir, exist_ok=True)

    with open(os.path.join(out_dir, "results.json"), "w") as f:
        json.dump(all_results, f, indent=4)

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    for ax, (gname, gres) in zip(axes, [(k, v) for k, v in all_results.items() if k != "cross_group"]):
        corrs = gres["correlations"]
        ax.hist(corrs, bins=5, edgecolor='black', color='skyblue', alpha=0.7)
        ax.axvline(gres["mean_correlation"], color='red', linestyle='dashed', linewidth=2,
                   label=f'Mean: {gres["mean_correlation"]:.3f}')
        ax.set_title(f"{gname} Agents\nCross-Env Correlations")
        ax.set_xlabel("Spearman r")
        ax.set_ylabel("Frequency")
        ax.legend()
        ax.grid(axis='y', alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, "correlation_histogram.png"))
    plt.close()
    print("Test 1 complete.")

if __name__ == "__main__":
    main()
