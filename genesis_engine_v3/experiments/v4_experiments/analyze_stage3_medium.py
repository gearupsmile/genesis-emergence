import os
import glob
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats

def analyze():
    log_dir = "logs/stage3_medium"
    files = glob.glob(f"{log_dir}/stage3_medium_*.csv")
    
    if len(files) != 8:
        print(f"Warning: Expected 8 log files, found {len(files)}.")
    
    data = []
    for f in files:
        filename = os.path.basename(f)
        parts = filename.replace('.csv', '').split('_')
        mode = parts[2]
        seed = int(parts[3].replace('seed', ''))
        
        try:
            df = pd.read_csv(f)
            df['Mode'] = mode
            df['Seed'] = seed
            data.append(df)
        except pd.errors.EmptyDataError:
            print(f"Skipping {filename} - empty")
            
    if not data:
        print("No valid data found.")
        return
        
    all_data = pd.concat(data, ignore_index=True)
    
    # Generate comparative plots
    sns.set(style="whitegrid")
    fig, axs = plt.subplots(3, 2, figsize=(15, 12))
    
    metrics = ['EPC', 'LZ', 'AvgNodes', 'AvgConns', 'NumSpecies', 'S_mean']
    titles = ['EPC (Energy Proxy)', 'LZ Complexity', 'Avg Nodes', 'Avg Connections', 'Number of Species', 'Mean Secretion (S_mean)']
    
    for i, metric in enumerate(metrics):
        ax = axs[i//2, i%2]
        sns.lineplot(data=all_data, x='Generation', y=metric, hue='Mode', errorbar=('ci', 95), ax=ax)
        ax.set_title(titles[i])
        
    plt.tight_layout()
    plot_path = os.path.join(log_dir, "stage3_medium_analysis.png")
    plt.savefig(plot_path)
    print(f"Saved plots to {plot_path}")
    
    # Compute Terminal T-tests (p-values) at final generation for each seed
    print("\n--- Terminal T-Tests (Final Iteration per Seed) ---")
    latest_idxs = all_data.groupby(['Mode', 'Seed'])['Generation'].idxmax()
    terminal_data = all_data.loc[latest_idxs]
    
    with open(os.path.join(log_dir, "analysis_results.txt"), "w") as f:
        f.write("--- Terminal T-Tests (Final Iteration) ---\n")
        for metric in metrics:
            real_vals = terminal_data[terminal_data['Mode'] == 'real'][metric].dropna()
            sham_vals = terminal_data[terminal_data['Mode'] == 'sham'][metric].dropna()
            
            if len(real_vals) > 1 and len(sham_vals) > 1:
                t_stat, p_val = stats.ttest_ind(real_vals, sham_vals, equal_var=False)
                mean_real = real_vals.mean()
                mean_sham = sham_vals.mean()
                
                sig = "*" if p_val < 0.05 else ""
                res = f"{metric:15s} | Real Mean: {mean_real:8.4f} | Sham Mean: {mean_sham:8.4f} | p-value: {p_val:.4f} {sig}"
            else:
                res = f"{metric:15s} | Not enough data for t-test"
                
            print(res)
            f.write(res + "\n")

if __name__ == '__main__':
    analyze()
