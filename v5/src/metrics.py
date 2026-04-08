import numpy as np
import random
import hashlib
from genesis_engine_v3.engine.structurally_evolvable_agent import AgentV4

def compute_pata_ec(agent_population, test_env_genome, num_test_agents=20, test_steps=50):
    """
    Performance of All Transferred Agents - Enhanced Criterion (PATA-EC).
    Evaluates the novelty/usefulness of a new environment by running agents in it
    and analyzing the variance in performance, penalized heavily if it perfectly
    correlates with existing performance (meaning it's just universally easier/harder 
    without actually requiring new skills).
    """
    if not agent_population:
        return 0.0
        
    substrate = test_env_genome.build_substrate(50, 50)
    test_agents = random.sample(agent_population, min(len(agent_population), num_test_agents))
    
    clones = []
    initial_energies = []
    for a in test_agents:
        clone = AgentV4(a.x, a.y, a.genome.copy())
        clone.energy = 1.0
        clones.append(clone)
        initial_energies.append(a.energy) # Base performance proxy
        
    for _ in range(test_steps):
        substrate.step()
        for agent in clones:
            agent.step(substrate)
            
    final_energies = [a.energy for a in clones]
    variance = np.var(final_energies)
    
    std_init = np.std(initial_energies)
    std_final = np.std(final_energies)
    
    if std_init == 0 or std_final == 0:
        corr = 0.0
    else:
        corr = np.corrcoef(initial_energies, final_energies)[0, 1]
        
    if np.isnan(corr):
        corr = 0.0
        
    novelty = variance * (1.0 - corr)
    return novelty

class ANNEX:
    """
    Accumulated Novel Environments Explored (ANNEX).
    Maintains a count of distinct, viable environments generated and "solved".
    """
    def __init__(self):
        self.count = 0
        self.fingerprints = set()
        
    def _hash_env(self, env_genome):
        """Creates a stable hash of the CPPN structure and weights."""
        conns = ""
        for _, conn in sorted(env_genome.cppn_genome.connections.items()):
            conns += f"{conn.from_node}-{conn.to_node}:{conn.weight:.2f};"
        return hashlib.md5(conns.encode('utf-8')).hexdigest()
        
    def record_environment(self, env_genome, agents_solved=True):
        """
        Record environment if agents solve it. Returns True if distinctly novel.
        """
        if not agents_solved:
            return False
            
        fp = self._hash_env(env_genome)
        if fp not in self.fingerprints:
            self.fingerprints.add(fp)
            self.count += 1
            return True
        return False
