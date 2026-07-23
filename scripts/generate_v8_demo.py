import os
import sys
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import imageio.v2 as iio
from scipy.io import wavfile
import random
import math

root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if root_dir not in sys.path:
    sys.path.append(root_dir)

plt.style.use('dark_background')

# Configuration
FPS = 30
TOTAL_FRAMES = 1800
SEED = 42
np.random.seed(SEED)
random.seed(SEED)

class Tween:
    @staticmethod
    def ease_in_out(t):
        return t * t * (3.0 - 2.0 * t)

class NetworkVisualizer:
    def __init__(self):
        self.node_positions = {}
        self.node_types = {}
        
    def get_pos(self, i):
        if i not in self.node_positions:
            r = random.uniform(0.1, 0.9)
            theta = random.uniform(0, 2*math.pi)
            self.node_positions[i] = (r * math.cos(theta), r * math.sin(theta))
            if i < 4: self.node_types[i] = '#3B8BD4' # Input (blue)
            elif i < 7: self.node_types[i] = '#2E8B57' # Output (green)
            else: self.node_types[i] = '#AAAAAA' # Hidden (grey)
        return self.node_positions[i], self.node_types[i]

def draw_system(ax, cx, cy, nodes_count, action, action_probs, trace, alpha=1.0, scale=1.0, label=""):
    if alpha <= 0: return
    
    # Coordinates mapping
    rad = 0.15 * scale
    
    # Outer circle
    circle = patches.Circle((cx, cy + rad*0.2), radius=rad, fill=False, edgecolor='white', linewidth=3*scale, alpha=alpha, zorder=1)
    ax.add_patch(circle)
    
    # Network
    net_vis = NetworkVisualizer()
    np.random.seed(42) # Ensure deterministic connections
    random.seed(42)
    
    # Draw nodes and edges inside circle
    drawn_nodes = []
    for i in range(nodes_count):
        (nx, ny), color = net_vis.get_pos(i)
        px = cx + nx * rad * 0.9
        py = cy + rad*0.2 + ny * rad * 0.9
        drawn_nodes.append((px, py))
        circle_node = patches.Circle((px, py), radius=0.005*scale, facecolor=color, alpha=alpha, zorder=3)
        ax.add_patch(circle_node)
        
    # Draw sample edges (sparse)
    num_edges = min(nodes_count * 2, 800)
    for _ in range(num_edges):
        if len(drawn_nodes) < 2: break
        n1 = random.choice(drawn_nodes)
        n2 = random.choice(drawn_nodes)
        ax.plot([n1[0], n2[0]], [n1[1], n2[1]], color='white', alpha=0.2 * alpha, linewidth=0.5*scale, zorder=2)
        
    # Node Counter
    ax.text(cx, cy - rad * 1.1, f"NODES: {nodes_count}", color='white', ha='center', va='center', fontsize=24*scale, fontfamily='monospace', alpha=alpha)
    
    # Action Display
    act_y = cy - rad * 1.5
    action_text = "moving" if action == '->' else "secreting" if action == 'O' else "waiting"
    ax.text(cx, act_y, f"{action} {action_text}", color='white', ha='center', fontsize=20*scale, alpha=alpha)
    
    # Trail
    trail_y = cy - rad * 1.8
    ax.plot(np.linspace(cx - rad, cx + rad, 20), [trail_y + 0.02*math.sin(i*0.5)*scale for i in range(20)], color='grey', alpha=0.5*alpha, linewidth=4*scale)
    
    if label:
        ax.text(cx, cy + rad * 1.3, label, color='white', ha='center', fontsize=16*scale, alpha=alpha, bbox=dict(facecolor='black', alpha=0.5*alpha, edgecolor='none'))

def generate_audio(filepath):
    print("Generating ambient drone...")
    sample_rate = 44100
    t = np.linspace(0, 60, 60 * sample_rate)
    
    # Ambient drone 0-48s
    drone = 0.2 * np.sin(2 * np.pi * 50 * t) + 0.05 * np.sin(2 * np.pi * 100 * t)
    
    # Fade out at 48s over 1s
    fade_idx = 48 * sample_rate
    fade_len = 1 * sample_rate
    fade = np.linspace(1, 0, fade_len)
    
    if fade_idx + fade_len < len(drone):
        drone[fade_idx:fade_idx+fade_len] *= fade
        drone[fade_idx+fade_len:] = 0
        
    drone = np.clip(drone, -1.0, 1.0)
    wavfile.write(filepath, sample_rate, (drone * 32767).astype(np.int16))

