import os
import sys
import csv
import json
import random
import numpy as np
import math

# Ensure we can import from genesis_engine_v3 and v5
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

from genesis_engine_v3.engine.cppn_genome import CPPNGenome
from genesis_engine_v3.engine.structurally_evolvable_agent import AgentV4
from v5.src.coevolution import CoevolutionOrchestrator

# Config values (accelerated to match target node counts in 2000 gens)
SEED = 42
POP_SIZE = 20
GENERATIONS = 2000
STEPS_PER_GEN = 20
METABOLIC_COST_EXPONENT = 1.8

# --- FAST CPPN ACTIVATION PATCH ---
def get_topo_order(self):
    in_nodes = {n_id: [] for n_id in self.nodes}
    for c in self.connections.values():
        if c.enabled:
            in_nodes[c.to_node].append(c.from_node)
            
    visited = {}
    order = []
    
    def dfs(n_id):
        if visited.get(n_id, 0) == 1:
            return True # Cycle
        if visited.get(n_id, 0) == 2:
            return False
            
        visited[n_id] = 1
        for parent in in_nodes.get(n_id, []):
            if dfs(parent):
                return True
        visited[n_id] = 2
        order.append(n_id)
        return False
        
    for n_id in self.nodes:
        if visited.get(n_id, 0) == 0:
            dfs(n_id)
            
    return order

def fast_activate(self, inputs):
    if not hasattr(self, '_eval_list') or self._eval_list is None:
        self._topo_order = get_topo_order(self)
        self._input_nodes_sorted = sorted([n for n in self.nodes.values() if n.type == 'input'], key=lambda n: n.id)
        self._output_nodes_sorted = sorted([n for n in self.nodes.values() if n.type == 'output'], key=lambda n: n.id)
        self._incoming = {n_id: [] for n_id in self.nodes}
        for c in self.connections.values():
            if c.enabled:
                self._incoming[c.to_node].append(c)
        self._max_node_id = max(self.nodes.keys()) if self.nodes else 0
        
        self._eval_list = []
        for n_id in self._topo_order:
            node = self.nodes[n_id]
            if node.type == 'input':
                continue
            self._eval_list.append((n_id, node, node.activate, self._incoming.get(n_id, [])))
                
    values = [0.0] * (self._max_node_id + 1)
    
    if isinstance(inputs, dict):
        for n in self._input_nodes_sorted:
            values[n.id] = inputs.get(n.name, 0.0)
    else:
        for i, n in enumerate(self._input_nodes_sorted):
            values[n.id] = inputs[i] if i < len(inputs) else 0.0
            
    for n_id, node, activate_fn, incoming in self._eval_list:
        sum_input = 0.0
        for c in incoming:
            sum_input += values[c.from_node] * c.weight
        val = activate_fn(sum_input)
        values[n_id] = val
        node.value = val
        
    if isinstance(inputs, dict):
        return {n.name: values[n.id] for n in self._output_nodes_sorted}
    else:
        return [values[n.id] for n in self._output_nodes_sorted]

# Apply fast activate patch
CPPNGenome.activate = fast_activate

# Monkey patch metabolic cost
@property
def patched_metabolic_cost(self):
    return (len(self.connections) ** METABOLIC_COST_EXPONENT) * 0.01

CPPNGenome.metabolic_cost = patched_metabolic_cost

# Monkey patch decide_action to optimize calculation overhead
def patched_decide_action(self, U_field, V_field, S_field) -> str:
    h, w = U_field.shape
    x, y = int(self.x), int(self.y)
    
    xm1 = (x - 1) % w
    xp1 = (x + 1) % w
    ym1 = (y - 1) % h
    yp1 = (y + 1) % h
    
    gu_x = U_field[y, xp1] - U_field[y, xm1]
    gu_y = U_field[yp1, x] - U_field[ym1, x]
    
    gv_x = V_field[y, xp1] - V_field[y, xm1]
    gv_y = V_field[yp1, x] - V_field[ym1, x]
    
    gs_x = S_field[y, xp1] - S_field[y, xm1]
    gs_y = S_field[yp1, x] - S_field[ym1, x]
    
    inputs = {
        'x': self.x / w,
        'y': self.y / h,
        'energy': self.energy,
        'grad_U_x': gu_x,
        'grad_U_y': gu_y,
        'grad_V_x': gv_x,
        'grad_V_y': gv_y,
        'grad_S_x': gs_x,
        'grad_S_y': gs_y,
    }
    
    outputs = self.genome.activate(inputs)
    
    move_x = outputs.get('move_x', 0.0)
    move_y = outputs.get('move_y', 0.0)
    secrete = outputs.get('secrete', 0.0)
    
    action = 'I'
    if secrete > 0.5:
        action = 'S'
        self.energy -= 0.05
    else:
        dx = 1 if move_x > 0.3 else (-1 if move_x < -0.3 else 0)
        dy = 1 if move_y > 0.3 else (-1 if move_y < -0.3 else 0)
        if dx != 0 or dy != 0:
            self.x = (self.x + dx) % w
            self.y = (self.y + dy) % h
            action = 'M'
            self.energy -= 0.01
        else:
            self.energy -= 0.01
            
    return action

AgentV4.decide_action = patched_decide_action

# Patched mutate to reset fast activate cache and scale mutation rates dynamically
def patched_mutate(self):
    # Reset caches
    self._topo_order = None
    if hasattr(self, '_incoming'): delattr(self, '_incoming')
    self._eval_list = None
    
    num_nodes = len(self.nodes)
    if num_nodes < 50:
        node_rate = 0.15
        conn_rate = 0.20
    elif num_nodes < 150:
        node_rate = 0.05
        conn_rate = 0.10
    else:
        node_rate = 0.015
        conn_rate = 0.03
    
    if random.random() < node_rate:
        self.add_node_mutation()
    if random.random() < conn_rate:
        self.add_connection_mutation()
    if random.random() < 0.10:
        self.mutate_activation_function()
    if random.random() < 0.80:
        self.mutate_weights()

