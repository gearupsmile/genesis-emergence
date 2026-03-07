"""
Progress Monitor for 50k Batch Run
Checks the completion percentage, EPC, and LZ of running experiments.
"""
import os
import argparse
import pandas as pd
import glob
import time

def check_progress(log_dir: str, target_gens: int = 50000):
    all_files = glob.glob(os.path.join(log_dir, "**", "*.csv"), recursive=True)
    
    if not all_files:
        print("No log files found yet.")
        return False, {}
        
    stats = {'real': {'gens': [], 'epc': [], 'lz': [], 'files': []}, 
             'sham': {'gens': [], 'epc': [], 'lz': [], 'files': []}}
             
    complete_count = 0
    total_count = 20 # 10 seeds * 2 modes
    
    current_time = time.time()
    stalled_files = []
    
    for f in all_files:
        mode = 'real' if 'real' in f else 'sham'
        try:
            # Check modified time for stalls (> 5 mins)
            mtime = os.path.getmtime(f)
            if current_time - mtime > 300: # 5 minutes
                stalled_files.append(f)
                
            df = pd.read_csv(f)
            if not df.empty:
                gen = df['gen'].max()
                stats[mode]['gens'].append(gen)
                stats[mode]['files'].append(f)
                
                if gen >= target_gens:
                    complete_count += 1
                
                # Get latest values
                latest = df.iloc[-1]
                if 'avg_fitness' in latest:
                    stats[mode]['epc'].append(latest['avg_fitness'])
                if 'avg_lz' in latest:
                    stats[mode]['lz'].append(latest['avg_lz'])
        except Exception as e:
            pass # File might be written to currently
            
    # Print formatted output
    print(f"\n--- Progress Report ---")
    
    for mode in ['real', 'sham']:
        if not stats[mode]['gens']: continue
        
        avg_gen = sum(stats[mode]['gens']) / len(stats[mode]['gens'])
        pct = (avg_gen / target_gens) * 100
        
        avg_epc = sum(stats[mode]['epc']) / len(stats[mode]['epc']) if stats[mode]['epc'] else 0.0
        avg_lz = sum(stats[mode]['lz']) / len(stats[mode]['lz']) if stats[mode]['lz'] else 0.0
        
        print(f"[{mode.upper()}] {len(stats[mode]['files'])} active | Avg Gen: {avg_gen:.0f} ({pct:.1f}%) | EPC: {avg_epc:.4f} | LZ: {avg_lz:.4f}")
        
    if stalled_files:
        print(f"\n[!] WARNING: {len(stalled_files)} runs appear stalled (no updates in >5 mins).")
        for sf in stalled_files:
            print(f"  - {sf}")
            
    print(f"\nCompletion: {complete_count}/{total_count} files reached target.")
    return complete_count == total_count, stats

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--log_dir", required=True)
    parser.add_argument("--target", type=int, default=50000)
    args = parser.parse_args()
    
    check_progress(args.log_dir, args.target)
