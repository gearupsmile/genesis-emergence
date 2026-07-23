import argparse
import sys
import os
import pygame
import csv
import numpy as np

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

from demo_viz.demo_config import *
from demo_viz.demo_visualizer import Visualizer
from demo_viz.demo_export import compile_video, create_zip

def load_csv_data(csv_path):
    data = []
    with open(csv_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            data.append(row)
    return data

def get_substrate_map(gen, substrate_dir, side):
    # Interpolates the substrate map between the nearest 50-generation boundaries
    g1 = (gen // 50) * 50
    if g1 == 0: g1 = 1
    g2 = min(2000, g1 + 50 if g1 > 1 else 50)
    
    path1 = os.path.join(substrate_dir, f'{side}_sub_{g1}.npy')
    path2 = os.path.join(substrate_dir, f'{side}_sub_{g2}.npy')
    
    if not os.path.exists(path1):
        return None
        
    try:
        u1 = np.load(path1)
        if g1 == g2 or gen == g1 or not os.path.exists(path2):
            return u1
        u2 = np.load(path2)
        t = (gen - g1) / float(g2 - g1)
        return (1.0 - t) * u1 + t * u2
    except Exception as e:
        print(f"Error loading substrate map for gen {gen}: {e}")
        return None

def main():
    parser = argparse.ArgumentParser(description="Genesis V5 Cinematic Storyboard Renderer")
    parser.add_argument('--test', action='store_true', help='Render a short 200 frame test clip')
    args = parser.parse_args()
    
    output_dir = os.path.join(BASE_DIR, 'demo_output')
    logs_dir = os.path.join(output_dir, 'logs')
    csv_path = os.path.join(logs_dir, 'demo_simulation_data.csv')
    substrate_dir = os.path.join(logs_dir, 'substrates')
    
    if not os.path.exists(csv_path):
        print(f"ERROR: Simulation log file not found at {csv_path}. Run generate_logs.py first.")
        sys.exit(1)
        
    print("Loading simulation trace data...")
    trace_data = load_csv_data(csv_path)
    print(f"Loaded {len(trace_data)} steps of simulation trace.")
    
    # 1. Initialize Visualizer
    viz = Visualizer()
    
    # Clear old frames
    for f in os.listdir(FRAMES_DIR):
        if f.endswith('.png'):
            os.remove(os.path.join(FRAMES_DIR, f))
            
    # Timeline config
    # 30fps video, total 1800 frames (60 seconds)
    total_frames = 200 if args.test else 1800
    
    decoupling_triggered = False
    decoupling_frame_start = -1
    
    save_idx = 0
    frame_idx = 0
    while frame_idx < total_frames:
        # Determine storyboard phase
        # Phase 1: Opening Titles (0-120 frames / 0-4 seconds)
        if frame_idx < 120 and not args.test:
            viz.render_opening_titles(frame_idx)
            frame_path = os.path.join(FRAMES_DIR, f"frame_{save_idx:04d}.png")
            pygame.image.save(viz.screen, frame_path)
            save_idx += 1
            frame_idx += 1
            continue
            
        # Phase 6: End Card (1650-1800 frames / 55-60 seconds)
        if frame_idx >= 1650 and not args.test:
            viz.render_end_card(frame_idx - 1650)
            frame_path = os.path.join(FRAMES_DIR, f"frame_{save_idx:04d}.png")
            pygame.image.save(viz.screen, frame_path)
            save_idx += 1
            frame_idx += 1
            continue
            
        # Scale remaining frames to trace data
        # For full run: active simulation frames are 120 to 1650 (1530 frames total)
        # We map these 1530 frames to the 2000 generations of trace data
        if args.test:
            sim_idx = frame_idx
            is_split_screen = True
            show_left_only = False
        else:
            active_frame = frame_idx - 120
            # Phase 2: Single World V4 (120 to 300 frames)
            if frame_idx < 300:
                show_left_only = True
                is_split_screen = False
                # Map 180 frames to first 180 generations
                sim_idx = active_frame
            else:
                show_left_only = False
                is_split_screen = True
                # Map remaining 1350 frames to generations 180 to 2000
                sim_idx = 180 + int((frame_idx - 300) * (1820.0 / 1350.0))
                
        sim_idx = min(len(trace_data) - 1, max(0, sim_idx))
        row = trace_data[sim_idx]
        gen = int(row['generation'])
        
        # Load nearest substrate maps
        left_sub_U = get_substrate_map(gen, substrate_dir, 'left')
        right_sub_U = get_substrate_map(gen, substrate_dir, 'right')
        
        # Trigger decoupling moment dynamically
        right_nodes = float(row['right_avg_nodes'])
        # Hardcode high similarity for decoupling prompt as requested
        similarity = 0.95
        
        # Render the frame
        viz.render_frame(frame_idx, row, left_sub_U, right_sub_U, similarity, is_split_screen, show_left_only)
        
        # Save frame image
        frame_path = os.path.join(FRAMES_DIR, f"frame_{save_idx:04d}.png")
        pygame.image.save(viz.screen, frame_path)
        save_idx += 1
        
        # Handle dynamic cinematic events (pulse & freeze)
        if not decoupling_triggered and (right_nodes > 350 or gen >= 1350) and not args.test:
            decoupling_triggered = True
            decoupling_frame_start = frame_idx
            
            # 1. Amber Flash on the right: render right screen overlay and save
            pulse_surf = pygame.Surface((viz.sub_width, viz.sub_height), pygame.SRCALPHA)
            pulse_surf.fill((255, 165, 0, 150))
            
            temp_right = viz.right_surface.copy()
            temp_right.blit(pulse_surf, (0, 0))
            
            viz.screen.blit(viz.left_surface, (0, 0))
            viz.screen.blit(temp_right, (viz.sub_width, 0))
            pygame.draw.line(viz.screen, (100, 100, 100), (viz.sub_width, 0), (viz.sub_width, viz.sub_height), 2)
            pygame.display.flip()
            
            # Save the flashed frame
            pulse_frame_path = os.path.join(FRAMES_DIR, f"frame_{save_idx:04d}.png")
            pygame.image.save(viz.screen, pulse_frame_path)
            save_idx += 1
            
            # 2. Freeze Frame: Duplicate current frame 9 times (0.3 sec)
            print(">>> EXECUTING CINEMATIC FREEZE FRAME (0.3s) <<<")
            import shutil
            for i in range(9):
                dup_path = os.path.join(FRAMES_DIR, f"frame_{save_idx:04d}.png")
                shutil.copy(pulse_frame_path, dup_path)
                save_idx += 1
                
        frame_idx += 1
        
    pygame.quit()
    print("Frame rendering completed.")
    
    # Export video and raw frames zip
    print("Compiling video...")
    compile_video("demo_video_test.mp4" if args.test else "demo_video.mp4")
    create_zip("raw_frames_test.zip" if args.test else "raw_frames.zip")
    
    print("\n--- STAGE COMPLETE ---")
    print(f"Video file: {os.path.join(VIDEOS_DIR, 'demo_video.mp4')}")
    print(f"Raw frames zip: {os.path.join(VIDEOS_DIR, 'raw_frames.zip')}")

if __name__ == "__main__":
    main()
