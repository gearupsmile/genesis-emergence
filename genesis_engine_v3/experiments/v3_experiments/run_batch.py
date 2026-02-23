"""
Batch Experiment Runner
Executes multiple seeds of run_sham_comparison.py in parallel.
"""
import subprocess
import argparse
import os
import multiprocessing
import time
from typing import List, Tuple

def run_single_experiment(args: Tuple[str, int, int, str]) -> None:
    mode, seed, generations, base_log_dir = args
    
    # Construct specific log directory for this seed
    log_dir = os.path.join(base_log_dir, f"seed_{seed}")
    os.makedirs(log_dir, exist_ok=True)
    
    cmd = [
        "python", "experiments/v3_experiments/run_sham_comparison.py",
        "--mode", mode,
        "--generations", str(generations),
        "--seed", str(seed),
        "--log_dir", log_dir
    ]
    
    print(f"[{mode.upper()} S{seed}] Starting...")
    start_time = time.time()
    
    # Run command
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    duration = time.time() - start_time
    
    if result.returncode == 0:
        print(f"[{mode.upper()} S{seed}] Completed in {duration:.1f}s")
    else:
        print(f"[{mode.upper()} S{seed}] FAILED with code {result.returncode}")
        print(result.stderr)

def run_batch(generations: int, seeds: List[int], workers: int, base_dir: str):
    tasks = []
    
    # Prepare tasks for Real
    real_dir = os.path.join(base_dir, "real")
    for seed in seeds:
        tasks.append(("real", seed, generations, real_dir))
        
    # Prepare tasks for Sham
    sham_dir = os.path.join(base_dir, "sham")
    for seed in seeds:
        tasks.append(("sham", seed, generations, sham_dir))
        
    print(f"Main: Queueing {len(tasks)} experiments (Workers: {workers})")
    print(f"Generations: {generations}")
    print(f"Seeds: {seeds}")
    
    start_time = time.time()
    
    with multiprocessing.Pool(processes=workers) as pool:
        pool.map(run_single_experiment, tasks)
        
    total_time = time.time() - start_time
    print(f"\nBatch Complete. Total time: {total_time:.1f}s")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--generations", type=int, default=1000)
    parser.add_argument("--seeds", type=int, nargs="+", default=[42, 123, 456])
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--out_dir", type=str, default="logs/batch_run")
    
    args = parser.parse_args()
    
    run_batch(args.generations, args.seeds, args.workers, args.out_dir)
