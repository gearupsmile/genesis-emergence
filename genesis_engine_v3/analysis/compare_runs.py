"""
Compare Real vs Sham Runs
"""
import sys
import os
import argparse
import pandas as pd
import matplotlib.pyplot as plt

def compare_runs(real_dir: str, sham_dir: str, output_file: str):
    print(f"Comparing logs from:\nReal: {real_dir}\nSham: {sham_dir}")
    
    # Find CSVs
    def get_latest_csv(d):
        files = [f for f in os.listdir(d) if f.endswith('.csv') and f.startswith('metrics_')]
        if not files: return None
        # Sort by modification time? Or just take first matching pattern?
        # Expecting metrics_mode_seed.csv
        return os.path.join(d, files[0])
        
    real_csv = get_latest_csv(real_dir)
    sham_csv = get_latest_csv(sham_dir)
    
    if not real_csv or not sham_csv:
        print(f"FAIL: Could not find CSV files.\nReal: {real_csv}\nSham: {sham_csv}")
        return
        
    df_real = pd.read_csv(real_csv)
    df_sham = pd.read_csv(sham_csv)
    
    print(f"Loaded Real data: {len(df_real)} rows")
    print(f"Loaded Sham data: {len(df_sham)} rows")
    
    # Plotting
    fig, axes = plt.subplots(2, 2, figsize=(15, 10))
    fig.suptitle('Real (Secretion) vs Sham (Control) Comparison', fontsize=16)
    
    # 1. Secretion Mean
    ax = axes[0, 0]
    ax.plot(df_real['gen'], df_real['s_mean'], label='Real', color='blue')
    ax.plot(df_sham['gen'], df_sham['s_mean'], label='Sham', color='red', linestyle='--')
    ax.set_title('Mean Secretion Field Value')
    ax.set_xlabel('Generation')
    ax.set_ylabel('S Value')
    ax.legend()
    ax.grid(True)
    
    # 2. Agent Count
    ax = axes[0, 1]
    ax.plot(df_real['gen'], df_real['agent_count'], label='Real', color='blue')
    ax.plot(df_sham['gen'], df_sham['agent_count'], label='Sham', color='red', linestyle='--')
    ax.set_title('Population Size')
    ax.set_xlabel('Generation')
    ax.set_ylabel('Count')
    ax.legend()
    ax.grid(True)
    
    # 3. Average LZ Complexity
    ax = axes[1, 0]
    ax.plot(df_real['gen'], df_real['avg_lz'], label='Real', color='blue')
    ax.plot(df_sham['gen'], df_sham['avg_lz'], label='Sham', color='red', linestyle='--')
    ax.set_title('Average LZ Complexity')
    ax.set_xlabel('Generation')
    ax.set_ylabel('LZ Score')
    ax.legend()
    ax.grid(True)
    
    # 4. Archive Size
    ax = axes[1, 1]
    ax.plot(df_real['gen'], df_real['archive_size'], label='Real', color='blue')
    ax.plot(df_sham['gen'], df_sham['archive_size'], label='Sham', color='red', linestyle='--')
    ax.set_title('AIS Archive Size')
    ax.set_xlabel('Generation')
    ax.set_ylabel('Entries')
    ax.legend()
    ax.grid(True)
    
    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    plt.savefig(output_file)
    print(f"Comparison plot saved to {output_file}")
    
    # Text Analysis
    print("\n--- Summary Metrics ---")
    print(f"Real Final S_Mean: {df_real['s_mean'].iloc[-1]:.4f}")
    print(f"Sham Final S_Mean: {df_sham['s_mean'].iloc[-1]:.4f}")
    print(f"Real Max LZ: {df_real['avg_lz'].max():.4f}")
    print(f"Sham Max LZ: {df_sham['avg_lz'].max():.4f}")
    
    # Validation Logic
    passed = True
    if df_real['s_mean'].iloc[-1] <= 0.01:
        print("FAIL: Real secretion too low.")
        passed = False
    if df_sham['s_mean'].iloc[-1] > 0.001:
        print("FAIL: Sham secretion non-zero.")
        passed = False
    if df_real['agent_count'].iloc[-1] == 0:
        print("FAIL: Real population died out.")
        passed = False
    
    if passed:
        print("\n[PASS] Comparison criteria met.")
    else:
        print("\n[FAIL] Comparison criteria not met.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--real", required=True, help="Real log dir")
    parser.add_argument("--sham", required=True, help="Sham log dir")
    parser.add_argument("--output", required=True, help="Output image file")
    
    args = parser.parse_args()
    
    compare_runs(args.real, args.sham, args.output)
