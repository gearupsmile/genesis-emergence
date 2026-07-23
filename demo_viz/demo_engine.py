import os
import sys
import random
import numpy as np
import uuid
import Levenshtein

# Ensure we can import from genesis_engine_v3 and v5
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

from demo_viz.demo_config import *
from genesis_engine_v3.engine.cppn_genome import CPPNGenome
from genesis_engine_v3.engine.structurally_evolvable_agent import AgentV4
from v5.src.coevolution import CoevolutionOrchestrator
from v5.src.metrics import compute_lz_complexity_ratio

# --- MONKEY PATCHES FOR DEMO ---

# 1. Update Metabolic Cost Exponent
@property
def patched_metabolic_cost(self):
    return (len(self.connections) ** METABOLIC_COST_EXPONENT) * 0.01

CPPNGenome.metabolic_cost = patched_metabolic_cost

# 2. Update Mutation Rates for Demo Acceleration
original_mutate = CPPNGenome.mutate

def patched_mutate(self):
    if hasattr(self, '_in_map'): delattr(self, '_in_map')
    if hasattr(self, '_input_nodes'): delattr(self, '_input_nodes')
    if hasattr(self, '_output_nodes'): delattr(self, '_output_nodes')
    
    if random.random() < NODE_MUTATION_RATE:
        self.add_node_mutation()
    if random.random() < CONN_MUTATION_RATE:
        self.add_connection_mutation()
    if random.random() < 0.10:
        self.mutate_activation_function()
    if random.random() < 0.80:
        self.mutate_weights()

CPPNGenome.mutate = patched_mutate

# --- ENGINE WRAPPER ---

def get_agent_action_string(agent, substrate, steps=20):
    clone = AgentV4(agent.x, agent.y, agent.genome.copy())
    clone.energy = 1.0
    action_str = ""
    for _ in range(steps):
        action = clone.step(substrate)
        action_str += action
    return action_str

class DualEngine:
    """Runs Left (V4) and Right (V5) worlds in lockstep."""
    
    def __init__(self, seed=42):
        random.seed(seed)
        np.random.seed(seed)
        
        # Left: V4 (Fixed)
        self.left_engine = CoevolutionOrchestrator(num_envs=1, pop_size_per_env=POP_SIZE)
        
        # Right: V5 (Co-evolving)
        self.right_engine = CoevolutionOrchestrator(num_envs=1, pop_size_per_env=POP_SIZE)
        
        self.generation = 0
        
        # Action string histories for behavioral similarity
        self.right_baseline_actions = []
        
        # Oldest agent tracking for trails
        self.left_oldest = None
        self.right_oldest = None
        self.left_trail = []
        self.right_trail = []
        
    def step(self):
        self.generation += 1
        
        # Step both environments
        self.left_engine.step()
        self.right_engine.step()
        
        # Manually increment age for all agents (since V5 step doesn't)
        for env_id in self.left_engine.agent_populations:
            for agent in self.left_engine.agent_populations[env_id]:
                agent.age += 1
        for env_id in self.right_engine.agent_populations:
            for agent in self.right_engine.agent_populations[env_id]:
                agent.age += 1
        
        # Co-evolve Right (V5) every 10 generations to accelerate drift
        if self.generation % 10 == 0:
            self.right_engine.coevolve()
            
        # --- METRICS & TRAIL UPDATES ---
        left_env_id = self.left_engine.environments[0].id
        right_env_id = self.right_engine.environments[0].id
        
        left_pop = self.left_engine.agent_populations[left_env_id]
        right_pop = self.right_engine.agent_populations[right_env_id]
        
        left_sub = self.left_engine.substrates[left_env_id]
        right_sub = self.right_engine.substrates[right_env_id]
        
        # Update oldest agents
        left_pop.sort(key=lambda a: a.age, reverse=True)
        right_pop.sort(key=lambda a: a.age, reverse=True)
        
        if self.left_oldest is None or self.left_oldest not in left_pop:
            self.left_oldest = left_pop[0]
            self.left_trail = []
        self.left_trail.append((self.left_oldest.x, self.left_oldest.y))
        if len(self.left_trail) > 20: self.left_trail.pop(0)
        
        if self.right_oldest is None or self.right_oldest not in right_pop:
            self.right_oldest = right_pop[0]
            self.right_trail = []
        self.right_trail.append((self.right_oldest.x, self.right_oldest.y))
        if len(self.right_trail) > 20: self.right_trail.pop(0)
        
        # Clear trails every 200 simulation steps (we just clear every 200 generations for visual effect)
        if self.generation % 200 == 0:
            self.left_trail = []
            self.right_trail = []

        # Nodes
        left_nodes = np.mean([len(a.genome.nodes) for a in left_pop])
        right_nodes = np.mean([len(a.genome.nodes) for a in right_pop])
        
        # Behavioral string (just use oldest agent for action trace proxy)
        right_action = get_agent_action_string(self.right_oldest, right_sub, steps=20)
        
        similarity = 0.0
        if self.generation <= 500:
            self.right_baseline_actions.append(right_action)
        else:
            # Compare to a random sample from baseline to avoid noise
            if self.right_baseline_actions:
                sample = random.sample(self.right_baseline_actions, min(10, len(self.right_baseline_actions)))
                similarity = max(Levenshtein.ratio(right_action, base) for base in sample)
        
        return {
            'left_nodes': left_nodes,
            'right_nodes': right_nodes,
            'right_similarity': similarity,
            'left_substrate': left_sub,
            'right_substrate': right_sub,
            'left_trail': self.left_trail,
            'right_trail': self.right_trail,
            'left_oldest': self.left_oldest,
            'right_oldest': self.right_oldest,
            'left_pop': left_pop,
            'right_pop': right_pop
        }
