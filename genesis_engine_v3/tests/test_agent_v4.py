import sys
import os
import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from engine.structurally_evolvable_agent import AgentV4
from engine.substrate import Substrate

def test_agent_v4_simulation():
    substrate = Substrate(width=50, height=50, enable_secretion=True)
    agent = AgentV4(25, 25)
    
    initial_nodes = len(agent.genome.nodes)
    initial_connections = len(agent.genome.connections)
    
    action_counts = {'M': 0, 'S': 0, 'I': 0}
    
    for step in range(1000):
        # Periodically perturb fields to provide gradients
        if step % 20 == 0:
            substrate.U += np.random.rand(50, 50) * 0.05
            substrate.V += np.random.rand(50, 50) * 0.05
            
        action = agent.step(substrate)
        action_counts[action] = action_counts.get(action, 0) + 1
        
        # Mutate through reproduction to verify growth
        if step % 100 == 0 and step > 0:
            agent = agent.reproduce()
            
    final_nodes = len(agent.genome.nodes)
    final_connections = len(agent.genome.connections)
    
    print("Action distribution:", action_counts)
    print(f"Genome size: Nodes {initial_nodes} -> {final_nodes}")
    print(f"Connections {initial_connections} -> {final_connections}")
    
    assert sum(action_counts.values()) == 1000
    print("test_agent_v4 passed successfully.")

if __name__ == '__main__':
    test_agent_v4_simulation()
