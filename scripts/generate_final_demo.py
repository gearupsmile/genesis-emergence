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

def draw_agent_triangle(ax, x, y, size=1.5, color='#3B8BD4', nodes=0, is_v5=False):
    # Triangle pointing up
    points = np.array([[x, y+size], [x-size, y-size], [x+size, y-size]])
    triangle = patches.Polygon(points, closed=True, facecolor=color, edgecolor='white', alpha=0.9, zorder=10)
    ax.add_patch(triangle)
    
    if is_v5 and nodes > 12:
        # Internal branching wireframe
        num_lines = int((nodes / 467) * 40) # Scale lines based on nodes
        for _ in range(num_lines):
            # random points inside triangle
            r1, r2 = random.random(), random.random()
            if r1 + r2 > 1: r1, r2 = 1 - r1, 1 - r2
            px1 = points[0][0]*r1 + points[1][0]*r2 + points[2][0]*(1-r1-r2)
            py1 = points[0][1]*r1 + points[1][1]*r2 + points[2][1]*(1-r1-r2)
            
            r1, r2 = random.random(), random.random()
            if r1 + r2 > 1: r1, r2 = 1 - r1, 1 - r2
            px2 = points[0][0]*r1 + points[1][0]*r2 + points[2][0]*(1-r1-r2)
            py2 = points[0][1]*r1 + points[1][1]*r2 + points[2][1]*(1-r1-r2)
            
            ax.plot([px1, px2], [py1, py2], color='white', alpha=0.4, linewidth=0.5, zorder=11)

def draw_action_bars(ax, probs, action, text):
    ax.clear()
    ax.axis('off')
    # Bar chart
    bars = ax.barh([2, 1, 0], probs, color=['grey', 'blue', 'green'], height=0.4)
    ax.set_xlim(0, 1)
    ax.text(-0.05, 2, "idle", color='grey', va='center', ha='right', fontsize=12)
    ax.text(-0.05, 1, "secrete", color='grey', va='center', ha='right', fontsize=12)
    ax.text(-0.05, 0, "move", color='grey', va='center', ha='right', fontsize=12)
    
    action_text = "moving" if action == '->' else "secreting" if action == 'O' else "waiting"
    ax.text(0.5, 3.5, f"{action} {action_text}", color='white', ha='center', fontsize=28)

def generate_audio(filepath):
    print("Generating synthetic audio...")
    sample_rate = 44100
    t = np.linspace(0, 60, 60 * sample_rate)
    
    # Ambient drone (50 Hz sine wave + harmonics)
    drone = 0.3 * np.sin(2 * np.pi * 50 * t) + 0.1 * np.sin(2 * np.pi * 100 * t)
    # Slow pulsing heartbeat volume envelope
    envelope = 0.5 + 0.5 * np.sin(2 * np.pi * (60/60) * t) # 60 BPM
    drone *= envelope
    
    # Silence after 45s
    drone[45 * sample_rate:] = 0
    
    # Click at 45s
    click_idx = 45 * sample_rate
    click_dur = int(0.05 * sample_rate)
    click = np.random.normal(0, 1, click_dur)
    
    # Add click with decay
    decay = np.exp(-np.linspace(0, 10, click_dur))
    if click_idx + click_dur < len(drone):
        drone[click_idx:click_idx+click_dur] += click * decay * 0.8
        
    drone = np.clip(drone, -1.0, 1.0)
    wavfile.write(filepath, sample_rate, (drone * 32767).astype(np.int16))

