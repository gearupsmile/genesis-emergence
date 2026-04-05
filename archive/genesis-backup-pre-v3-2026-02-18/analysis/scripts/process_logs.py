"""
Data Processing Pipeline for Genesis Emergence Paper
Parses logs, aligns runs, and computes statistics for figures.
"""

import json
import numpy as np
import pandas as pd
from pathlib import Path
import sys

def load_baseline_data(baseline_name, results_dir='results/baselines'):
    """
    Load timeseries data for all seeds of a given baseline.
    
    Args:
        baseline_name: 'novelty_search', 'map_elites', 'random_search', 'fixed_constraints'
        results_dir: Path to results directory
        
    Returns:
        DataFrame with columns [generation, seed, gac, epc, nnd, baseline]
    """
    results_path = Path(results_dir)
    pattern = f"{baseline_name}_seed_*_timeseries.json"
    files = list(results_path.glob(pattern))
    
    if not files:
        print(f"[WARN] No files found for {baseline_name}")
        return pd.DataFrame()
        
    all_data = []
    
    for file_path in files:
        # Extract seed from filename
        try:
            seed = int(file_path.name.split('_seed_')[1].split('_')[0])
        except:
            seed = 0
            
        with open(file_path, 'r') as f:
            data = json.load(f)
            
        # Parse based on structure
        # All my new scripts save { 'gac_history': [], 'epc_history': [], ... }
        # Or simple list of dicts for MapElites/Random
        
        histories = []
        
        if 'gac_history' in data: # Novelty/Fixed/Genesis style
            # Assume lists are aligned by generation?
            # They might have different lengths if logged at diff intervals?
            # My scripts use same PNCT logger with synced intervals.
            
            gac_recs = data['gac_history']
            epc_recs = data.get('epc_history', [])
            nnd_recs = data.get('nnd_history', [])
            
            # Convert to dict lookup by generation
            gac_dict = {r['generation']: r for r in gac_recs}
            epc_dict = {r['generation']: r for r in epc_recs}
            nnd_dict = {r['generation']: r for r in nnd_recs}
            
            # Union of generations
            gens = sorted(gac_dict.keys())
            
            for gen in gens:
                rec = {
                    'generation': gen,
                    'seed': seed,
                    'baseline': baseline_name,
                    'gac': gac_dict[gen]['genome_length']['mean'],
                    'epc': epc_dict.get(gen, {}).get('lz_complexity', {}).get('mean', np.nan),
                    'nnd': nnd_dict.get(gen, {}).get('mean_nnd', np.nan)
                }
                histories.append(rec)
                
        elif isinstance(data, list): # MapElites/Random style (list of dicts)
            for r in data:
                rec = {
                    'generation': r['generation'],
                    'seed': seed,
                    'baseline': baseline_name,
                    'gac': r.get('mean_gac', np.nan),
                    'epc': r.get('mean_epc', np.nan),
                    'nnd': np.nan # These don't track NND usually
                }
                histories.append(rec)
        
        all_data.extend(histories)
        
    return pd.DataFrame(all_data)

def align_and_aggregate(df, metric, baseline_name):
    """
    Calculate Median, 25th, 75th percentiles for a metric over generations.
    """
    if df.empty:
        return pd.DataFrame()
        
    # Group by generation
    grouped = df.groupby('generation')[metric]
    
    stats = grouped.agg(
        median='median',
        p25=lambda x: np.percentile(x, 25),
        p75=lambda x: np.percentile(x, 75)
    ).reset_index()
    
    stats['baseline'] = baseline_name
    return stats

def calculate_slope(series, window_size=None):
    """
    Calculate the linear regression slope of a series.
    If window_size is provided, calculates slope over the last N points.
    """
    if len(series) < 2:
        return 0.0
        
    y = np.array(series)
    if window_size and window_size < len(y):
        y = y[-window_size:]
        
    x = np.arange(len(y))
    if len(y) < 2:
        return 0.0
        
    # Polyfit degree 1 returns [slope, intercept]
    slope, _ = np.polyfit(x, y, 1)
    return slope

def classify_failure_modes(all_runs_dict):
    """
    Classify runs into failure modes based on quantitative criteria.
    
    Args:
        all_runs_dict: Dict mapping run_id (or seed) -> DataFrame of history
        
    Returns:
        Dict mapping category name -> list of run_ids
    """
    categories = {
        'success': [],
        'metabolic_failure': [],
        'dominance_failure': [],
        'neutral_drift': []
    }
    
    print(f"Classifying {len(all_runs_dict)} runs...")
    
    for run_id, df in all_runs_dict.items():
        if df.empty or len(df) < 100:
            print(f"Skipping run {run_id} (insufficient data)")
            continue
            
        # Sort by generation just in case
        df = df.sort_values('generation')
        
        # Extract metrics
        gac = df['gac'].values
        epc = df['epc'].values
        nnd = df['nnd'].fillna(0).values
        
        # Criteria 1: Metabolic Failure
        # Last 2000 gens: GAC slope > 0.01 AND EPC slope < 0.001
        # (Growing complexity but flat/low phenotypic expression)
        gac_slope = calculate_slope(gac, window_size=2000)
        epc_slope = calculate_slope(epc, window_size=2000)
        
        is_metabolic = (gac_slope > 0.01) and (epc_slope < 0.001)
        
        # Criteria 2: Dominance Failure (Monopoly)
        # Last 1000 gens: Mean NND < 0.1
        # (Low novelty/diversity)
        if len(nnd) >= 50: # Ensure enough data for NND check
            recent_nnd = nnd[-1000:] if len(nnd) > 1000 else nnd
            mean_nnd = np.mean(recent_nnd)
            is_dominance = mean_nnd < 0.1
        else:
            is_dominance = False
            
        # Criteria 3: Neutral Drift
        # Last 3000 gens: Abs slopes of GAC, EPC, NND all < 0.001
        # (Stagnation / Random Walk)
        nnd_slope = calculate_slope(nnd, window_size=3000)
        
        # Recalculate others with 3000 window for this check
        gac_slope_3k = calculate_slope(gac, window_size=3000)
        epc_slope_3k = calculate_slope(epc, window_size=3000)
        
        is_drift = (abs(gac_slope_3k) < 0.001 and 
                    abs(epc_slope_3k) < 0.001 and 
                    abs(nnd_slope) < 0.001)
                    
        # Assign Category (Priority: Metabolic > Dominance > Drift > Success)
        if is_metabolic:
            categories['metabolic_failure'].append(run_id)
        elif is_dominance:
            categories['dominance_failure'].append(run_id)
        elif is_drift:
            categories['neutral_drift'].append(run_id)
        else:
            # If validated as viable, it's a success
            categories['success'].append(run_id)
            
    return categories

def analyze_failure_modes(runs_path_or_dict):
    """Wrapper to load and classify."""
    # If path passed, load data first (placeholder logic)
    # Assumes runs_path_or_dict is ALREADY a dict of DataFrames usually
    # But for compatibility with main script usage:
    return classify_failure_modes(runs_path_or_dict)

if __name__ == '__main__':
    # Test loading
    root = Path(__file__).parent.parent.parent
    results = root / 'results' / 'baselines'
    
    df_nov = load_baseline_data('novelty_search', results)
    print("Novelty Data:", df_nov.shape)
    if not df_nov.empty:
        print(df_nov.head())
        
    df_fix = load_baseline_data('fixed_constraints', results)
    print("Fixed Data:", df_fix.shape)
