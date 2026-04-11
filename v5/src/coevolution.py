import uuid
import random
import numpy as np

from genesis_engine_v3.engine.cppn_genome import CPPNGenome
from genesis_engine_v3.engine.structurally_evolvable_agent import AgentV4
from .cppn_environment import CPPNEnvironment, V5Substrate

class EnvironmentGenome:
    def __init__(self, cppn_genome=None):
        self.id = str(uuid.uuid4())
        if cppn_genome is None:
            self.cppn_genome = CPPNGenome()
            self.cppn_genome.add_input_node('x')
            self.cppn_genome.add_input_node('y')
            self.cppn_genome.add_output_node('f', activation='sigmoid')
            self.cppn_genome.add_output_node('k', activation='sigmoid')
            self.cppn_genome.add_output_node('diff_U', activation='sigmoid')
            self.cppn_genome.add_output_node('diff_V', activation='sigmoid')
            # Starter connections
            self.cppn_genome.add_connection(0, 2, random.uniform(-1, 1))
            self.cppn_genome.add_connection(1, 3, random.uniform(-1, 1))
        else:
            self.cppn_genome = cppn_genome
            
        self.age = 0
        self.fitness = 0.0

    def mutate(self):
        self.cppn_genome.mutate()
        
    def crossover(self, other):
        # Simplify crossover for CPPN; we'll rely on mutation primarily
        pass
        
    def copy(self):
        env = EnvironmentGenome(self.cppn_genome.copy())
        env.age = self.age
        env.fitness = self.fitness
        return env
        
    def build_substrate(self, width=50, height=50):
        gen = CPPNEnvironment(self.cppn_genome, width, height)
        # mapped to typical Gray-Scott parameters
        f_map = gen.generate_property_map('f', 0.01, 0.1)
        k_map = gen.generate_property_map('k', 0.04, 0.07)
        u_map = gen.generate_property_map('diff_U', 0.8, 1.0)
        v_map = gen.generate_property_map('diff_V', 0.4, 0.6)
        
        return V5Substrate(width, height, f_map, k_map, u_map, v_map)


class POETMinimalCriteria:
    @staticmethod
    def is_viable(env_genome, agent_population, width=50, height=50, num_test_agents=20, test_steps=100):
        if not agent_population:
            return False
            
        substrate = env_genome.build_substrate(width, height)
        test_agents = random.sample(agent_population, min(len(agent_population), num_test_agents))
        
        # Deep copy agents to test
        clones = []
        for a in test_agents:
            clone = AgentV4(a.x, a.y, a.genome.copy())
            clone.energy = 1.0
            clones.append(clone)
            
        # Simulate briefly
        for _ in range(test_steps):
            substrate.step()
            for agent in clones:
                agent.step(substrate)
                
        energies = [a.energy for a in clones]
        mean_e = np.mean(energies)
        var_e = np.var(energies)
        
        # Minimal Criteria: the environment must not be overly lethal nor trivial
        if mean_e < -test_steps * 0.05:  # Nearly dead
            return False
        if var_e < 0.001:  # Completely homogenous, no challenge
            return False
            
        return True


class GoalSwitching:
    @staticmethod
    def should_transfer(agent, source_substrate, target_substrate, test_steps=20):
        """
        Evaluate if agent transfers to new target.
        Short test steps for performance.
        """
        clone_s = AgentV4(agent.x, agent.y, agent.genome.copy())
        clone_s.energy = 1.0
        
        clone_t = AgentV4(agent.x, agent.y, agent.genome.copy())
        clone_t.energy = 1.0
        
        for _ in range(test_steps):
            clone_s.step(source_substrate)
            clone_t.step(target_substrate)
            
        # Transfer if standard absolute performance is better in target
        # Energy correlates with successful navigation / secretion loops
        return clone_t.energy > (clone_s.energy + 0.05)


class CoevolutionOrchestrator:
    def __init__(self, num_envs=5, pop_size_per_env=20):
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
            self.substrates[env.id] = env.build_substrate()
            
            pop = [AgentV4(random.randint(0, 49), random.randint(0, 49)) for _ in range(pop_size_per_env)]
            self.agent_populations[env.id] = pop

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
                    # Gain energy from the environment to create an evolutionary gradient!
                    agent.energy += sub.V[int(agent.y), int(agent.x)] * 0.5
                    
            # Evaluate fitness and selection within this environment
            pop.sort(key=lambda a: a.energy, reverse=True)
            
            # Record avg energy as env fitness
            env.fitness = np.mean([a.energy for a in pop])
            
            survivors = pop[:len(pop)//2]
            
            for a in survivors:
                a.energy = min(1.0, max(0.0, a.energy + 0.2))  # Base recovery
                # Randomize positions slightly to avoid complete clustering
                a.x = (a.x + random.choice([-1, 0, 1])) % sub.width
                a.y = (a.y + random.choice([-1, 0, 1])) % sub.height
                
            new_pop = list(survivors)
            while len(new_pop) < self.pop_size_per_env:
                parent = random.choice(survivors)
                child = parent.reproduce()
                # Hypermutation driven by co-evolutionary arms race (POET-specific pressure)
                for _ in range(4):
                    child.genome.mutate()
                new_pop.append(child)
                
            self.agent_populations[env.id] = new_pop
            
    def coevolve(self):
        """
        Periodically handles environment replacement and agent transfers.
        Should be called every N generations (e.g., 500)
        """
        # 1. Goal Switching / Transfer Agents
        for src_env in self.environments:
            for tgt_env in self.environments:
                if src_env.id == tgt_env.id: continue
                # Test top agent from src
                src_pop = self.agent_populations[src_env.id]
                best_agent = sorted(src_pop, key=lambda a: a.energy, reverse=True)[0]
                
                if GoalSwitching.should_transfer(best_agent, self.substrates[src_env.id], self.substrates[tgt_env.id]):
                    # Transfer a copy
                    self.agent_populations[tgt_env.id].append(AgentV4(best_agent.x, best_agent.y, best_agent.genome.copy()))
                    self.total_transfers += 1
        
        # Trim inflated populations
        for env_id in self.agent_populations:
            pop = self.agent_populations[env_id]
            if len(pop) > self.pop_size_per_env:
                pop.sort(key=lambda a: a.energy, reverse=True)
                self.agent_populations[env_id] = pop[:self.pop_size_per_env]

        # 2. Environment Mutation & Replacement
        self.environments.sort(key=lambda e: e.fitness)
        # Replace the worst environment if it's too stagnant
        worst_env = self.environments[0]
        best_env = self.environments[-1]
        
        # Create mutation of best
        mutated_env = best_env.copy()
        mutated_env.mutate()
        
        # Test Minimal Criteria
        all_agents = []
        for pop in self.agent_populations.values():
            all_agents.extend(pop)
            
        if POETMinimalCriteria.is_viable(mutated_env, all_agents):
            # Accept replacement
            self.environments[0] = mutated_env
            self.substrates[mutated_env.id] = mutated_env.build_substrate()
            self.agent_populations[mutated_env.id] = self.agent_populations.pop(worst_env.id)
            self.total_mutations += 1
            return mutated_env # Returns the new env if accepted
        return None
