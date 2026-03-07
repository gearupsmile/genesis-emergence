"""
Convert experimental CSV data to LaTeX/TikZ coordinates
Generates ready-to-paste LaTeX code for all figures
"""

import pandas as pd
import numpy as np
from pathlib import Path

def csv_to_latex_coords(csv_file, x_col='generation', y_col='gac', subsample=100):
    """Convert CSV data to LaTeX coordinates string"""
    try:
        df = pd.read_csv(csv_file)
        
        # Subsample for cleaner LaTeX (every Nth point)
        if len(df) > subsample:
            indices = np.linspace(0, len(df)-1, subsample, dtype=int)
            df = df.iloc[indices]
        
        # Generate coordinate string
        coords = ' '.join([f"({row[x_col]},{row[y_col]:.2f})" 
                          for _, row in df.iterrows()])
        
        return coords
    except Exception as e:
        print(f"Error processing {csv_file}: {e}")
        return None

def generate_figure_2_latex(results_dir='results/baselines'):
    """Generate LaTeX code for Figure 2 (Phase Transition)"""
    
    print("=" * 60)
    print("FIGURE 2: PHASE TRANSITION PLOT")
    print("=" * 60)
    
    # Try to load full system data
    full_system_file = Path(results_dir).parent / 'full_system' / 'run_seed_42' / 'metrics.csv'
    
    if not full_system_file.exists():
        print(f"\nWarning: {full_system_file} not found")
        print("Using synthetic data. Run experiments first!")
        return
    
    # Generate coordinates for each metric
    print("\n% GAC trajectory:")
    gac_coords = csv_to_latex_coords(full_system_file, y_col='gac')
    if gac_coords:
        print(f"\\addplot[blue, thick, smooth] coordinates {{{gac_coords}}};")
    
    print("\n% EPC trajectory:")
    epc_coords = csv_to_latex_coords(full_system_file, y_col='epc')
    if epc_coords:
        print(f"\\addplot[green!60!black, thick, smooth] coordinates {{{epc_coords}}};")
    
    print("\n% NND trajectory:")
    nnd_coords = csv_to_latex_coords(full_system_file, y_col='nnd')
    if nnd_coords:
        print(f"\\addplot[magenta, thick, smooth] coordinates {{{nnd_coords}}};")

def generate_figure_3_latex(results_dir='results/baselines'):
    """Generate LaTeX code for Figure 3 (Comparison)"""
    
    print("\n" + "=" * 60)
    print("FIGURE 3: BASELINE COMPARISON")
    print("=" * 60)
    
    baselines = {
        'Genesis (Full)': ('full_system_seed_42.csv', 'blue, very thick'),
        'Random Search': ('random_search_seed_42.csv', 'red, dotted, thick'),
        'No CARP': ('fixed_constraints_seed_42.csv', 'magenta, dash dot, thick'),
        'Novelty Search': ('novelty_seed_42.csv', 'green!60!black, dashed, thick')
    }
    
    for label, (filename, style) in baselines.items():
        filepath = Path(results_dir) / filename
        
        if filepath.exists():
            coords = csv_to_latex_coords(filepath, y_col='gac', subsample=50)
            if coords:
                print(f"\n% {label}")
                print(f"\\addplot[{style}, smooth] coordinates {{{coords}}};")
                print(f"\\addlegendentry{{{label}}}")
        else:
            print(f"\nWarning: {filepath} not found - run experiments first!")

def generate_figure_4_latex(results_dir='results/baselines'):
    """Generate LaTeX code for Figure 4 (Failure Timeline)"""
    
    print("\n" + "=" * 60)
    print("FIGURE 4: FAILURE TIMELINE")
    print("=" * 60)
    
    # This requires analyzing multiple runs to calculate cumulative failures
    # For now, provide template
    
    print("\n% Note: This requires analyzing all 12 runs per configuration")
    print("% to calculate cumulative failure percentage at each generation")
    print("\n% Template:")
    print("\\addplot[blue, very thick, smooth] coordinates {")
    print("    % (generation, cumulative_failure_percentage)")
    print("    (0,0) (10000,10) (20000,20) (30000,30) (40000,40) (50000,42)")
    print("};")
    print("\\addlegendentry{Full System}")

def average_multiple_seeds(results_dir='results/baselines', config='full_system', seeds=[42, 123, 456]):
    """Average data across multiple seeds"""
    
    print("\n" + "=" * 60)
    print(f"AVERAGING {config} ACROSS SEEDS {seeds}")
    print("=" * 60)
    
    dfs = []
    for seed in seeds:
        filepath = Path(results_dir) / f'{config}_seed_{seed}.csv'
        if filepath.exists():
            df = pd.read_csv(filepath)
            dfs.append(df)
        else:
            print(f"Warning: {filepath} not found")
    
    if not dfs:
        print("No data files found!")
        return
    
    # Average across seeds
    avg_df = pd.concat(dfs).groupby('generation').mean().reset_index()
    
    # Generate coordinates
    gac_coords = csv_to_latex_coords_from_df(avg_df, y_col='gac')
    
    print(f"\n% Averaged GAC (n={len(dfs)} seeds):")
    print(f"\\addplot[blue, thick, smooth] coordinates {{{gac_coords}}};")

def csv_to_latex_coords_from_df(df, x_col='generation', y_col='gac', subsample=100):
    """Convert DataFrame to LaTeX coordinates"""
    if len(df) > subsample:
        indices = np.linspace(0, len(df)-1, subsample, dtype=int)
        df = df.iloc[indices]
    
    coords = ' '.join([f"({row[x_col]},{row[y_col]:.2f})" 
                      for _, row in df.iterrows()])
    return coords

def main():
    """Generate all LaTeX figure code"""
    
    print("=" * 60)
    print("LATEX FIGURE CODE GENERATOR")
    print("=" * 60)
    print("\nThis script converts your experimental CSV data")
    print("into ready-to-paste LaTeX/TikZ coordinates.\n")
    
    results_dir = 'results/baselines'
    
    # Check if results exist
    if not Path(results_dir).exists():
        print(f"\nError: {results_dir} directory not found!")
        print("\nPlease run experiments first:")
        print("  python run_all_baselines.py")
        print("\nUsing synthetic data for demonstration...\n")
    
    # Generate code for each figure
    generate_figure_2_latex(results_dir)
    generate_figure_3_latex(results_dir)
    generate_figure_4_latex(results_dir)
    
    print("\n" + "=" * 60)
    print("DONE!")
    print("=" * 60)
    print("\nCopy the generated \\addplot commands above")
    print("and paste them into your LaTeX figure code.")
    print("\nSee LATEX_FIGURES.md for complete figure templates.")

if __name__ == '__main__':
    main()
