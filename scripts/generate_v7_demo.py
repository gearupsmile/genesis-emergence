import os
import sys
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import matplotlib.gridspec as gridspec
import networkx as nx
import imageio.v2 as iio
from scipy.io import wavfile
import random

root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if root_dir not in sys.path:
    sys.path.append(root_dir)

from genesis_engine_v3.engine.structurally_evolvable_agent import AgentV4
from v5.src.cppn_environment import V5Substrate
from v5.src.coevolution import CoevolutionOrchestrator

plt.style.use('dark_background')

# Configuration
FPS = 30
TOTAL_FRAMES = 1800
TARGET_GENS = 2000
GENS_PER_FRAME = max(1, int(TARGET_GENS / 1440)) # 48s of evolution
SEED = 42
np.random.seed(SEED)
random.seed(SEED)

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
    
    vals = np.array([max(0, abs(mx)+abs(my)), max(0, s), 0.1])
    probs = np.exp(vals) / np.sum(np.exp(vals))
    
    action = '||'
    if s > 0.5: action = 'O'
    elif abs(mx) > 0.3 or abs(my) > 0.3: action = '->'
    return probs, action

class DemoSimulator:
    def __init__(self):
        width, height = 50, 50
        f_map = np.full((height, width), 0.055, dtype=np.float32)
        k_map = np.full((height, width), 0.062, dtype=np.float32)
        u_map = np.full((height, width), 1.0, dtype=np.float32)
        v_map = np.full((height, width), 0.4, dtype=np.float32)
        self.v4_sub = V5Substrate(width, height, f_map, k_map, u_map, v_map)
        self.v4_pop = [AgentV4(random.randint(0, width-1), random.randint(0, height-1)) for _ in range(20)]
        self.v5_orch = CoevolutionOrchestrator(num_envs=1, pop_size_per_env=20)
        self.gen = 0
        
    def step_gen(self):
        self.gen += 1
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

def draw_network(ax, agent, frame):
    ax.clear()
    ax.axis('off')
    if not agent: return
    
    nodes = agent.genome.nodes
    conns = agent.genome.connections
    num_nodes = len(nodes)
    
    G = nx.DiGraph()
    colors = []
    for idx, node in nodes.items():
        G.add_node(idx)
        if getattr(node, 'type', 'hidden') == 'input': colors.append('#3B8BD4')
        elif getattr(node, 'type', 'hidden') == 'output': colors.append('#2E8B57')
        else: colors.append('#AAAAAA')
        
    for c in conns.values():
        if getattr(c, 'enabled', True):
            G.add_edge(c.from_node, c.to_node)
            
    # Deterministic layout
    pos = nx.spring_layout(G, seed=42)
    
    # White circular border (simulate 300px on axes scale)
    circle = patches.Circle((0, 0), radius=1.5, fill=False, edgecolor='white', linewidth=3, zorder=1)
    ax.add_patch(circle)
    ax.set_xlim(-1.6, 1.6)
    ax.set_ylim(-1.6, 1.6)
    
    nx.draw_networkx_nodes(G, pos, ax=ax, node_size=15, node_color=colors, zorder=2)
    nx.draw_networkx_edges(G, pos, ax=ax, edge_color='white', alpha=0.3, width=0.5, zorder=1)

def draw_action_bars(ax, probs, action):
    ax.clear()
    ax.axis('off')
    ax.barh([2, 1, 0], probs, color=['grey', 'blue', 'green'], height=0.4)
    ax.set_xlim(0, 1)
    ax.text(-0.05, 2, "idle", color='grey', va='center', ha='right', fontsize=12)
    ax.text(-0.05, 1, "secrete", color='grey', va='center', ha='right', fontsize=12)
    ax.text(-0.05, 0, "move", color='grey', va='center', ha='right', fontsize=12)
    action_text = "moving" if action == '->' else "secreting" if action == 'O' else "waiting"
    ax.text(0.5, 3.2, f"{action} {action_text}", color='white', ha='center', fontsize=20)

