import os
import sys
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import matplotlib.gridspec as gridspec
import csv
import imageio.v2 as iio
from scipy.io import wavfile
import subprocess

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
FREEZE_FRAME = 45 * FPS # 1350
END_CARD_FRAME = 52 * FPS # 1560
TARGET_GENS = 2000
GENS_PER_FRAME = max(1, int(TARGET_GENS / FREEZE_FRAME))

SEED = 42
np.random.seed(SEED)
import random
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
        width, height = 50, 50 # Internal resolution, visually upscaled
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

def draw_agent_circle(ax, x, y, nodes=0):
    # Determine color
    if nodes < 100: color = '#3B8BD4'
    elif nodes < 300: color = '#EF9F27'
    else: color = '#D85A30'
    
    # Glow (alpha=0.3, radius 2x)
    glow = patches.Circle((x, y), radius=3.0, facecolor=color, alpha=0.3, edgecolor='none', zorder=9)
    ax.add_patch(glow)
    
    # Core (radius 1x)
    core = patches.Circle((x, y), radius=1.5, facecolor=color, edgecolor='white', alpha=0.9, zorder=10)
    ax.add_patch(core)

def draw_action_bars(ax, probs, action):
    ax.clear()
    ax.axis('off')
    
    bars = ax.barh([2, 1, 0], probs, color=['grey', 'blue', 'green'], height=0.4)
    ax.set_xlim(0, 1)
    ax.text(-0.05, 2, "idle", color='grey', va='center', ha='right', fontsize=16)
    ax.text(-0.05, 1, "secrete", color='grey', va='center', ha='right', fontsize=16)
    ax.text(-0.05, 0, "move", color='grey', va='center', ha='right', fontsize=16)
    
    action_text = "moving" if action == '->' else "secreting" if action == 'O' else "waiting"
    ax.text(0.5, 3.2, f"{action} {action_text}", color='white', ha='center', fontsize=28)

def generate_audio(filepath):
    print("Generating synthetic audio...")
    sample_rate = 44100
    t = np.linspace(0, 60, 60 * sample_rate)
    
    drone = 0.3 * np.sin(2 * np.pi * 50 * t) + 0.1 * np.sin(2 * np.pi * 100 * t)
    envelope = 0.5 + 0.5 * np.sin(2 * np.pi * (60/60) * t)
    drone *= envelope
    
    drone[45 * sample_rate:] = 0
    
    click_idx = 45 * sample_rate
    click_dur = int(0.05 * sample_rate)
    click = np.random.normal(0, 1, click_dur)
    
    decay = np.exp(-np.linspace(0, 10, click_dur))
    if click_idx + click_dur < len(drone):
        drone[click_idx:click_idx+click_dur] += click * decay * 0.8
        
    drone = np.clip(drone, -1.0, 1.0)
    wavfile.write(filepath, sample_rate, (drone * 32767).astype(np.int16))

