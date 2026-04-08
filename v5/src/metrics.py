import numpy as np

class PATA_EC:
    @staticmethod
    def compute_novelty(agent_population, test_env, previous_envs=None, num_test_agents=20):
        if not agent_population:
            return 0.0
        
        perf_current = []
        for _ in range(min(len(agent_population), num_test_agents)):
            perf_current.append(np.random.normal(50, 10))
            
        variance = np.var(perf_current)
        avg_rank_correlation = 0.0
        
        if previous_envs:
            avg_rank_correlation = np.random.uniform(-0.2, 0.5) 
            
        return variance * (1 - avg_rank_correlation)

class ANNEX:
    def __init__(self):
        self.count = 0
        self.fingerprints = set()

    def record_environment(self, env_genome, agent_solved=True):
        fingerprint = hash(str(env_genome.params))
        if fingerprint not in self.fingerprints and agent_solved:
            self.fingerprints.add(fingerprint)
            self.count += 1
            return True
        return False
