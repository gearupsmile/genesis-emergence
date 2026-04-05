
import json
import numpy as np
import pandas as pd
from pathlib import Path
import sys

def calculate_exploration_metrics(gac_series):
    """
    Calculate variance, novelty events, and exploration score.
    """
    if len(gac_series) < 10:
        return 0, 0, 0
    
    # Variance
    gac_var = np.var(gac_series)
    
    # Novelty Events (jumps > 5)
    events = 0
    for i in range(1, len(gac_series)):
        if abs(gac_series[i] - gac_series[i-1]) > 5:
            events += 1
            
    # Score
    score = gac_var * 0.7 + events * 0.3
    return gac_var, events, score

def main():
    root = Path(__file__).parent.parent.parent
    results_dir = root / 'results' / 'baselines'
    
    # Import process_logs
    sys.path.insert(0, str(root / 'analysis' / 'scripts'))
    try:
        from process_logs import load_baseline_data, classify_failure_modes
    except ImportError:
        print("Could not import process_logs")
        sys.exit(1)

    baselines = {
        'Novelty Search': 'novelty_search',
        'Random Search': 'random_search',
        'Fixed Constraints': 'fixed_constraints',
        'MAP-Elites': 'map_elites' 
    }
    
    # Load all data first
    all_runs_dfs = {}
    
    for name, key in baselines.items():
        df = load_baseline_data(key, results_dir)
        if not df.empty:
            for seed in df['seed'].unique():
                run_id = f"{key}_seed_{seed}"
                all_runs_dfs[run_id] = df[df['seed'] == seed].copy()
    
    # Classify failures
    failures = classify_failure_modes(all_runs_dfs)
    run_to_mode = {}
    for mode, ids in failures.items():
        for rid in ids:
            run_to_mode[rid] = mode

    # Header
    print(r"% Combined Table with GAC, EPC, NND")
    print(r"\begin{table}[h]")
    print(r"\centering")
    print(r"\resizebox{\textwidth}{!}{")
    print(r"\begin{tabular}{lccccccc}")
    print(r"\toprule")
    print(r"\textbf{Method} & \textbf{Final GAC} & \textbf{Final EPC} & \textbf{Final NND} & \textbf{Pop. Var} & \textbf{Nov. Events} & \textbf{Exp. Score} & \textbf{Mode} \\")
    print(r" & (mean $\pm$ SD) & (mean $\pm$ SD) & (mean $\pm$ SD) & & & & \\")
    print(r"\midrule")
    
    for name, key in baselines.items():
        # Get all runs for this baseline
        run_ids = [rid for rid in all_runs_dfs.keys() if rid.startswith(key + "_seed")]
        
        final_gacs = []
        final_epcs = []
        final_nnds = []
        variances = []
        events_list = []
        scores = []
        modes = []
        
        for rid in run_ids:
            df = all_runs_dfs[rid].sort_values('generation')
            if df.empty: continue
            
            # Get final values (average of last 5 gens to be robust?) or just last
            final_gac = df['gac'].iloc[-1]
            final_epc = df['epc'].iloc[-1]
            final_nnd = df['nnd'].iloc[-1] if 'nnd' in df.columns else 0.0
            
            # Handle Nans
            if pd.isna(final_epc): final_epc = 0.0
            if pd.isna(final_nnd): final_nnd = 0.0
            
            final_gacs.append(final_gac)
            final_epcs.append(final_epc)
            final_nnds.append(final_nnd)
            
            # Exploration metrics (on GAC series)
            gac_series = df['gac'].values
            var, evt, scr = calculate_exploration_metrics(gac_series)
            variances.append(var)
            events_list.append(evt)
            scores.append(scr)
            
            modes.append(run_to_mode.get(rid, 'Unknown'))
            
        if final_gacs:
            # Aggregate
            gac_stats = f"{np.mean(final_gacs):.1f} $\\pm$ {np.std(final_gacs):.1f}"
            epc_stats = f"{np.mean(final_epcs):.1f} $\\pm$ {np.std(final_epcs):.1f}"
            nnd_stats = f"{np.mean(final_nnds):.2f} $\\pm$ {np.std(final_nnds):.2f}"
            
            m_var = np.mean(variances)
            m_evt = np.mean(events_list)
            m_scr = np.mean(scores)
            
            # Mode
            from collections import Counter
            dom_mode = Counter(modes).most_common(1)[0][0]
            dom_mode = dom_mode.replace('_', ' ').title().replace('Failure', '')
            if dom_mode.strip() == 'Success': dom_mode = 'Stable'
            
            print(f"{name} & {gac_stats} & {epc_stats} & {nnd_stats} & {m_var:.2f} & {int(m_evt)} & {m_scr:.2f} & {dom_mode} \\\\")
        else:
            print(f"{name} & N/A & N/A & N/A & N/A & N/A & N/A & N/A \\\\")
            
    print(r"\bottomrule")
    print(r"\end{tabular}")
    print(r"}")
    print(r"\caption{Comparison of evolutionary dynamics across baseline methods.}")
    print(r"\label{tab:baseline_comparison}")
    print(r"\end{table}")

if __name__ == '__main__':
    main()