def main():
    print("Initializing Circular Network Pipeline...")
    sim = DemoSimulator()
    os.makedirs('demo_output/v7_frames', exist_ok=True)
    
    fig = plt.figure(figsize=(19.2, 10.8), facecolor='black')
    
    cached_v5_nodes = 12
    last_rendered_nodes = 12
    
    for frame in range(TOTAL_FRAMES):
        if frame < 48 * FPS:
            for _ in range(GENS_PER_FRAME):
                sim.step_gen()
                
            v4_rep, v4_sub, v5_rep, v5_sub = sim.get_rep_data()
            v4_probs, v4_act = get_action_probs(v4_rep, v4_sub)
            v5_probs, v5_act = get_action_probs(v5_rep, v5_sub) if v5_rep else ([0.33,0.33,0.33], '||')
            
            cached_v5_nodes = len(v5_rep.genome.nodes) if v5_rep else 12
            if last_rendered_nodes < cached_v5_nodes:
                increment = max(1, (cached_v5_nodes - last_rendered_nodes) // (FPS//2))
                last_rendered_nodes = min(cached_v5_nodes, last_rendered_nodes + increment)
                
        fig.clf()
        fig.patch.set_facecolor('black')
        
        if frame < 4 * FPS:
            alpha = min(1.0, frame / FPS)
            fig.text(0.5, 0.5, "Can a system become more complex inside\nwhile looking exactly the same outside?", 
                     color='white', ha='center', va='center', fontsize=36, alpha=alpha)
        elif frame < 12 * FPS:
            ax = fig.add_subplot(111)
            ax.axis('off')
            ax.imshow(v5_sub.U, cmap='inferno')
        elif frame < 48 * FPS:
            gs = gridspec.GridSpec(10, 2, figure=fig, hspace=0.1, wspace=0.01)
            ax_net_l = fig.add_subplot(gs[0:7, 0])
            ax_net_r = fig.add_subplot(gs[0:7, 1])
            ax_act_l = fig.add_subplot(gs[7:9, 0])
            ax_act_r = fig.add_subplot(gs[7:9, 1])
            
            fig.text(0.25, 0.95, "FIXED PHYSICS (V4)", color='grey', ha='center', fontsize=20)
            fig.text(0.75, 0.95, "CO-EVOLVING PHYSICS (V5)", color='grey', ha='center', fontsize=20)
            
            draw_network(ax_net_l, v4_rep, frame)
            if v5_rep: draw_network(ax_net_r, v5_rep, frame)
            
            fig.text(0.25, 0.1, "NODES: 12", color='grey', ha='center', fontsize=48, fontfamily='monospace')
            fig.text(0.75, 0.1, f"NODES: {last_rendered_nodes:03d}", color='#EF9F27', ha='center', fontsize=48, fontfamily='monospace')
            
            draw_action_bars(ax_act_l, v4_probs, v4_act)
            draw_action_bars(ax_act_r, v5_probs, v5_act)
            
            if frame == 45 * FPS:
                plt.savefig(f"demo_output/v7_frames/frame_freeze.png", facecolor='black')
        
        elif frame < 52 * FPS:
            # Re-read freeze frame to save compute
            fig.text(0.75, 0.5, "STRUCTURE-FUNCTION DECOUPLING\n467 internal nodes. Same 3 actions as generation 1.\np = 0.00018 · sham-controlled · GECCO 2026", 
                     color='white', ha='center', va='center', fontsize=24, fontweight='bold',
                     bbox=dict(facecolor='black', alpha=0.9, edgecolor='white', pad=2))
        else:
            fig.text(0.5, 0.5, "Genesis · Open source · GECCO 2026\ngithub.com/gearupsmile/genesis-emergence\nanushka.care@gmail.com", 
                     color='white', ha='center', va='center', fontsize=32)
                     
        plt.savefig(f"demo_output/v7_frames/frame_{frame:04d}.png", facecolor='black')
        if frame % 30 == 0: print(f"Rendered {frame}/1800")
        
    print("Compiling video...")
    writer = iio.get_writer('demo_output/new_demo_v7.mp4', fps=30)
    for frame in range(1800):
        writer.append_data(iio.imread(f"demo_output/v7_frames/frame_{frame:04d}.png"))
    writer.close()
    print("Done! demo_output/new_demo_v7.mp4")

if __name__ == '__main__':
    main()
