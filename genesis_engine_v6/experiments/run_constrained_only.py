"""
run_constrained_only.py
Runs the Constrained (max_nodes=52) condition for 10,000 generations independently.
"""

import sys
import os
import csv

root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if root_dir not in sys.path:
    sys.path.append(root_dir)

from genesis_engine_v6.experiments.run_constrained_ceiling import run_condition

def main():
    out_dirs = ['genesis_engine_v6/results', 'v6/results']
    csv_files = []
    writers = []

    for d in out_dirs:
        os.makedirs(d, exist_ok=True)
        path = os.path.join(d, 'constrained_only.csv')
        f = open(path, 'w', newline='')
        w = csv.writer(f)
        w.writerow(['Generation', 'Condition', 'AvgNodes', 'ActionEntropy', 'GAC', 'SpeciesCount', 'ANNEX', 'AvgEdges'])
        csv_files.append(f)
        writers.append(w)

    try:
        run_condition("Constrained", max_nodes=52, generations=10000, log_interval=100,
                      pop_size_per_env=20, seed=42, csv_writers=writers, csv_files=csv_files)
        print("\n[SUCCESS] Constrained condition run completed.")
    finally:
        for f in csv_files:
            f.close()

if __name__ == "__main__":
    main()
