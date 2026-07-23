import os
import sys
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import matplotlib.gridspec as gridspec
import networkx as nx
import csv
import imageio.v2 as iio
from io import BytesIO

# Ensure paths
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if root_dir not in sys.path:
    sys.path.append(root_dir)

from genesis_engine_v3.engine.structurally_evolvable_agent import AgentV4
from v5.src.cppn_environment import V5Substrate
from v5.src.coevolution import CoevolutionOrchestrator
from v5.src.metrics import compute_lz_complexity_ratio

plt.style.use('dark_background')

# Configuration
FPS = 30
DURATION_SEC = 60
TOTAL_FRAMES = FPS * DURATION_SEC
TARGET_GENS = 2000
GENS_PER_FRAME = max(1, int(TARGET_GENS / TOTAL_FRAMES))

SEED = 42
np.random.seed(SEED)
import random
random.seed(SEED)

def get_agent_action_string(agent, substrate, steps=20):
    clone = AgentV4(agent.x, agent.y, agent.genome.copy())
    clone.energy = 1.0
    action_str = ""
    for _ in range(steps):
        action_str += clone.step(substrate)
    return action_str

def get_action_probs(agent, substrate):
    h, w = substrate.U.shape
    x, y = int(agent.x), int(agent.y)
    def grad(field):
        dx = field[y, (x+1)%w] - field[y, (x-1)%w]
        dy = field[(y+1)%h, x] - field[(y-1)%h, x]
        return dx, dy
    inputs = {
        'x': agent.x / max(1, w), 'y': agent.y / max(1, h), 'energy': agent.energy,
        'grad_U_x': grad(substrate.U)[0], 'grad_U_y': grad(substrate.U)[1],
        'grad_V_x': grad(substrate.V)[0], 'grad_V_y': grad(substrate.V)[1],
        'grad_S_x': grad(substrate.S)[0], 'grad_S_y': grad(substrate.S)[1],
    }
    outputs = agent.genome.activate(inputs)
    mx, my, s = outputs.get('move_x', 0), outputs.get('move_y', 0), outputs.get('secrete', 0)
    
    # Softmax mock for viz
    vals = np.array([max(0, abs(mx)+abs(my)), max(0, s), 0.1]) # Move, Secrete, Idle baseline
    probs = np.exp(vals) / np.sum(np.exp(vals))
    
    action = 'I'
    if s > 0.5: action = 'S'
    elif abs(mx) > 0.3 or abs(my) > 0.3: action = 'M'
    return probs, action

class DemoSimulator:
    def __init__(self):
        # V4 Baseline
        width, height = 50, 50
        f_map = np.full((height, width), 0.055, dtype=np.float32)
        k_map = np.full((height, width), 0.062, dtype=np.float32)
        u_map = np.full((height, width), 1.0, dtype=np.float32)
        v_map = np.full((height, width), 0.4, dtype=np.float32)
        self.v4_sub = V5Substrate(width, height, f_map, k_map, u_map, v_map)
        self.v4_pop = [AgentV4(random.randint(0, width-1), random.randint(0, height-1)) for _ in range(20)]
        
        # V5 Coevolution
        self.v5_orch = CoevolutionOrchestrator(num_envs=1, pop_size_per_env=20)
        
        self.gen = 0
        self.v4_traces = []
        self.v5_traces = []
        
    def step_gen(self):
        self.gen += 1
        # Step V4
        for _ in range(20):
            self.v4_sub.step()
            for a in self.v4_pop:
                a.step(self.v4_sub)
                a.energy += self.v4_sub.V[int(a.y)%self.v4_sub.height, int(a.x)%self.v4_sub.width] * 0.5
        self.v4_pop.sort(key=lambda a: a.energy, reverse=True)
        survivors = self.v4_pop[:10]
        for a in survivors:
            a.energy = min(1.0, max(0.0, a.energy + 0.2))
        new_pop = list(survivors)
        while len(new_pop) < 20:
            new_pop.append(random.choice(survivors).reproduce())
        self.v4_pop = new_pop
        
        # Step V5
        self.v5_orch.step()
        if self.gen % 100 == 0:
            self.v5_orch.coevolve()
            
    def get_rep_data(self):
        v4_rep = self.v4_pop[0]
        v5_env = self.v5_orch.environments[0]
        v5_pop = self.v5_orch.agent_populations[v5_env.id]
        v5_pop.sort(key=lambda a: a.energy, reverse=True)
        v5_rep = v5_pop[0] if v5_pop else None
        return v4_rep, self.v4_sub, v5_rep, self.v5_orch.substrates[v5_env.id]

