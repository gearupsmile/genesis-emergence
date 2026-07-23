import os
import csv
import json
import math
import numpy as np
import random

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
output_dir = os.path.join(BASE_DIR, 'demo_output', 'logs')
os.makedirs(output_dir, exist_ok=True)
substrate_dir = os.path.join(output_dir, 'substrates')
os.makedirs(substrate_dir, exist_ok=True)

csv_path = os.path.join(output_dir, 'demo_simulation_data.csv')

# Generate 2000 generations
GENERATIONS = 2000

def get_v5_nodes(gen):
    # Interpolate between:
    # 0 -> 12
    # 500 -> 47
    # 1000 -> 120
    # 1500 -> 280
    # 2000 -> 467
    if gen <= 500:
        t = gen / 500.0
        return 12.0 * (1 - t) + 47.0 * t
    elif gen <= 1000:
        t = (gen - 500) / 500.0
        return 47.0 * (1 - t) + 120.0 * t
    elif gen <= 1500:
        t = (gen - 1000) / 500.0
        return 120.0 * (1 - t) + 280.0 * t
    else:
        t = (gen - 1500) / 500.0
        return 280.0 * (1 - t) + 467.0 * t

def get_v4_nodes(gen):
    # Linear interpolation from 12 to 60
    t = gen / 2000.0
    return 12.0 * (1 - t) + 60.0 * t

def serialize_fake_network(num_nodes, agent_color_seed):
    # Generate deterministic nodes and connections that grow with num_nodes
    nodes = []
    for i in range(num_nodes):
        n_type = "input" if i < 6 else ("output" if i < 9 else "hidden")
        nodes.append({"id": i, "type": n_type})
        
    conns = []
    # Connect inputs to outputs first, then add hidden connections
    for i in range(num_nodes):
        # Deterministic but pseudo-random weights
        weight = math.sin(i + agent_color_seed) * 2.0
        # Connect to next node and another node
        if num_nodes > 1:
            conns.append({"from": i, "to": (i + 1) % num_nodes, "weight": round(weight, 2)})
            if i % 3 == 0:
                conns.append({"from": i, "to": (i + 5) % num_nodes, "weight": round(weight * 0.5, 2)})
                
    return json.dumps({"nodes": nodes, "connections": conns})

print("Generating interpolated CSV trace data...")

# Generate CSV
with open(csv_path, 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow([
        'generation',
        'left_avg_nodes', 'left_oldest_nodes', 'left_action', 'left_x', 'left_y', 'left_network',
        'right_avg_nodes', 'right_oldest_nodes', 'right_action', 'right_x', 'right_y', 'right_network'
    ])
    
    for gen in range(1, GENERATIONS + 1):
        left_nodes = get_v4_nodes(gen)
        right_nodes = get_v5_nodes(gen)
        
        # Position movement in smooth orbit with small noise
        left_x = 25.0 + 8.0 * math.sin(gen * 0.03) + random.uniform(-0.2, 0.2)
        left_y = 25.0 + 8.0 * math.cos(gen * 0.03) + random.uniform(-0.2, 0.2)
        
        right_x = 25.0 + 10.0 * math.sin(gen * 0.02) + random.uniform(-0.2, 0.2)
        right_y = 25.0 + 10.0 * math.cos(gen * 0.02) + random.uniform(-0.2, 0.2)
        
        # Action sequence: cycle through M, S, I
        phase = gen % 60
        if phase < 40:
            left_act = 'M'
            right_act = 'M'
        elif phase < 50:
            left_act = 'S'
            right_act = 'S'
        else:
            left_act = 'I'
            right_act = 'I'
            
        left_net = serialize_fake_network(int(left_nodes), 10)
        right_net = serialize_fake_network(int(right_nodes), 20)
        
        writer.writerow([
            gen,
            left_nodes, left_nodes, left_act, left_x, left_y, left_net,
            right_nodes, right_nodes, right_act, right_x, right_y, right_net
        ])

print("CSV trace data generated successfully.")

# Generate Substrate npy files
print("Generating interpolated substrate npy files...")
npy_generations = [1] + list(range(50, 2001, 50))

for g in npy_generations:
    left_grid = np.zeros((50, 50), dtype=np.float32)
    right_grid = np.zeros((50, 50), dtype=np.float32)
    
    t_left = g * 0.005
    t_right = g * 0.015
    
    for y in range(50):
        ny = (y / 49.0) * 2.0 - 1.0
        for x in range(50):
            nx = (x / 49.0) * 2.0 - 1.0
            
            val_left = 0.5 + 0.3 * math.sin(nx * 3.0 + t_left) * math.cos(ny * 3.0)
            left_grid[y, x] = max(0.0, min(1.0, val_left))
            
            val_right = 0.5 + 0.35 * math.sin(nx * 4.0 + t_right) * math.cos(ny * 4.0 - t_right) + 0.15 * math.sin((nx+ny)*2.0)
            right_grid[y, x] = max(0.0, min(1.0, val_right))
            
    np.save(os.path.join(substrate_dir, f'left_sub_{g}.npy'), left_grid)
    np.save(os.path.join(substrate_dir, f'right_sub_{g}.npy'), right_grid)

print("Substrate npy files generated successfully.")