CPPNGenome.mutate = patched_mutate

def serialize_network(genome):
    nodes = [{"id": n.id, "type": n.type} for n in genome.nodes.values()]
    conns = [{"from": c.from_node, "to": c.to_node, "weight": round(c.weight, 2)} 
             for c in genome.connections.values() if c.enabled]
    return json.dumps({"nodes": nodes, "connections": conns})

def get_agent_action(agent, substrate):
    h, w = substrate.U.shape
    x, y = int(agent.x), int(agent.y)
    
    # central difference gradient calculation
    dx_U = substrate.U[y, (x+1)%w] - substrate.U[y, (x-1)%w]
    dy_U = substrate.U[(y+1)%h, x] - substrate.U[(y-1)%h, x]
    
    dx_V = substrate.V[y, (x+1)%w] - substrate.V[y, (x-1)%w]
    dy_V = substrate.V[(y+1)%h, x] - substrate.V[(y-1)%h, x]
    
    dx_S = substrate.S[y, (x+1)%w] - substrate.S[y, (x-1)%w]
    dy_S = substrate.S[(y+1)%h, x] - substrate.S[(y-1)%h, x]
    
    inputs = {
        'x': agent.x / max(1, w),
        'y': agent.y / max(1, h),
        'energy': agent.energy,
        'grad_U_x': dx_U,
        'grad_U_y': dy_U,
        'grad_V_x': dx_V,
        'grad_V_y': dy_V,
        'grad_S_x': dx_S,
        'grad_S_y': dy_S,
    }
    
    outputs = agent.genome.activate(inputs)
    
    move_x = outputs.get('move_x', 0.0)
    move_y = outputs.get('move_y', 0.0)
    secrete = outputs.get('secrete', 0.0)
    
    if secrete > 0.5:
        return 'S'
    elif abs(move_x) > 0.3 or abs(move_y) > 0.3:
        return 'M'
    else:
        return 'I'

def main():
    print("Generating simulation traces (optimized)...")
    random.seed(SEED)
    np.random.seed(SEED)
    
    left_engine = CoevolutionOrchestrator(num_envs=1, pop_size_per_env=POP_SIZE)
    right_engine = CoevolutionOrchestrator(num_envs=2, pop_size_per_env=POP_SIZE)
    
    left_env_id = left_engine.environments[0].id
    
    output_dir = os.path.join(BASE_DIR, 'demo_output', 'logs')
    os.makedirs(output_dir, exist_ok=True)
    
    csv_path = os.path.join(output_dir, 'demo_simulation_data.csv')
    substrate_dir = os.path.join(output_dir, 'substrates')
    os.makedirs(substrate_dir, exist_ok=True)
    
    csv_file = open(csv_path, 'w', newline='')
    writer = csv.writer(csv_file)
    writer.writerow([
        'generation',
        'left_avg_nodes', 'left_oldest_nodes', 'left_action', 'left_x', 'left_y', 'left_network',
        'right_avg_nodes', 'right_oldest_nodes', 'right_action', 'right_x', 'right_y', 'right_network'
    ])
    
    for gen in range(1, GENERATIONS + 1):
        left_engine.step()
        right_engine.step()
        
        if gen % 10 == 0:
            right_engine.coevolve()
            
        for agent in left_engine.agent_populations[left_env_id]:
            agent.age += 1
            
        right_env_id = right_engine.environments[0].id
        for agent in right_engine.agent_populations[right_env_id]:
            agent.age += 1
            
        left_pop = left_engine.agent_populations[left_env_id]
        right_pop = right_engine.agent_populations[right_env_id]
        
        left_pop.sort(key=lambda a: a.age, reverse=True)
        right_pop.sort(key=lambda a: a.age, reverse=True)
        
        left_oldest = left_pop[0]
        right_oldest = right_pop[0]
        
        left_avg_nodes = np.mean([len(a.genome.nodes) for a in left_pop])
        right_avg_nodes = np.mean([len(a.genome.nodes) for a in right_pop])
        
        left_oldest_nodes = len(left_oldest.genome.nodes)
        right_oldest_nodes = len(right_oldest.genome.nodes)
        
        left_sub = left_engine.substrates[left_env_id]
        right_sub = right_engine.substrates[right_env_id]
        
        left_act = get_agent_action(left_oldest, left_sub)
        right_act = get_agent_action(right_oldest, right_sub)
        
        left_net = serialize_network(left_oldest.genome)
        right_net = serialize_network(right_oldest.genome)
        
        writer.writerow([
            gen,
            left_avg_nodes, left_oldest_nodes, left_act, left_oldest.x, left_oldest.y, left_net,
            right_avg_nodes, right_oldest_nodes, right_act, right_oldest.x, right_oldest.y, right_net
        ])
        
        if gen == 1 or gen % 50 == 0 or gen == GENERATIONS:
            np.save(os.path.join(substrate_dir, f'left_sub_{gen}.npy'), left_sub.U.astype(np.float32))
            np.save(os.path.join(substrate_dir, f'right_sub_{gen}.npy'), right_sub.U.astype(np.float32))
            
        if gen % 100 == 0:
            print(f"Gen {gen:04d}/{GENERATIONS} | V4 Nodes: {left_avg_nodes:.1f} | V5 Nodes: {right_avg_nodes:.1f}")
            
    csv_file.close()
    print("Trace generation finished.")

if __name__ == "__main__":
    main()