def draw_network(ax, agent):
    ax.clear()
    ax.set_facecolor('black')
    ax.axis('off')
    if not agent: return
    
    nodes = agent.genome.nodes
    conns = agent.genome.connections
    num_nodes = len(nodes)
    
    if num_nodes <= 100:
        # Exact graph
        G = nx.DiGraph()
        for idx in nodes: G.add_node(idx)
        for c in conns.values():
            if c.enabled: G.add_edge(c.from_node, c.to_node)
        pos = nx.spring_layout(G, seed=42)
        nx.draw_networkx_nodes(G, pos, ax=ax, node_size=10, node_color='gray')
        nx.draw_networkx_edges(G, pos, ax=ax, alpha=0.3, edge_color='gray')
    else:
        # Node cloud
        theta = np.linspace(0, 2*np.pi, num_nodes)
        r = np.random.uniform(0.5, 1.0, num_nodes)
        x = r * np.cos(theta)
        y = r * np.sin(theta)
        ax.scatter(x, y, s=4, c='cyan', alpha=0.6, edgecolors='none')
        ax.text(0, 0, f"{num_nodes} nodes", color='white', ha='center', va='center', fontsize=14, fontweight='bold')

def draw_sensory(ax, agent, sub):
    ax.clear()
    ax.axis('off')
    if not agent: return
    
    x, y = int(agent.x), int(agent.y)
    h, w = sub.U.shape
    
    # 3x3 window
    rgb = np.zeros((3, 3, 3))
    for dy in range(-1, 2):
        for dx in range(-1, 2):
            ny, nx = (y+dy)%h, (x+dx)%w
            rgb[dy+1, dx+1, 0] = sub.V[ny, nx] # Red
            rgb[dy+1, dx+1, 1] = sub.S[ny, nx] # Green
            rgb[dy+1, dx+1, 2] = sub.U[ny, nx] # Blue
            
    ax.imshow(np.clip(rgb, 0, 1), interpolation='nearest')
    
def draw_action(ax, probs, action, trace):
    ax.clear()
    ax.set_facecolor('black')
    ax.axis('off')
    
    # Bar chart
    ax.bar(['Move', 'Secrete', 'Idle'], probs, color=['green', 'blue', 'gray'])
    ax.set_ylim(0, 1)
    
    # Trace
    trace_str = " ".join([c for c in trace[-20:]])
    ax.text(0.5, -0.2, f"TRACE: {trace_str}", color='white', ha='center', transform=ax.transAxes, fontsize=8)
    ax.text(0.5, 0.8, f"ACTION: {action}", color='white', ha='center', transform=ax.transAxes, fontsize=12, fontweight='bold')

