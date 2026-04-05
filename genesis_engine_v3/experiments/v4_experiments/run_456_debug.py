import sys
import os
import csv
import random
import time
import numpy as np
from collections import deque

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from engine.genesis_engine import GenesisEngine
from engine.structurally_evolvable_agent import AgentV4

def _lz76_complexity(s: str) -> int:
    n = len(s)
    if n == 0: return 0
    i, k, l = 0, 1, 1
    c, k_max = 1, 1
    while True:
        if i + k - 1 < n and l + k - 1 < n and s[i + k - 1] == s[l + k - 1]:
            k += 1
            if l + k > n:
                c += 1
                break
        else:
            if k > k_max: k_max = k
            i += 1
            if i == l:
                c += 1
                l += k_max
                if l + 1 > n: break
                i = 0
                k = 1
                k_max = 1
            else:
                k = 1
    return c

print("Starting Seed 456 Real DEBUG...")

seed = 456
random.seed(seed)
np.random.seed(seed)
if hasattr(os, 'environ'): os.environ['PYTHONHASHSEED'] = str(seed)

lineage_histories = {}
original_step = AgentV4.step
def tracking_step(self, substrate):
    action = original_step(self, substrate)
    if self.lineage_id not in lineage_histories:
        lineage_histories[self.lineage_id] = deque(maxlen=200)
    lineage_histories[self.lineage_id].append(action)
    return action
    
AgentV4.step = tracking_step

engine = GenesisEngine(
    population_size=100, 
    mutation_rate=0.2, 
    agent_type='cppn', 
    enable_secretion=True,
    compatibility_threshold=0.3,
    stagnation_limit=25
)

# Run a few generations with prints to track progress
for gen in range(500):
    start = time.time()
    engine.run_cycle()
    end = time.time()
    if (gen+1) % 50 == 0:
        print(f"Gen {gen+1}: {end-start:.4f}s, PopSize: {len(engine.population)}, Sp: {len(engine.species_list)}")

print("Done with debug script.")
