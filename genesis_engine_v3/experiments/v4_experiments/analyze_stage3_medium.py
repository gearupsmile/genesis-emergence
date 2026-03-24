import os
import glob
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats

def analyze_medium_runs(log_dir):
    all_files = glob.glob(os.path.join(log_dir, "*.csv"))
    if not all_files:
        print("No CSV files found in", log_dir)
        return
        
    dfs = []
    for f in all_files:
        basename = os.path.basename(f)
        parts = basename.replace('.csv', '').split('_')
        mode = parts[2]
        seed = int(parts[3].replace('seed', ''))
        
        df = pd.read_csv(f)
        df['Mode'] = mode
        df['Seed'] = seed
        dfs.append(df)
        
    data = pd.concat(dfs, ignore_index=True)
    
    metrics = [
        ('EPC', 'EPC (Avg Energy)'),
        ('AvgNodes', 'Average Nodes'),
        ('AvgConns', 'Average Connections'),
        ('NumSpecies', 'Number of Species'),
        ('S_mean', 'Secretion Field Mean'),
        ('LZ', 'Action Trace LZ Complexity')
    ]
    
    os.makedirs('experiments/v4_experiments/plots', exist_ok=True)
    
    sns.set_theme(style="whitegrid")
    
    print("Generating plots...")
    for col, ylabel in metrics:
        if col not in data.columns:
            continue
            
        plt.figure(figsize=(10, 6))
        sns.lineplot(data=data, x='Generation', y=col, hue='Mode', 
                     errorbar=('ci', 95), estimator=np.mean)
        plt.title(f"{ylabel} over Generations")
        plt.ylabel(ylabel)
        
        plt.savefig(f"experiments/v4_experiments/plots/medium_{col.lower()}.png")
        plt.close()
        
    print("\n--- Terminal Statistics (Generation 5000) ---")
    term_data = data[data['Generation'] == 5000]
    
    if term_data.empty:
        max_gen = data['Generation'].max()
        print(f"No data reached 5k. Max Gen is {max_gen}")
        term_data = data[data['Generation'] == max_gen]
        print(f"Running terminal stats on Gen {max_gen} instead:")
        
    for col, ylabel in metrics:
        if col not in term_data.columns:
            continue
            
        real_vals = term_data[term_data['Mode'] == 'real'][col].values
        sham_vals = term_data[term_data['Mode'] == 'sham'][col].values
        
        if len(real_vals) > 0 and len(sham_vals) > 0:
            if np.std(real_vals) == 0 and np.std(sham_vals) == 0 and real_vals[0] == sham_vals[0]:
                p_val = 1.0
            else:
                t_stat, p_val = stats.ttest_ind(real_vals, sham_vals, equal_var=False)
                
            real_mean = np.mean(real_vals)
            sham_mean = np.mean(sham_vals)
            
            sig = "***" if p_val < 0.001 else "**" if p_val < 0.01 else "*" if p_val < 0.05 else "ns"
            
            print(f"{ylabel:30s} | Real: {real_mean:9.4f} | Sham: {sham_mean:9.4f} | p-val: {p_val:7.4f} {sig}")
        else:
            print(f"{ylabel:30s} | Incomplete data for t-test.")

if __name__ == '__main__':
    analyze_medium_runs('logs/stage3_medium')
