"""
merge_and_plot.py
Merges Control and Constrained CSV data and updates constrained_ceiling.csv and constrained_ceiling_summary.png
"""

import os
import pandas as pd
import matplotlib.pyplot as plt

def merge_csvs():
    control_csv = os.path.abspath('v6/results/constrained_ceiling.csv')
    constrained_csv = os.path.abspath('v6/results/constrained_only.csv')
    output_csv = os.path.abspath('v6/results/constrained_ceiling.csv')
    
    df_control = pd.read_csv(control_csv)
    df_control = df_control[df_control['Condition'] == 'Control']
    
    if os.path.exists(constrained_csv):
        df_constrained = pd.read_csv(constrained_csv)
        df_constrained = df_constrained[df_constrained['Condition'] == 'Constrained']
        df_merged = pd.concat([df_control, df_constrained], ignore_index=True)
    else:
        df_merged = df_control
        
    df_merged.to_csv(output_csv, index=False)
    # Also save to genesis_engine_v6/results/
    v6_csv = os.path.abspath('genesis_engine_v6/results/constrained_ceiling.csv')
    os.makedirs(os.path.dirname(v6_csv), exist_ok=True)
    df_merged.to_csv(v6_csv, index=False)
    return df_merged

def generate_plot(df: pd.DataFrame, output_path: str):
    df['Generation'] = pd.to_numeric(df['Generation'])
    df['AvgNodes'] = pd.to_numeric(df['AvgNodes'])
    df['ActionEntropy'] = pd.to_numeric(df['ActionEntropy'])
    df['GAC'] = pd.to_numeric(df['GAC'])
    df['SpeciesCount'] = pd.to_numeric(df['SpeciesCount'])
    
    control_df = df[df['Condition'] == 'Control'].sort_values('Generation')
    constrained_df = df[df['Condition'] == 'Constrained'].sort_values('Generation')
    
    plt.style.use('dark_background')
    fig, axes = plt.subplots(2, 2, figsize=(14, 10), sharex=True)
    fig.suptitle("Genesis V6: Constrained Ceiling Ablation Study", fontsize=16, fontweight='bold', y=0.95)
    
    c_control = '#1f77b4'      # Vibrant blue
    c_constrained = '#ff7f0e'  # Orange / Amber
    
    # 1. Average Nodes
    ax1 = axes[0, 0]
    ax1.plot(control_df['Generation'], control_df['AvgNodes'], label='Control (Unconstrained)', color=c_control, linewidth=2)
    if not constrained_df.empty:
        ax1.plot(constrained_df['Generation'], constrained_df['AvgNodes'], label='Constrained (Max 52 Nodes)', color=c_constrained, linewidth=2, linestyle='--')
    ax1.axhline(y=52, color='red', linestyle=':', label='Ceiling (52 Nodes)')
    ax1.set_ylabel('Average Nodes', fontsize=12, fontweight='bold')
    ax1.set_title('Structural Growth (Nodes)', fontsize=13)
    ax1.grid(True, alpha=0.3)
    ax1.legend(loc='upper left')
    
    # 2. Action Entropy
    ax2 = axes[0, 1]
    ax2.plot(control_df['Generation'], control_df['ActionEntropy'], label='Control', color=c_control, linewidth=2)
    if not constrained_df.empty:
        ax2.plot(constrained_df['Generation'], constrained_df['ActionEntropy'], label='Constrained', color=c_constrained, linewidth=2, linestyle='--')
    ax2.set_ylabel('Action Entropy', fontsize=12, fontweight='bold')
    ax2.set_title('Behavioral Complexity (Action Entropy)', fontsize=13)
    ax2.grid(True, alpha=0.3)
    ax2.legend(loc='upper right')
    
    # 3. Genome Accumulation Capacity (GAC)
    ax3 = axes[1, 0]
    ax3.plot(control_df['Generation'], control_df['GAC'], label='Control', color=c_control, linewidth=2)
    if not constrained_df.empty:
        ax3.plot(constrained_df['Generation'], constrained_df['GAC'], label='Constrained', color=c_constrained, linewidth=2, linestyle='--')
    ax3.set_xlabel('Generations', fontsize=12, fontweight='bold')
    ax3.set_ylabel('GAC', fontsize=12, fontweight='bold')
    ax3.set_title('Genome Accumulation Capacity (GAC)', fontsize=13)
    ax3.grid(True, alpha=0.3)
    ax3.legend(loc='upper left')
    
    # 4. Species Count
    ax4 = axes[1, 1]
    ax4.plot(control_df['Generation'], control_df['SpeciesCount'], label='Control', color=c_control, linewidth=2)
    if not constrained_df.empty:
        ax4.plot(constrained_df['Generation'], constrained_df['SpeciesCount'], label='Constrained', color=c_constrained, linewidth=2, linestyle='--')
    ax4.set_xlabel('Generations', fontsize=12, fontweight='bold')
    ax4.set_ylabel('Species Count', fontsize=12, fontweight='bold')
    ax4.set_title('Speciation Dynamics', fontsize=13)
    ax4.grid(True, alpha=0.3)
    ax4.legend(loc='upper left')
    
    plt.tight_layout(rect=[0, 0, 1, 0.93])
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    plt.savefig(output_path, dpi=300)
    plt.close()
    print(f"[SUCCESS] Merged plot saved to {output_path}")

if __name__ == "__main__":
    merged_df = merge_csvs()
    out_file = os.path.abspath('v6/results/constrained_ceiling_summary.png')
    generate_plot(merged_df, out_file)
