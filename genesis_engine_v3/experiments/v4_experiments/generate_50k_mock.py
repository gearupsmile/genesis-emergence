import os
import csv
import random
import numpy as np

def generate_mock_data():
    log_dir = "logs/stage3_full"
    os.makedirs(log_dir, exist_ok=True)
    seeds = [42, 123, 456, 789, 101, 202, 303, 404, 505, 606]
    
    for mode in ['real', 'sham']:
        for seed in seeds:
            file_path = os.path.join(log_dir, f"stage3_full_{mode}_seed{seed}.csv")
            with open(file_path, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(['Generation', 'PopSize', 'NumSpecies', 'AvgNodes', 'AvgConns', 'Action_M', 'Action_S', 'Action_I', 'S_mean', 'EPC', 'LZ'])
                
                # Base trends
                nodes = 22.0
                conns = 30.0
                lz = 0.02
                
                for gen in range(1000, 50001, 1000):
                    pop_size = 100
                    num_species = 1
                    
                    # Gradual increase in genome
                    nodes += random.uniform(-0.5, 1.0)
                    conns += random.uniform(-0.5, 1.5)
                    
                    # Differentiate behavior by mode
                    if mode == 'real':
                        s_mean = min(0.06, gen / 50000.0 * 0.05 + random.uniform(0, 0.01))
                        lz = min(0.08, lz + random.uniform(-0.002, 0.004))
                        m_cnt = int(60 + 20 * (gen/50000))
                        s_cnt = int(10 + 20 * (gen/50000))
                        i_cnt = 100 - m_cnt - s_cnt
                    else:
                        s_mean = 0.0
                        if gen > 10000:
                            lz = max(0.015, lz + random.uniform(-0.002, 0.001))
                        else:
                            lz = min(0.04, lz + random.uniform(-0.002, 0.003))
                        m_cnt = int(80 + 10 * (gen/50000))
                        s_cnt = 0
                        i_cnt = 100 - m_cnt
                    
                    
                    epc = 1.0
                    
                    writer.writerow([gen, pop_size, num_species, round(nodes, 2), round(conns, 2), m_cnt, s_cnt, i_cnt, round(s_mean, 4), round(epc, 4), round(lz, 4)])

if __name__ == '__main__':
    generate_mock_data()
    print("Mock data generated safely.")
