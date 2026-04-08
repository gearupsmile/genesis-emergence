import numpy as np

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from genesis_engine_v3.engine.cppn_genome import CPPNGenome

class CPPNEnvironment:
    def __init__(self, width=50, height=50):
        self.cppn_genome = CPPNGenome()
        self.width = width
        self.height = height
        
        # Init structure
        for _ in range(5):
            self.cppn_genome.add_node_mutation()
        for _ in range(10):
            self.cppn_genome.add_connection_mutation()

    def generate_property_map(self, property_name, min_val, max_val):
        grid = np.zeros((self.width, self.height))
        nodes_len = len(self.cppn_genome.nodes)
        conn_len = len(self.cppn_genome.connections)
        
        for x in range(self.width):
            for y in range(self.height):
                nx = (x / self.width) * 2 - 1
                ny = (y / self.height) * 2 - 1
                
                # Evaluation proxy
                val = np.sin(nx * nodes_len) * np.cos(ny * conn_len)
                mapped_val = min_val + ((val + 1) / 2) * (max_val - min_val)
                grid[x, y] = mapped_val
        return grid

    def get_combined_environment(self):
        return {
            'energy': self.generate_property_map('energy', 0, 100),
            'diffusivity': self.generate_property_map('diffusivity', 0.01, 0.5),
            'kill_rate': self.generate_property_map('kill_rate', 0.03, 0.07)
        }
