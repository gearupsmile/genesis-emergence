import matplotlib.pyplot as plt
import matplotlib as mpl
import os

# Set font
mpl.rcParams['font.family'] = 'Arial' # or 'Times New Roman'
mpl.rcParams['font.size'] = 10
mpl.rcParams['axes.titlesize'] = 12
mpl.rcParams['axes.labelsize'] = 10

# Data
generations = [0, 1000, 2000, 3000, 4000, 5000, 6000, 7000, 8000, 9000, 10000]
nodes = [12, 25, 58, 104, 167, 230, 272, 316, 362, 407, 467]
lz = [0.55, 0.56, 0.57, 0.56, 0.58, 0.57, 0.58, 0.56, 0.57, 0.56, 0.56]

# Create figure and axis (6x4 inches)
fig, ax1 = plt.subplots(figsize=(6, 4))

# Left Y-axis (Nodes)
color1 = 'tab:blue'
ax1.set_xlabel('Generations')
ax1.set_ylabel('Neural nodes', color=color1)
ax1.plot(generations, nodes, color=color1, linestyle='-', marker='o', label='Neural nodes')
ax1.tick_params(axis='y', labelcolor=color1)
ax1.set_xticks([0, 2000, 4000, 6000, 8000, 10000])

# Right Y-axis (LZ complexity)
ax2 = ax1.twinx()
color2 = 'tab:red'
ax2.set_ylabel('LZ complexity', color=color2)
ax2.plot(generations, lz, color=color2, linestyle='--', marker='s', label='LZ complexity')
ax2.tick_params(axis='y', labelcolor=color2)
# Set appropriate limits for LZ to make the flat line visible but not cramped
ax2.set_ylim(0.45, 0.65)

# Shade region from gen 4000 to 10000
ax1.axvspan(4000, 10000, color='lightgray', alpha=0.3)

# Annotation for structure/function decoupling
ax1.annotate('structure/function\ndecoupling', 
             xy=(5000, 200), xytext=(7000, 300),
             arrowprops=dict(facecolor='black', arrowstyle='->', shrinkA=0, shrinkB=0),
             ha='center', va='center')

# Caption
caption = "Fig. 1: Neural nodes increase 12→467 (p=1.8e-4) while behavioral LZ stays flat – structure/function decoupling."
fig.text(0.5, 0.02, caption, ha='center', fontsize=10, wrap=True)

# Adjust layout to make room for caption
plt.subplots_adjust(bottom=0.2)

# Save figure to the same directory as the script
output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ccs2026_figure.png')
fig.savefig(output_path, dpi=300, bbox_inches='tight')
print(f"Figure successfully saved to {output_path}")

# Display plot if running interactively
plt.show()
