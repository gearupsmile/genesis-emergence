import sys
import os
import random
import numpy as np

# Ensure root directory is on the path so we can import from genesis_engine_v3 and v5
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if root_dir not in sys.path:
    sys.path.append(root_dir)

from v5.experiments.run_v5 import main

if __name__ == "__main__":
    print("Running V5 Baseline (Seed 42) for 500 generations...")
    np.random.seed(42)
    random.seed(42)
    main(generations=500, log_interval=100, num_envs=5, pop_size=100)