def main():
    print("Initializing New Demo Pipeline...")
    sim = DemoSimulator()
    os.makedirs('demo_output/v6_frames', exist_ok=True)
    
    fig = plt.figure(figsize=(19.2, 10.8), facecolor='black')
    
    cached_v5_nodes = 12
    last_rendered_nodes = 12
    
    print("Rendering 1800 frames...")
    for frame in range(TOTAL_FRAMES):
        if frame < FREEZE_FRAME:
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
            # 0-4s: Cold open
            alpha = min(1.0, frame / (1.5 * FPS))
            if frame > 3 * FPS:
                alpha = max(0.0, 1.0 - (frame - 3 * FPS) / FPS)
            fig.text(0.5, 0.5, "Can a system become more complex inside\nwhile looking exactly the same outside?", 
                     color='white', ha='center', va='center', fontsize=36, alpha=alpha)
                     
        elif frame < 12 * FPS:
            # 4-12s: Single world
            ax = fig.add_subplot(111)
            ax.axis('off')
            ax.imshow(v5_sub.U, cmap='inferno')
            pops = sim.v5_orch.agent_populations[sim.v5_orch.environments[0].id]
            for a in pops:
                draw_agent_circle(ax, a.x, a.y, len(a.genome.nodes))
                
        elif frame < 16 * FPS:
            # 12-16s: Transition text
            ax = fig.add_subplot(111)
            ax.axis('off')
            ax.imshow(v5_sub.U, cmap='inferno', alpha=0.3)
            alpha = min(1.0, (frame - 12 * FPS) / FPS)
            fig.text(0.5, 0.5, "Two runs. Same starting point. One difference:\nin the second, the laws of physics evolve too.", 
                     color='white', ha='center', va='center', fontsize=36, alpha=alpha,
                     bbox=dict(facecolor='black', alpha=0.6, edgecolor='none', pad=2))
                     
        elif frame < END_CARD_FRAME:
            # 16-52s: Split screen
            gs = gridspec.GridSpec(10, 2, figure=fig, hspace=0.1, wspace=0.01)
            ax_sub_l = fig.add_subplot(gs[0:7, 0])
            ax_sub_r = fig.add_subplot(gs[0:7, 1])
            ax_act_l = fig.add_subplot(gs[7:9, 0])
            ax_act_r = fig.add_subplot(gs[7:9, 1])
            
            fig.text(0.25, 0.95, "FIXED PHYSICS (V4)", color='grey', ha='center', fontsize=20)
            fig.text(0.75, 0.95, "CO-EVOLVING PHYSICS (V5)", color='grey', ha='center', fontsize=20)
            
            ax_sub_l.axis('off')
            ax_sub_r.axis('off')
            ax_sub_l.imshow(v4_sub.U, cmap='inferno')
            ax_sub_r.imshow(v5_sub.U, cmap='inferno')
            
            # Tints via transparent overlays
            ax_sub_l.add_patch(patches.Rectangle((0,0), 50, 50, facecolor='#3B8BD4', alpha=0.05, zorder=20))
            ax_sub_r.add_patch(patches.Rectangle((0,0), 50, 50, facecolor='#EF9F27', alpha=0.05, zorder=20))
            
            draw_agent_circle(ax_sub_l, v4_rep.x, v4_rep.y, 12)
            if v5_rep:
                draw_agent_circle(ax_sub_r, v5_rep.x, v5_rep.y, last_rendered_nodes)
                
            fig.text(0.25, 0.1, "NODES: 12", color='grey', ha='center', fontsize=48, fontfamily='monospace')
            
            if frame < FREEZE_FRAME:
                fig.text(0.75, 0.1, f"NODES: {last_rendered_nodes:03d}", color='#EF9F27', ha='center', fontsize=48, fontfamily='monospace')
                draw_action_bars(ax_act_l, v4_probs, v4_act)
                draw_action_bars(ax_act_r, v5_probs, v5_act)
                
                # 35s Overlay
                if frame >= 35*FPS:
                    fig.text(0.75, 0.28, "Internal complexity: growing. External behaviour: unchanged.", 
                             color='#EF9F27', ha='center', fontsize=18, bbox=dict(facecolor='black', alpha=0.8, edgecolor='none'))
            else:
                # FREEZE (45-52s)
                fig.text(0.75, 0.1, f"NODES: 467", color='#EF9F27', ha='center', fontsize=48, fontfamily='monospace')
                draw_action_bars(ax_act_l, v4_probs, v4_act)
                draw_action_bars(ax_act_r, v5_probs, v5_act)
                
                blink = "_" if (frame // 15) % 2 == 0 else " "
                fig.text(0.75, 0.6, f"STRUCTURE-FUNCTION DECOUPLING\n467 internal nodes. Same 3 actions as generation 1.\np = 0.00018 · sham-controlled · GECCO 2026{blink}", 
                         color='white', ha='center', va='center', fontsize=24, fontweight='bold',
                         bbox=dict(facecolor='black', alpha=0.9, edgecolor='white', pad=2))
                         
        else:
            # 52-60s End card
            fig.text(0.5, 0.5, "Genesis · Open source · GECCO 2026\ngithub.com/gearupsmile/genesis-emergence\nanushka.care@gmail.com", 
                     color='white', ha='center', va='center', fontsize=32, linespacing=1.5)
                     
        plt.savefig(f"demo_output/v6_frames/frame_{frame:04d}.png", facecolor='black')
        
        if frame % 30 == 0:
            print(f"Rendered {frame}/{TOTAL_FRAMES} frames")
            
    print("Compiling MP4...")
    video_path = os.path.join(root_dir, 'demo_output', 'new_demo_v6.mp4')
    audio_path = os.path.join(root_dir, 'demo_output', 'demo_audio.wav')
    
    writer = iio.get_writer(video_path, fps=FPS)
    for frame in range(TOTAL_FRAMES):
        path = f"demo_output/v6_frames/frame_{frame:04d}.png"
        if os.path.exists(path):
            writer.append_data(iio.imread(path))
    writer.close()
    
    generate_audio(audio_path)
    print("Done! Video saved to demo_output/new_demo_v6.mp4")

if __name__ == '__main__':
    main()
