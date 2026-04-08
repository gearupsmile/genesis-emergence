import sys
import os

root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if root_dir not in sys.path:
    sys.path.append(root_dir)

from v5.experiments.run_v5 import main

if __name__ == "__main__":
    print("Running Quick Test for Genesis V5 Co-evolution Orchestrator...")
    try:
        # Run extremely brief simulation to verify logic
        main(generations=100, log_interval=25, num_envs=2, pop_size=20)
        print("Quick test completed without runtime errors. Everything is functional!")
    except Exception as e:
        print(f"Quick test encountered an error: {e}")
        sys.exit(1)
