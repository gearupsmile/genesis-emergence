"""
quicktest_transfer_shock.py - 100-Generation Quicktest for Phase 2 Transfer Shock Experiment
"""

import sys
import os

root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if root_dir not in sys.path:
    sys.path.append(root_dir)

from genesis_engine_v6.experiments.run_transfer_shock import main

if __name__ == '__main__':
    print("Executing Quicktest (100 generations per condition)...")
    main(num_generations=100, log_interval=50, seed=42)
    print("Quicktest completed successfully!")
