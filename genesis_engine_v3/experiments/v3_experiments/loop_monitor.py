"""
Continuous Monitor for 50k Batch Run
Runs check_progress periodically and formats output as requested.
"""
import time
import subprocess
import os
import glob
from datetime import datetime

TARGET_GENS = 50000
LOG_DIR = "logs/50k_batch_fresh/"
STALL_TIMEOUT = 300 # 5 minutes

def print_status(real_gen, sham_gen, real_epc, sham_epc, real_lz, sham_lz, status_msg):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    avg_gen = (real_gen + sham_gen) / 2
    
    epc_diff = real_epc - sham_epc
    
    print(f"⏱️ [{timestamp}] Generation {avg_gen:.0f}/{TARGET_GENS}")
    print(f"📊 Real EPC: {real_epc:.2f} | Sham EPC: {sham_epc:.2f} | Diff: {epc_diff:.2f}")
    print(f"🔬 Real LZ: {real_lz:.3f} | Sham LZ: {sham_lz:.3f}")
    print(f"🚦 Status: [{status_msg}]")
    print("-" * 50)

def restart_stalled_run(filepath):
    """Attempt to extract params from filepath and restart."""
    print(f"Attempting to restart stalled run: {filepath}")
    # Extract seed and mode from path: logs/50k_batch/real/seed_42/...
    parts = filepath.replace("\\", "/").split("/")
    
    mode = None
    seed = None
    
    for p in parts:
        if p in ['real', 'sham']:
            mode = p
        if p.startswith('seed_'):
            try:
                seed = int(p.split('_')[1])
            except:
                pass
                
    if mode and seed is not None:
        cmd = [
            "python", "experiments/v3_experiments/run_sham_comparison.py",
            "--mode", mode,
            "--generations", str(TARGET_GENS),
            "--seed", str(seed),
            "--log_dir", os.path.dirname(filepath)
        ]
        print(f"Restarting with command: {' '.join(cmd)}")
        # Start detached
        subprocess.Popen(cmd)
        return True
    return False

def monitor_loop():
    print(f"Starting continuous monitoring for {LOG_DIR}...")
    complete = False
    
    while not complete:
        try:
            # Run the check script and capture output to parse
            result = subprocess.run(
                ["python", "experiments/v3_experiments/check_progress.py", "--log_dir", LOG_DIR, "--target", str(TARGET_GENS)],
                capture_output=True, text=True
            )
            
            output = result.stdout
            
            # Parse metrics from output if possible
            real_gen, sham_gen = 0, 0
            real_epc, sham_epc = 0.0, 0.0
            real_lz, sham_lz = 0.0, 0.0
            
            for line in output.split('\n'):
                if "[REAL]" in line:
                    parts = line.split('|')
                    if len(parts) >= 4:
                        try:
                            real_gen = float(parts[1].split(':')[1].split('(')[0].strip())
                            real_epc = float(parts[2].split(':')[1].strip())
                            real_lz = float(parts[3].split(':')[1].strip())
                        except: pass
                elif "[SHAM]" in line:
                    parts = line.split('|')
                    if len(parts) >= 4:
                        try:
                            sham_gen = float(parts[1].split(':')[1].split('(')[0].strip())
                            sham_epc = float(parts[2].split(':')[1].strip())
                            sham_lz = float(parts[3].split(':')[1].strip())
                        except: pass
                        
            # Check for stalled runs in raw Python
            current_time = time.time()
            all_files = glob.glob(os.path.join(LOG_DIR, "**", "*.csv"), recursive=True)
            stalled_files = []
            for f in all_files:
                if current_time - os.path.getmtime(f) > STALL_TIMEOUT:
                    stalled_files.append(f)
                    
            if stalled_files:
                status_msg = f"Running ({len(stalled_files)} stalled)"
                for f in stalled_files:
                    restart_stalled_run(f)
            else:
                status_msg = "Running"
                
            if "Completion: 20/20" in output:
                complete = True
                status_msg = "Complete"
                
            print_status(real_gen, sham_gen, real_epc, sham_epc, real_lz, sham_lz, status_msg)
            
            if complete:
                break
                
            # Sleep for 1 minute before next check
            time.sleep(60)
            
        except KeyboardInterrupt:
            print("Monitoring stopped.")
            break
        except Exception as e:
            print(f"Monitor error: {e}")
            time.sleep(60)
            
    if complete:
        print("\nAll runs complete! Launching analysis...")
        subprocess.run([
            "python", "analysis/compare_runs_multi.py", 
            "--real", os.path.join(LOG_DIR, "real"),
            "--sham", os.path.join(LOG_DIR, "sham"),
            "--output", "50k_comparison.png",
            "--stats"
        ])

if __name__ == "__main__":
    monitor_loop()
