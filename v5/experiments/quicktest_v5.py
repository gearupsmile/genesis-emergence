import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from v5.experiments.run_v5 import run_experiment

if __name__ == "__main__":
    print("Running V5 Quicktest (100 generations)...")
    run_experiment(generations=100)
    print("Quicktest completed successfully!")
