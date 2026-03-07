"""
Master Script: Run All Baselines
Executes the four baseline experiments for 3 seeds each (42, 123, 456).
Generates 10k generations of data for Table 4.
"""

import sys
import subprocess
from pathlib import Path
import time
import argparse
import os

def run_baseline(script_path, seed, generations=10000):
    """Run a single baseline configuration."""
    cmd = [
        sys.executable,
        str(script_path),
        '--seed', str(seed),
        '--generations', str(generations)
    ]
    
    print(f"Running: {script_path.name} (Seed={seed})...")
    start = time.time()
    
    # We set PYTHONPATH to include genesis_engine_v2 root
    env = os.environ.copy()
    root_dir = Path(__file__).parent.parent
    env['PYTHONPATH'] = str(root_dir / 'genesis_engine_v2')
    
    try:
        # Run process
        result = subprocess.run(
            cmd,
            env=env,
            capture_output=True,
            text=True
        )
        
        duration = time.time() - start
        
        if result.returncode == 0:
            print(f"  [PASS] Completed in {duration:.1f}s")
            return True
        else:
            print(f"  [FAIL] Failed with code {result.returncode}")
            print("  Output tail:")
            print("\n".join(result.stdout.splitlines()[-10:]))
            print("  Error tail:")
            print("\n".join(result.stderr.splitlines()[-10:]))
            return False
            
    except Exception as e:
        print(f"  [ERROR] Execution failed: {e}")
        return False

def main():
    print("=" * 60)
    print("GENESIS EMERGENCE: BASELINE EXECUTION")
    print("=" * 60)
    
    parser = argparse.ArgumentParser()
    parser.add_argument('--test', action='store_true', help='Run short test validation')
    args = parser.parse_args()
    
    # Configuration
    seeds = [42, 123, 456]
    generations = 10000
    
    if args.test:
        print("[TEST MODE] Running 10 generations for verification")
        generations = 10
        seeds = [42] # Just one seed
    
    # Paths
    experiments_dir = Path(__file__).parent.parent / 'experiments'
    baselines_dir = experiments_dir / 'baselines'
    
    scripts = [
        # Script Name, Description
        ('run_novelty_baseline_final.py', 'Novelty Search'),
        ('run_baseline_mapelites.py', 'MAP-Elites'), 
        ('run_baseline_random.py', 'Random Search'),
        ('run_baseline_fixed.py', 'Fixed Constraints')
    ]
    
    # Validate scripts exist
    for script_name, _ in scripts:
        path = baselines_dir / script_name
        if not path.exists():
            print(f"[ERROR] Script not found: {path}")
            return
            
    print(f"Configuration: {generations} generations, Seeds: {seeds}")
    print(f"Total Runs: {len(scripts) * len(seeds)}")
    print("-" * 60)
    
    failures = []
    
    for script_name, description in scripts:
        print(f"\nMetric: {description}")
        print("-" * 30)
        script_path = baselines_dir / script_name
        
        for seed in seeds:
            success = run_baseline(script_path, seed, generations)
            if not success:
                failures.append(f"{description} (Seed {seed})")
                
    print("\n" + "=" * 60)
    if failures:
        print(f"completed with {len(failures)} FAILURES:")
        for f in failures:
            print(f"  - {f}")
        sys.exit(1)
    else:
        print("ALL BASELINES COMPLETED SUCCESSFULLY")
        sys.exit(0)

if __name__ == '__main__':
    main()
