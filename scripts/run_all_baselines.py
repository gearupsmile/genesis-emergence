import subprocess
import os
import sys

def main():
    seeds = [42, 123, 456]
    generations = 10000
    
    scripts = [
        ('experiments/run_baseline_fixed.py', 'Fixed Constraints'),
        ('experiments/run_baseline_random.py', 'Random Search'),
        ('experiments/run_baseline_mapelites.py', 'MAP-Elites'),
        ('experiments/run_novelty_baseline_final.py', 'Novelty Search')
    ]
    
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    
    for script, name in scripts:
        script_path = os.path.join(root_dir, script)
        if not os.path.exists(script_path):
            print(f"[ERROR] Script not found: {script_path}")
            continue
            
        for seed in seeds:
            print(f"\n{'='*50}")
            print(f"Running {name} [Seed: {seed}]")
            print(f"{'='*50}")
            
            cmd = [sys.executable, script_path, '--seed', str(seed), '--generations', str(generations)]
            
            try:
                # Run the baseline script
                result = subprocess.run(cmd, cwd=root_dir, check=True)
                print(f"[SUCCESS] {name} seed {seed} completed.")
            except subprocess.CalledProcessError as e:
                print(f"[ERROR] {name} seed {seed} failed with error {e.returncode}.")
                sys.exit(1)

    print("\n" + "="*50)
    print("All baselines completed successfully!")
    print("Results saved to results/baselines/")
    print("="*50)

if __name__ == "__main__":
    main()
