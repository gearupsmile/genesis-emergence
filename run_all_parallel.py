import subprocess
import sys
import os

def run_task(cmd):
    print(f"[*] Starting: {cmd}")
    process = subprocess.Popen(cmd, shell=True)
    return process

if __name__ == '__main__':
    commands = [
        "python v5/experiments/run_validation_v5_seeds.py 42",
        "python v5/experiments/run_validation_v5_seeds.py 123",
        "python v5/experiments/run_validation_v5_seeds.py 456",
        "python v4/experiments/run_baseline_comparison.py 42",
        "python v4/experiments/run_baseline_comparison.py 123",
        "python v4/experiments/run_baseline_comparison.py 456"
    ]
    
    print("===================================================")
    print("Spawning 6 parallel processes to massively speed up execution...")
    print("This will execute all V4 and V5 runs simultaneously!")
    print("CPU usage will be high. Please wait for completion.")
    print("===================================================")
    
    processes = []
    for cmd in commands:
        processes.append(run_task(cmd))
        
    # Wait for all to finish
    for p in processes:
        p.wait()
        
    print("\nAll 6 concurrent validation runs finished!")
    print("Now compiling statistical analysis and plotting...")
    
    # Run analysis
    subprocess.run("python v5/experiments/analyze_v5_vs_v4.py", shell=True)
    
    print("===================================================")
    print("Parallel Suite Finished! Check docs/v5_v4_comparison.png")
    print("===================================================")
