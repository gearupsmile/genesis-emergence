import random
import numpy as np

# Dynamically importing V4 equivalents from V3 shared engine space
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from genesis_engine_v3.engine.structurally_evolvable_agent import AgentV4

class EnvironmentGenome:
    def __init__(self, params=None):
        self.params = params or {
            'diffusion_rate': random.uniform(0.01, 0.5),
            'secretion_decay': random.uniform(0.01, 0.2),
            'energy_injection': random.uniform(5.0, 50.0),
            'obstacle_density': random.uniform(0.0, 0.3)
        }
        self.fitness = 0.0
        self.age = 0
        self.id = id(self)

    def mutate(self):
        new_params = self.params.copy()
        key = random.choice(list(new_params.keys()))
        new_params[key] *= random.uniform(0.8, 1.2)
        return EnvironmentGenome(new_params)

    def crossover(self, other):
        new_params = {}
        for k in self.params:
            new_params[k] = self.params[k] if random.random() < 0.5 else other.params[k]
        return EnvironmentGenome(new_params)

    def copy(self):
        return EnvironmentGenome(self.params.copy())

class POETMinimalCriteria:
    @staticmethod
    def is_viable(env_genome, agent_population, num_test_agents=20, test_steps=100):
        if not agent_population:
            return True
        test_agents = random.sample(agent_population, min(len(agent_population), num_test_agents))
        performances = []
        for agent in test_agents:
            # Simulate a brief interaction in this environment for speed
            base_perf = (env_genome.params['energy_injection'] * 0.1) - (env_genome.params['obstacle_density'] * 5)
            # Use connection size via genome length or mock
            connections_len = len(agent.genome.connections) if hasattr(agent, 'genome') and hasattr(agent.genome, 'connections') else 10
            perf = base_perf + (connections_len * 0.01) + random.uniform(-1, 1)
            performances.append(perf)
        
        var = np.var(performances)
        mean = np.mean(performances)
        # Goldilocks zone: not too hard, not too easy
        return mean > -5.0 and var > 0.1

class GoalSwitching:
    @staticmethod
    def should_transfer(agent, source_env, target_env, threshold=1.3):
        connections_len = len(agent.genome.connections) if hasattr(agent, 'genome') and hasattr(agent.genome, 'connections') else 10
        source_perf = (source_env.params['energy_injection'] * 0.1) + (connections_len * 0.01)
        target_perf = (target_env.params['energy_injection'] * 0.1) + (connections_len * 0.01)
        return target_perf > (source_perf * threshold)

    @staticmethod
    def transfer(agent, target_env, agent_populations):
        agent_populations[target_env.id].append(AgentV4(agent.x, agent.y, genome=agent.genome.copy() if getattr(agent, 'genome', None) else None, lineage_id=getattr(agent, 'lineage_id', None)))

class CoevolutionOrchestrator:
    def __init__(self, num_environments=5, agents_per_env=20):
        self.environments = [EnvironmentGenome() for _ in range(num_environments)]
        self.agent_populations = {}
        for env in self.environments:
            self.agent_populations[env.id] = [AgentV4(x=0, y=0) for _ in range(agents_per_env)]
        self.max_envs = num_environments

    def step(self, generation):
        # 1. Evolve agents
        for env in self.environments:
            pop = self.agent_populations.get(env.id, [])
            if not pop: continue
            
            for agent in pop:
                # Morph agent slightly
                if hasattr(agent, 'genome'):
                    if random.random() < 0.05 and hasattr(agent.genome, 'add_node_mutation'):
                        agent.genome.add_node_mutation()
                    if random.random() < 0.1 and hasattr(agent.genome, 'add_connection_mutation'):
                        agent.genome.add_connection_mutation()
                
                connections_len = len(agent.genome.connections) if hasattr(agent, 'genome') and hasattr(agent.genome, 'connections') else 10
                agent.fitness = (env.params['energy_injection'] * 0.1) + connections_len
            
            # Simple reproduction (top 50% clone)
            pop.sort(key=lambda a: getattr(a, 'fitness', 0), reverse=True)
            survivors = pop[:max(1, len(pop)//2)]
            new_pop = []
            for a in survivors:
                new_pop.append(a)
                new_pop.append(AgentV4(a.x, a.y, genome=a.genome.copy() if getattr(a, 'genome', None) else None, lineage_id=getattr(a, 'lineage_id', None)))
            self.agent_populations[env.id] = new_pop
            
            env.age += 1
            env.fitness = np.mean([getattr(a, 'fitness', 0) for a in self.agent_populations[env.id]])

        # 2. Co-evolutionary events
        if generation > 0 and generation % 50 == 0:
            self._mutate_environments()
            self._goal_switching()

    def _mutate_environments(self):
        self.environments.sort(key=lambda e: e.fitness, reverse=True)
        if len(self.environments) >= self.max_envs:
            dropped = self.environments.pop()
            if dropped.id in self.agent_populations:
                del self.agent_populations[dropped.id]
        
        if not self.environments: return
        top_env = self.environments[0]
        new_env = top_env.mutate()
        
        if POETMinimalCriteria.is_viable(new_env, self.agent_populations.get(top_env.id, [])):
            self.environments.append(new_env)
            self.agent_populations[new_env.id] = [AgentV4(a.x, a.y, genome=a.genome.copy() if getattr(a, 'genome', None) else None, lineage_id=getattr(a, 'lineage_id', None)) for a in self.agent_populations.get(top_env.id, [])]

    def _goal_switching(self):
        for source_env in self.environments:
            pop = self.agent_populations.get(source_env.id, [])
            if not pop: continue
            best_agent = max(pop, key=lambda a: getattr(a, 'fitness', 0))
            for target_env in self.environments:
                if source_env.id != target_env.id:
                    if GoalSwitching.should_transfer(best_agent, source_env, target_env):
                        GoalSwitching.transfer(best_agent, target_env, self.agent_populations)
                        break