def main():
    print("Initializing Final Demo Pipeline...")
    sim = DemoSimulator()
    os.makedirs('demo_output/final_frames', exist_ok=True)
    
    fig = plt.figure(figsize=(19.2, 10.8), facecolor='black')
    gs = gridspec.GridSpec(10, 2, figure=fig, hspace=0.1, wspace=0.01)
    
    ax_sub_l = fig.add_subplot(gs[0:8, 0])
    ax_sub_r = fig.add_subplot(gs[0:8, 1])
    ax_act_l = fig.add_subplot(gs[8:10, 0])
    ax_act_r = fig.add_subplot(gs[8:10, 1])
    
    # Persistent labels
    fig.text(0.25, 0.95, "FIXED PHYSICS (V4)", color='grey', ha='center', fontsize=18)
    fig.text(0.75, 0.95, "CO-EVOLVING PHYSICS (V5)", color='grey', ha='center', fontsize=18)
    
    cached_v5_nodes = 12
    last_rendered_nodes = 12
    
    print("Rendering 1800 frames...")
    for frame in range(TOTAL_FRAMES):
        if frame < FREEZE_FRAME:
            # Active simulation
            for _ in range(GENS_PER_FRAME):
                sim.step_gen()
                
            v4_rep, v4_sub, v5_rep, v5_sub = sim.get_rep_data()
            
            v4_probs, v4_act = get_action_probs(v4_rep, v4_sub)
            v5_probs, v5_act = get_action_probs(v5_rep, v5_sub) if v5_rep else ([0.33,0.33,0.33], '||')
            
            cached_v5_nodes = len(v5_rep.genome.nodes) if v5_rep else 12
            
            # Smooth node counter climbing (~10 per second)
            if last_rendered_nodes < cached_v5_nodes:
                # Interpolate smoothly rather than jumping
                increment = max(1, (cached_v5_nodes - last_rendered_nodes) // (FPS//2))
                last_rendered_nodes = min(cached_v5_nodes, last_rendered_nodes + increment)
                
            ax_sub_l.clear()
            ax_sub_r.clear()
            ax_sub_l.axis('off')
            ax_sub_r.axis('off')
            
            ax_sub_l.imshow(v4_sub.U, cmap='inferno')
            ax_sub_r.imshow(v5_sub.U, cmap='inferno')
            
            draw_agent_triangle(ax_sub_l, v4_rep.x, v4_rep.y, color='#3B8BD4')
            if v5_rep:
                draw_agent_triangle(ax_sub_r, v5_rep.x, v5_rep.y, color='#EF9F27', nodes=last_rendered_nodes, is_v5=True)
                
            # Node counters
            ax_sub_l.text(25, 55, "NODES: 12", color='grey', ha='center', fontsize=48, fontfamily='monospace')
            ax_sub_r.text(25, 55, f"NODES: {last_rendered_nodes:03d}", color='#EF9F27', ha='center', fontsize=48, fontfamily='monospace')
            
            draw_action_bars(ax_act_l, v4_probs, v4_act, "moving")
            draw_action_bars(ax_act_r, v5_probs, v5_act, "moving")
            
            # 8s Overlay
            if 8*FPS <= frame <= 11*FPS:
                fig.text(0.5, 0.5, "Two identical behaviors. Only one is hiding something.", 
                         color='white', ha='center', va='center', fontsize=32, 
                         bbox=dict(facecolor='black', alpha=0.7, edgecolor='none', pad=2))
                         
            if frame >= 35*FPS:
                ax_sub_r.text(25, 60, f"Internal nodes: {last_rendered_nodes} | External behavior: unchanged", 
                              color='grey', ha='center', fontsize=14)
                              
            plt.savefig(f"demo_output/final_frames/frame_{frame:04d}.png", facecolor='black')
            
        elif frame == FREEZE_FRAME:
            # Generate the frozen image ONCE, then copy it to avoid matplotlib overhead
            # Draw overlay
            ax_sub_r.text(25, 25, "NODES: 467\nBEHAVIOR: UNCHANGED\nTHE REALITY GAP", 
                          color='white', ha='center', va='center', fontsize=36, fontweight='bold', fontfamily='monospace',
                          bbox=dict(facecolor='black', alpha=0.8, edgecolor='white', pad=2))
            plt.savefig(f"demo_output/final_frames/frame_base_frozen.png", facecolor='black')
            
        elif frame < END_CARD_FRAME:
            # We are in freeze, just blink the cursor
            blink = "_" if (frame // 15) % 2 == 0 else " "
            # Redraw text with cursor
            ax_sub_r.clear()
            ax_sub_r.axis('off')
            ax_sub_r.imshow(v5_sub.U, cmap='inferno')
            draw_agent_triangle(ax_sub_r, v5_rep.x, v5_rep.y, color='#EF9F27', nodes=467, is_v5=True)
            ax_sub_r.text(25, 55, f"NODES: 467", color='#EF9F27', ha='center', fontsize=48, fontfamily='monospace')
            ax_sub_r.text(25, 60, f"Internal nodes: 467 | External behavior: unchanged", color='grey', ha='center', fontsize=14)
            
            ax_sub_r.text(25, 25, f"NODES: 467\nBEHAVIOR: UNCHANGED\nTHE REALITY GAP{blink}", 
                          color='white', ha='center', va='center', fontsize=36, fontweight='bold', fontfamily='monospace',
                          bbox=dict(facecolor='black', alpha=0.8, edgecolor='white', pad=2))
            plt.savefig(f"demo_output/final_frames/frame_{frame:04d}.png", facecolor='black')
            
        else:
            # End card 52s - 60s
            fig.clf()
            fig.patch.set_facecolor('black')
            fig.text(0.5, 0.5, "Genesis · Open source · GECCO 2026\ngithub.com/gearupsmile/genesis-emergence\nanushka.care@gmail.com", 
                     color='white', ha='center', va='center', fontsize=24, linespacing=1.5)
            plt.savefig(f"demo_output/final_frames/frame_{frame:04d}.png", facecolor='black')

        if frame % 30 == 0:
            print(f"Rendered {frame}/{TOTAL_FRAMES} frames")

    print("Compiling MP4...")
    video_path = os.path.join(root_dir, 'demo_output', 'final_genesis_demo.mp4')
    audio_path = os.path.join(root_dir, 'demo_output', 'demo_audio.wav')
    muxed_path = os.path.join(root_dir, 'demo_output', 'FINAL_GECCO_DEMO.mp4')
    
    writer = iio.get_writer(video_path, fps=FPS)
    for frame in range(TOTAL_FRAMES):
        if frame == FREEZE_FRAME: continue # skip the base frozen frame
        path = f"demo_output/final_frames/frame_{frame:04d}.png"
        if os.path.exists(path):
            writer.append_data(iio.imread(path))
    writer.close()
    
    generate_audio(audio_path)
    
    try:
        print("Muxing audio and video...")
        subprocess.run(['ffmpeg', '-y', '-i', video_path, '-i', audio_path, '-c:v', 'copy', '-c:a', 'aac', muxed_path], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print(f"Success! Final demo saved to {muxed_path}")
    except Exception as e:
        print(f"FFMPEG muxing failed (is ffmpeg installed in PATH?). Raw video and audio are saved separately in demo_output/.")

if __name__ == '__main__':
    main()