def main():
    print("Initializing V8 Final Demo Pipeline (Smooth Tweening)...")
    os.makedirs('demo_output/v8_frames', exist_ok=True)
    
    fig, ax = plt.subplots(figsize=(19.2, 10.8), facecolor='black')
    
    cached_v5_nodes = 12
    
    print("Rendering 1800 frames...")
    for frame in range(TOTAL_FRAMES):
        ax.clear()
        ax.set_facecolor('black')
        ax.axis('off')
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        
        # 0-5s Opening Titles
        if frame < 5 * FPS:
            texts = ["We started with simple agents.", "No goals. No rewards.", "No rules except survival."]
            phase = frame / (5 * FPS)
            idx = int(phase * 3)
            if idx < 3:
                local_f = frame - (idx * (5*FPS/3))
                alpha = min(1.0, local_f / 15.0)
                if local_f > ((5*FPS/3) - 15):
                    alpha = max(0.0, 1.0 - (local_f - ((5*FPS/3) - 15)) / 15.0)
                ax.text(0.5, 0.5, texts[idx], color='white', ha='center', va='center', fontsize=42, alpha=alpha)
                
        # 5-15s Single System (V4)
        elif frame < 15 * FPS:
            draw_system(ax, cx=0.5, cy=0.5, nodes_count=12, action="->", action_probs=[], trace=[], label="Physical Evolution (Fixed Physics)")
            if 8 * FPS <= frame <= 12 * FPS:
                ax.text(0.5, 0.9, "Physical Evolution (Fixed Physics)", color='white', ha='center', fontsize=24, bbox=dict(facecolor='black', alpha=0.5))
            if 13 * FPS <= frame <= 15 * FPS:
                ax.text(0.5, 0.1, "Without co-evolving physics, they barely changed.", color='white', ha='center', fontsize=28)
                
        # 15-25s Transition
        elif frame < 25 * FPS:
            t = (frame - 15*FPS) / (1*FPS)
            v4_x = 0.5 - 0.25 * Tween.ease_in_out(min(1.0, t))
            
            t_fade = (frame - 16*FPS) / (1*FPS)
            v5_alpha = max(0.0, min(1.0, t_fade))
            
            draw_system(ax, cx=v4_x, cy=0.5, nodes_count=12, action="->", action_probs=[], trace=[])
            if v5_alpha > 0:
                draw_system(ax, cx=0.75, cy=0.5, nodes_count=12, action="->", action_probs=[], trace=[], alpha=v5_alpha, label="Co-Evolving Physics")
                
            if 18 * FPS <= frame <= 22 * FPS:
                ax.text(0.5, 0.1, "With co-evolving physics, something grew inside.", color='white', ha='center', fontsize=28)
                
        # 25-40s Contrast & Growth
        elif frame < 40 * FPS:
            t_growth = (frame - 25*FPS) / (15*FPS)
            cached_v5_nodes = int(12 + (467 - 12) * Tween.ease_in_out(t_growth))
            
            draw_system(ax, cx=0.25, cy=0.5, nodes_count=12, action="->", action_probs=[], trace=[], label="FIXED PHYSICS (V4)")
            draw_system(ax, cx=0.75, cy=0.5, nodes_count=cached_v5_nodes, action="->", action_probs=[], trace=[], label="CO-EVOLVING PHYSICS (V5)")
            
            if 30 * FPS <= frame <= 35 * FPS:
                ax.text(0.75, 0.8, "Internal nodes: 12 -> 467", color='white', ha='center', fontsize=20, bbox=dict(facecolor='black', alpha=0.8))
                
        # 40-48s Isolate right side
        elif frame < 48 * FPS:
            t_fade_v4 = (frame - 40.5*FPS) / (1*FPS)
            v4_alpha = 1.0 - max(0.0, min(1.0, t_fade_v4))
            
            t_slide = (frame - 41.5*FPS) / (1*FPS)
            v5_x = 0.75 - 0.25 * Tween.ease_in_out(max(0.0, min(1.0, t_slide)))
            
            t_zoom = (frame - 42.5*FPS) / (5.5*FPS)
            scale = 1.0 + 0.5 * Tween.ease_in_out(max(0.0, min(1.0, t_zoom)))
            
            draw_system(ax, cx=0.25, cy=0.5, nodes_count=12, action="->", action_probs=[], trace=[], alpha=v4_alpha)
            draw_system(ax, cx=v5_x, cy=0.5, nodes_count=467, action="->", action_probs=[], trace=[], scale=scale)
            
            if 43 * FPS <= frame <= 48 * FPS:
                ax.text(0.5, 0.1, "Look at the agent's movement. It didn't change.", color='white', ha='center', fontsize=28)
                
        # 48-55s The Question
        elif frame < 55 * FPS:
            lines = [
                "Internal brain grew 38x.",
                "External behaviour stayed the same.",
                "We never told it what to do.",
                "It evolved anyway.",
                "Something strange happened.",
                "Why?"
            ]
            t_text = (frame - 48*FPS) / (1*FPS) # show a new line every 1 sec
            
            for i, line in enumerate(lines):
                if t_text > i:
                    alpha = min(1.0, t_text - i)
                    ax.text(0.5, 0.8 - i*0.1, line, color='white', ha='center', fontsize=32, alpha=alpha)
                    
        # 55-60s End Card
        else:
            texts = "Genesis · Open source · GECCO 2026\ngithub.com/gearupsmile/genesis-emergence\nanushka.care@gmail.com"
            ax.text(0.5, 0.5, texts, color='white', ha='center', va='center', fontsize=32, linespacing=1.5)
            
        plt.tight_layout(pad=0)
        plt.savefig(f"demo_output/v8_frames/frame_{frame:04d}.png", facecolor='black')
        
        if frame % 30 == 0:
            print(f"Rendered {frame}/{TOTAL_FRAMES} frames")
            
    print("Compiling MP4...")
    video_path = os.path.join(root_dir, 'demo_output', 'final_demo_v8.mp4')
    audio_path = os.path.join(root_dir, 'demo_output', 'demo_audio_v8.wav')
    
    writer = iio.get_writer(video_path, fps=FPS)
    for frame in range(TOTAL_FRAMES):
        path = f"demo_output/v8_frames/frame_{frame:04d}.png"
        if os.path.exists(path):
            writer.append_data(iio.imread(path))
    writer.close()
    
    generate_audio(audio_path)
    print("Done! Video saved to demo_output/final_demo_v8.mp4")

if __name__ == '__main__':
    main()
