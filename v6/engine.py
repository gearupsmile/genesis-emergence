import random
import numpy as np
from v5.src.coevolution import CoevolutionOrchestrator, EnvironmentGenome
from v6.agent import AgentV6
from v6.substrate import create_v6_substrate

class V6Orchestrator(CoevolutionOrchestrator):
    def __init__(self, config, num_envs=5, pop_size_per_env=100):
        self.config = config
        self.num_envs = num_envs
        self.pop_size_per_env = pop_size_per_env
        self.environments = []
        self.substrates = {}
        self.agent_populations = {}
        self.total_transfers = 0
        self.total_mutations = 0
        
        # Generate initial environments and populations
        for _ in range(num_envs):
            env = EnvironmentGenome()
            self.environments.append(env)
            self.substrates[env.id] = create_v6_substrate(env, width=50, height=50, config=self.config)
            
            pop = [AgentV6(random.randint(0, 49), random.randint(0, 49), config=self.config) for _ in range(pop_size_per_env)]
            self.agent_populations[env.id] = pop

    def _get_avg_neighbour_energy(self, agent, pop, radius=5, width=50, height=50):
        # Calculate distance with periodic boundary wrap
        energies = []
        for other in pop:
            if other.id == agent.id:
                continue
            dx = min(abs(agent.x - other.x), width - abs(agent.x - other.x))
            dy = min(abs(agent.y - other.y), height - abs(agent.y - other.y))
            if dx <= radius and dy <= radius:
                energies.append(other.energy)
        
        if not energies:
            return 0.0
        return np.mean(energies)

    def step(self):
        """Advance simulation by 1 generation for all environments."""
        for env in self.environments:
            sub = self.substrates[env.id]
            pop = self.agent_populations[env.id]
            
            env.age += 1
            
            # Simulation loop per generation
            for _ in range(20):
                sub.step()
                for agent in pop:
                    agent.step(sub)
                    # Gain energy from the environment
                    agent.energy += sub.V[int(agent.y), int(agent.x)] * 0.5
                    
            # Exp 4 logic vs Baseline Truncation
            if self.config.relative_reproduction:
                # Relative reproduction logic
                next_pop = []
                for agent in pop:
                    avg_n_energy = self._get_avg_neighbour_energy(agent, pop, radius=5, width=sub.width, height=sub.height)
                    
                    # Survive if energy > 0 (or some minimal threshold)
                    if agent.energy > 0:
                        agent.energy = min(1.0, max(0.0, agent.energy + 0.2)) # Base recovery
                        agent.x = (agent.x + random.choice([-1, 0, 1])) % sub.width
                        agent.y = (agent.y + random.choice([-1, 0, 1])) % sub.height
                        next_pop.append(agent)
                        
                        # Reproduce if condition met
                        if agent.energy > avg_n_energy * 1.2 and agent.energy > 5.0:
                            child = agent.reproduce()
                            # Hypermutation
                            for _ in range(4):
                                child.genome.mutate()
                            next_pop.append(child)
                            
                # Trim or pad to maintain rough pop size if it explodes
                if len(next_pop) > self.pop_size_per_env * 2:
                    next_pop.sort(key=lambda a: a.energy, reverse=True)
                    next_pop = next_pop[:self.pop_size_per_env * 2]
                elif len(next_pop) == 0 and pop:
                    # Extinction prevention fallback
                    best = max(pop, key=lambda a: a.energy)
                    best.energy = 1.0
                    next_pop.append(best)
                    
                self.agent_populations[env.id] = next_pop
                env.fitness = np.mean([a.energy for a in pop])
            else:
                # V5 Default Truncation logic
                pop.sort(key=lambda a: a.energy, reverse=True)
                env.fitness = np.mean([a.energy for a in pop])
                
                survivors = pop[:len(pop)//2]
                for a in survivors:
                    a.energy = min(1.0, max(0.0, a.energy + 0.2))
                    a.x = (a.x + random.choice([-1, 0, 1])) % sub.width
                    a.y = (a.y + random.choice([-1, 0, 1])) % sub.height
                    
                new_pop = list(survivors)
                while len(new_pop) < self.pop_size_per_env:
                    parent = random.choice(survivors)
                    child = parent.reproduce()
                    for _ in range(4):
                        child.genome.mutate()
                    new_pop.append(child)
                    
                self.agent_populations[env.id] = new_pop

    def _should_transfer(self, agent, source_substrate, target_substrate, test_steps=20):
        clone_s = AgentV6(agent.x, agent.y, agent.genome.copy(), config=self.config)
        clone_s.energy = 1.0
        
        clone_t = AgentV6(agent.x, agent.y, agent.genome.copy(), config=self.config)
        clone_t.energy = 1.0
        
        for _ in range(test_steps):
            clone_s.step(source_substrate)
            clone_t.step(target_substrate)
            
        return clone_t.energy > (clone_s.energy + 0.05)

    def _is_viable_env(self, env_genome, agent_population, width=50, height=50, num_test_agents=20, test_steps=100):
        if not agent_population:
            return False
            
        substrate = create_v6_substrate(env_genome, width, height, config=self.config)
        test_agents = random.sample(agent_population, min(len(agent_population), num_test_agents))
        
        clones = []
        for a in test_agents:
            clone = AgentV6(a.x, a.y, a.genome.copy(), config=self.config)
            clone.energy = 1.0
            clones.append(clone)
            
        for _ in range(test_steps):
            substrate.step()
            for agent in clones:
                agent.step(substrate)
                
        energies = [a.energy for a in clones]
        mean_e = np.mean(energies)
        var_e = np.var(energies)
        
        if mean_e < -test_steps * 0.05:
            return False
        if var_e < 0.001:
            return False
            
        return True

    def coevolve(self):
        # 1. Goal Switching / Transfer Agents
        for src_env in self.environments:
            for tgt_env in self.environments:
                if src_env.id == tgt_env.id: continue
                # Test top agent from src
                src_pop = self.agent_populations[src_env.id]
                best_agent = sorted(src_pop, key=lambda a: a.energy, reverse=True)[0]
                
                if self._should_transfer(best_agent, self.substrates[src_env.id], self.substrates[tgt_env.id]):
                    # Transfer a copy
                    self.agent_populations[tgt_env.id].append(AgentV6(best_agent.x, best_agent.y, best_agent.genome.copy(), lineage_id=best_agent.lineage_id, config=self.config))
                    self.total_transfers += 1
        
        # Trim inflated populations
        for env_id in self.agent_populations:
            pop = self.agent_populations[env_id]
            if len(pop) > self.pop_size_per_env:
                pop.sort(key=lambda a: a.energy, reverse=True)
                self.agent_populations[env_id] = pop[:self.pop_size_per_env]

        # 2. Environment Mutation & Replacement
        self.environments.sort(key=lambda e: e.fitness)
        worst_env = self.environments[0]
        best_env = self.environments[-1]
        
        mutated_env = best_env.copy()
        mutated_env.mutate()
        
        all_agents = []
        for pop in self.agent_populations.values():
            all_agents.extend(pop)
            
        if self._is_viable_env(mutated_env, all_agents):
            self.environments[0] = mutated_env
            self.substrates[mutated_env.id] = create_v6_substrate(mutated_env, width=50, height=50, config=self.config)
            self.agent_populations[mutated_env.id] = self.agent_populations.pop(worst_env.id)
            self.total_mutations += 1
            return mutated_env
        return None
