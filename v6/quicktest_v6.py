"""
quicktest_v6.py - Verification Script for Genesis V6
Runs 100 generations of both Control and Constrained conditions to verify clean execution.
"""

import sys
import os

# Add root directory to sys.path
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if root_dir not in sys.path:
    sys.path.append(root_dir)

from genesis_engine_v6.experiments.run_constrained_ceiling import main

def run_quicktest():
    print("=" * 60)
    print(" Starting Genesis V6 Quicktest (100 Generations)")
    print(" Verifying Control and Constrained conditions...")
    print("=" * 60)

    # Run for 100 generations with log_interval=50
    main(generations=100, log_interval=50, pop_size_per_env=10, seed=42)

    print("\n[VERIFICATION PASSED] Quicktest executed with zero errors.")

if __name__ == "__main__":
    run_quicktest()
