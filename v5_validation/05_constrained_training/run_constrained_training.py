import sys, os, json, random, numpy as np
sys.path.insert(0, '.')
from v5.src.coevolution import CoevolutionOrchestrator
from genesis_engine_v3.engine.structurally_evolvable_agent import AgentV4

MAX_NODES = 52
MAX_GENS = 500
LOG_INTERVAL = 50
SEED = 42
random.seed(SEED); np.random.seed(SEED)
out_dir = "v5_validation/05_constrained_training"
os.makedirs(out_dir, exist_ok=True)

def cap_genome_nodes(genome, max_nodes=MAX_NODES):
    if len(genome.nodes) <= max_nodes: return
    exc = len(genome.nodes) - max_nodes
    hidden = sorted([nid for nid, n in genome.nodes.items() if n.type == "hidden"])
    rids = set(hidden[:exc])
    genome.nodes = {i:n for i,n in genome.nodes.items() if i not in rids}
    genome.connections = {i:c for i,c in genome.connections.items() if c.from_node not in rids and c.to_node not in rids}
    genome.next_node_id = max(genome.nodes.keys()) + 1
    for attr in ["_topo_order","_input_nodes","_output_nodes","_in_map_tuples"]:
        if hasattr(genome, attr): delattr(genome, attr)

orch = CoevolutionOrchestrator(num_envs=3, pop_size_per_env=10)
log_path = os.path.join(out_dir, "progress.log")

with open(log_path, "w") as log:
    log.write("Constrained Training max_nodes=%d seed=%d\n" % (MAX_NODES, SEED))
    log.write("Gen,AvgNodes,MaxNodes,AvgConns,AvgEnergy,EnvSolved\n")
    for gen in range(1, MAX_GENS+1):
        orch.step()
        for env in orch.environments:
            for a in orch.agent_populations[env.id]:
                cap_genome_nodes(a.genome)
        if gen % LOG_INTERVAL == 0:
            if gen % 100 == 0: orch.coevolve()
            an, ac, ae = [], [], []
            for env in orch.environments:
                for a in orch.agent_populations[env.id]:
                    an.append(len(a.genome.nodes))
                    ac.append(len(a.genome.connections))
                    ae.append(a.energy)
            line = "%d,%.2f,%d,%.2f,%.4f,%d\n" % (gen, np.mean(an), max(an), np.mean(ac), np.mean(ae), sum(1 for e in orch.environments if e.fitness>0))
            log.write(line); log.flush()
            print(line.strip())

print("Done. Saving summary...")
all_nodes = []
for env in orch.environments:
    for a in orch.agent_populations[env.id]:
        all_nodes.append(len(a.genome.nodes))
summary = {
    "generations_run": MAX_GENS,
    "max_nodes_allowed": MAX_NODES,
    "max_nodes_reached": max(all_nodes) if all_nodes else 0,
    "environments_solved": sum(1 for e in orch.environments if e.fitness > 0),
    "total_environments": len(orch.environments)
}
with open(os.path.join(out_dir, "final_summary.json"), "w") as f:
    json.dump(summary, f, indent=4)
print("Test 5 complete.")