def main():
    print("Initializing Real Simulation Data Generator...")
    sim = DemoSimulator()
    
    os.makedirs('demo_output/frames', exist_ok=True)
    csv_data = []
    
    match_frames = 0
    decoupling_triggered = False
    
    print("Starting render pipeline (1800 frames)...")
    for frame in range(TOTAL_FRAMES):
        # 0-3s Hook
        if frame < 90:
            fig, ax = plt.subplots(figsize=(16, 9), facecolor='black')
            ax.set_facecolor('black')
            ax.axis('off')
            ax.text(0.5, 0.5, "no rules. no goal. watch.", color='white', ha='center', va='center', fontsize=30)
            plt.savefig(f"demo_output/frames/frame_{frame:04d}.png", facecolor='black', dpi=120)
            plt.close()
            continue
            
        # Step logic
        for _ in range(GENS_PER_FRAME):
            sim.step_gen()
            
        v4_rep, v4_sub, v5_rep, v5_sub = sim.get_rep_data()
        
        # Action logic
        v4_probs, v4_act = get_action_probs(v4_rep, v4_sub)
        v5_probs, v5_act = get_action_probs(v5_rep, v5_sub) if v5_rep else ([0.33,0.33,0.33], 'I')
        
        sim.v4_traces.append(v4_act)
        sim.v5_traces.append(v5_act)
        
        # Similarity
        sim_score = 0.0
        if len(sim.v4_traces) > 20:
            matches = sum(1 for a, b in zip(sim.v4_traces[-20:], sim.v5_traces[-20:]) if a == b)
            sim_score = matches / 20.0
            
        # Match condition
        if v4_act == v5_act and sim_score > 0.8:
            match_frames += 1
        else:
            match_frames = 0
            
        nodes_v5 = len(v5_rep.genome.nodes) if v5_rep else 0
        if nodes_v5 > 400 and match_frames >= 5 and sim_score > 0.9:
            decoupling_triggered = True
            
        csv_data.append([sim.gen, nodes_v5, sim_score, match_frames, list(v5_probs)])
        
        # 3-12s Emergence
        if frame < 360:
            fig, ax = plt.subplots(figsize=(16, 9), facecolor='black')
            ax.set_facecolor('black')
            ax.axis('off')
            ax.imshow(v5_sub.U, cmap='magma', alpha=0.5)
            # Scatter agents
            pops = sim.v5_orch.agent_populations[sim.v5_orch.environments[0].id]
            xs = [a.x for a in pops]
            ys = [a.y for a in pops]
            colors = []
            for a in pops:
                n = len(a.genome.nodes)
                if n < 100: colors.append('blue')
                elif n < 200: colors.append('cyan')
                elif n < 300: colors.append('yellow')
                elif n < 400: colors.append('orange')
                else: colors.append('red')
            ax.scatter(xs, ys, c=colors, s=60, alpha=0.8, edgecolors='none')
            plt.savefig(f"demo_output/frames/frame_{frame:04d}.png", facecolor='black', dpi=120)
            plt.close()
            continue
            
        # Split Screen 12-60s
        fig = plt.figure(figsize=(16, 9), facecolor='black')
        gs = gridspec.GridSpec(3, 2, figure=fig)
        
        # Left side (V4)
        ax_l1 = fig.add_subplot(gs[0, 0])
        ax_l2 = fig.add_subplot(gs[1, 0])
        ax_l3 = fig.add_subplot(gs[2, 0])
        
        # Right side (V5)
        ax_r1 = fig.add_subplot(gs[0, 1])
        ax_r2 = fig.add_subplot(gs[1, 1])
        ax_r3 = fig.add_subplot(gs[2, 1])
        
        draw_sensory(ax_l1, v4_rep, v4_sub)
        draw_sensory(ax_r1, v5_rep, v5_sub)
        
        draw_network(ax_l2, v4_rep)
        draw_network(ax_r2, v5_rep)
        
        draw_action(ax_l3, v4_probs, v4_act, "".join(sim.v4_traces))
        draw_action(ax_r3, v5_probs, v5_act, "".join(sim.v5_traces))
        
        fig.suptitle(f"FIXED PHYSICS (V4)                                CO-EVOLVING PHYSICS (V5)\nGEN: {sim.gen} / 2000", color='white', fontsize=16)
        
        if decoupling_triggered:
            fig.text(0.5, 0.9, "STRUCTURE-FUNCTION DECOUPLING DETECTED", color='white', bbox=dict(facecolor='black', edgecolor='orange', boxstyle='round,pad=0.5'), ha='center', fontsize=20, fontweight='bold')
            fig.text(0.75, 0.45, f"Internal complexity: {nodes_v5} nodes\nBehavior unchanged ({int(sim_score*100)}% similarity)", color='white', ha='center')
        
        plt.tight_layout(rect=[0, 0, 1, 0.95])
        plt.savefig(f"demo_output/frames/frame_{frame:04d}.png", facecolor='black', dpi=120)
        plt.close()
        
        if frame % 30 == 0:
            print(f"Rendered {frame}/{TOTAL_FRAMES} frames (Gen {sim.gen})")
            
    print("Compiling video...")
    writer = iio.get_writer('demo_output/genesis_v5_demo.mp4', fps=FPS)
    for frame in range(TOTAL_FRAMES):
        writer.append_data(iio.imread(f"demo_output/frames/frame_{frame:04d}.png"))
    writer.close()
    
    with open('demo_output/demo_metrics.csv', 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['generation', 'node_count', 'behavioural_similarity', 'action_match_duration', 'action_probabilities'])
        w.writerows(csv_data)
        
    print("Demo video rendering complete! Check 'demo_output/'")

if __name__ == '__main__':
    main()
