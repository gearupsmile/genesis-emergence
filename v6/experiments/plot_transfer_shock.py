import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os

csv_path = 'v6/results/transfer_shock.csv'
df = pd.read_csv(csv_path)

plt.style.use('dark_background')
fig, axes = plt.subplots(2, 2, figsize=(14, 10))

colors = {
    'Condition A (V5 467 nodes)': '#ff4d4d',       # Red
    'Condition B (V6 Constrained 52 nodes)': '#00e676', # Vibrant green
    'Condition C (V4 123 nodes)': '#ffb74d',       # Orange
    'Condition D (Naive 12 nodes)': '#4fc3f7'        # Cyan
}

labels = {
    'Condition A (V5 467 nodes)': 'V5 Control (467 nodes)',
    'Condition B (V6 Constrained 52 nodes)': 'V6 Constrained (52 nodes, 815 edges)',
    'Condition C (V4 123 nodes)': 'V4 Baseline (123 nodes)',
    'Condition D (Naive 12 nodes)': 'Naive Baseline (12 nodes)'
}

shocks = df['Environment'].unique()

# Plot 1: ANNEX Emergence Across Shocks (End of Trial Gen 5000)
ax1 = axes[0, 0]
final_df = df[df['Generation'] == 5000]

x = np.arange(len(shocks))
width = 0.2

for i, cond in enumerate(colors.keys()):
    cond_data = final_df[final_df['Condition'] == cond]
    annex_vals = [cond_data[cond_data['Environment'] == s]['ANNEX'].values[0] if len(cond_data[cond_data['Environment'] == s]) > 0 else 0 for s in shocks]
    ax1.bar(x + i*width, annex_vals, width, label=labels[cond], color=colors[cond], alpha=0.9, edgecolor='white', linewidth=0.5)

ax1.set_xticks(x + width * 1.5)
ax1.set_xticklabels(shocks, fontsize=11, fontweight='bold')
ax1.set_title('Post-Shock Structural Complexity (ANNEX at Gen 5000)', fontsize=12, pad=10)
ax1.set_ylabel('ANNEX (Edges Added / Node Limit)', fontsize=10)
ax1.grid(True, linestyle='--', alpha=0.3)
ax1.legend(fontsize=9, loc='upper left')

# Plot 2: Average Edges Rewired Across Time in Shock A (Gradient Shift)
ax2 = axes[0, 1]
shock_a_df = df[df['Environment'] == 'Shock A']
for cond, color in colors.items():
    c_df = shock_a_df[shock_a_df['Condition'] == cond]
    ax2.plot(c_df['Generation'], c_df['AvgEdges'], label=labels[cond], color=color, linewidth=2.5)

ax2.set_title('Shock A: Chemical Gradient Shift Rewiring Trajectory', fontsize=12, pad=10)
ax2.set_xlabel('Generation', fontsize=10)
ax2.set_ylabel('Average Edge Count', fontsize=10)
ax2.grid(True, linestyle='--', alpha=0.3)

# Plot 3: Average Edges Rewired Across Time in Shock B (Inverted Physics)
ax3 = axes[1, 0]
shock_b_df = df[df['Environment'] == 'Shock B']
for cond, color in colors.items():
    c_df = shock_b_df[shock_b_df['Condition'] == cond]
    ax3.plot(c_df['Generation'], c_df['AvgEdges'], label=labels[cond], color=color, linewidth=2.5)

ax3.set_title('Shock B: Inverted Physics (Viscosity Shock) Trajectory', fontsize=12, pad=10)
ax3.set_xlabel('Generation', fontsize=10)
ax3.set_ylabel('Average Edge Count', fontsize=10)
ax3.grid(True, linestyle='--', alpha=0.3)

# Plot 4: Action Entropy Across Conditions in Shock A vs B vs C
ax4 = axes[1, 1]
shock_c_df = df[df['Environment'] == 'Shock C']
for cond, color in colors.items():
    c_df = shock_c_df[shock_c_df['Condition'] == cond]
    ax4.plot(c_df['Generation'], c_df['AvgEdges'], label=labels[cond], color=color, linewidth=2.5)

ax4.set_title('Shock C: High Noise / Dissipation Trajectory', fontsize=12, pad=10)
ax4.set_xlabel('Generation', fontsize=10)
ax4.set_ylabel('Average Edge Count', fontsize=10)
ax4.grid(True, linestyle='--', alpha=0.3)

plt.tight_layout()
out_fig = 'C:/Users/Lenovo/.gemini/antigravity-ide/brain/9313252f-4461-4c35-83f0-2e527ef2f941/transfer_shock_summary.png'
plt.savefig(out_fig, dpi=300, bbox_inches='tight')
print(f"Saved figure to {out_fig}")
