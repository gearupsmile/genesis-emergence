"""
Batch Experiment Runner
Executes multiple seeds of run_sham_comparison.py in parallel using threads.
(Uses ThreadPoolExecutor because each job IS a subprocess - multiprocessing.Pool
 hangs on Windows when workers themselves spawn child processes.)
"""
import subprocess
import argparse
import os
import time
from typing import List, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, '../../'))


def run_single_experiment(args: Tuple[str, int, int, str]) -> str:
    mode, seed, generations, base_log_dir = args

    log_dir = os.path.join(base_log_dir, f"seed_{seed}")
    os.makedirs(log_dir, exist_ok=True)

    cmd = [
        "python",
        os.path.join(SCRIPT_DIR, "run_sham_comparison.py"),
        "--mode", mode,
        "--generations", str(generations),
        "--seed", str(seed),
        "--log_dir", log_dir
    ]

    print(f"[{mode.upper()} S{seed}] Starting...", flush=True)
    start_time = time.time()

    result = subprocess.run(cmd, capture_output=True, text=True, cwd=PROJECT_ROOT)

    duration = time.time() - start_time

    if result.returncode == 0:
        msg = f"[{mode.upper()} S{seed}] Done in {duration:.1f}s"
    else:
        msg = (f"[{mode.upper()} S{seed}] FAILED (code {result.returncode})\n"
               f"{result.stderr[-500:]}")

    print(msg, flush=True)
    return msg


def run_batch(generations: int, seeds: List[int], workers: int, base_dir: str):
    tasks = []
    for seed in seeds:
        tasks.append(("real", seed, generations, os.path.join(base_dir, "real")))
    for seed in seeds:
        tasks.append(("sham", seed, generations, os.path.join(base_dir, "sham")))

    print(f"Queueing {len(tasks)} experiments | Workers={workers} | Gens={generations} | Seeds={seeds}", flush=True)
    start_time = time.time()

    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {executor.submit(run_single_experiment, t): t for t in tasks}
        for future in as_completed(futures):
            try:
                future.result()
            except Exception as e:
                task = futures[future]
                print(f"[ERROR] {task[0]} S{task[1]}: {e}", flush=True)

    total = time.time() - start_time
    print(f"\nAll done. Total time: {total:.1f}s ({total/60:.1f} min)", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--generations", type=int, default=1000)
    parser.add_argument("--seeds", type=int, nargs="+", default=[42, 123, 456])
    parser.add_argument("--workers", type=int, default=3)
    parser.add_argument("--out_dir", type=str, default="logs/batch_run")
    args = parser.parse_args()

    run_batch(args.generations, args.seeds, args.workers, args.out_dir)
