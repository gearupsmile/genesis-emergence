"""
MAP-Elites (Quality-Diversity) Baseline
Fills behavior space but doesn't achieve unbounded growth without objectives
"""

import numpy as np
import json
from pathlib import Path

class MAPElitesBaseline:
    """
    MAP-Elites baseline using a 2D behavior space grid.
    Demonstrates quality-diversity but not open-ended evolution.
    """
    
    def __init__(self, grid_size=(20, 20), generations=10000, seed=42):
        self.grid_size = grid_size
        self.generations = generations
        self.seed = seed
        
        np.random.seed(seed)
        
        # Grid archive: [gene_count_bin, lz_complexity_bin] -> agent
        self.archive = {}
        
        # Behavior space bounds
        self.gene_count_bounds = (5, 100)
        self.lz_complexity_bounds = (5, 50)
        
        # Metrics tracking
        self.metrics = {
            'generation': [],
            'archive_size': [],
            'mean_gac': [],
            'coverage': []
        }
        
    def behavior_to_bin(self, gene_count, lz_complexity):
        """Convert continuous behavior to discrete grid bin"""
        # Normalize to [0, 1]
        gene_norm = (gene_count - self.gene_count_bounds[0]) / \
                   (self.gene_count_bounds[1] - self.gene_count_bounds[0])
        lz_norm = (lz_complexity - self.lz_complexity_bounds[0]) / \
                 (self.lz_complexity_bounds[1] - self.lz_complexity_bounds[0])
        
        # Clip and convert to bin
        gene_norm = np.clip(gene_norm, 0, 0.999)
        lz_norm = np.clip(lz_norm, 0, 0.999)
        
        bin_x = int(gene_norm * self.grid_size[0])
        bin_y = int(lz_norm * self.grid_size[1])
        
        return (bin_x, bin_y)
    
    def create_random_agent(self):
        """Create random agent"""
        gene_count = np.random.randint(10, 30)
        lz_complexity = gene_count * 0.6 + np.random.normal(0, 2)
        lz_complexity = max(5, lz_complexity)
        
        return {
            'gene_count': gene_count,
            'lz_complexity': lz_complexity,
            'quality': np.random.random()  # Minimal quality metric
        }
    
    def mutate(self, agent):
        """Mutate an agent"""
        child = agent.copy()
        
        # Mutate gene count
        if np.random.random() < 0.5:
            child['gene_count'] += np.random.randint(-3, 4)
            child['gene_count'] = max(5, min(100, child['gene_count']))
        
        # Mutate LZ complexity (correlated with gene count)
        if np.random.random() < 0.5:
            child['lz_complexity'] += np.random.normal(0, 2)
            child['lz_complexity'] = max(5, min(50, child['lz_complexity']))
        
        # Mutate quality slightly
        child['quality'] = agent['quality'] + np.random.normal(0, 0.1)
        child['quality'] = np.clip(child['quality'], 0, 1)
        
        return child
    
    def add_to_archive(self, agent):
        """Add agent to archive if it's better in its bin"""
        bin_coords = self.behavior_to_bin(agent['gene_count'], agent['lz_complexity'])
        
        # If bin is empty or agent is better, add it
        if bin_coords not in self.archive or \
           agent['quality'] > self.archive[bin_coords]['quality']:
            self.archive[bin_coords] = agent.copy()
            return True
        return False
    
    def run(self):
        """Execute MAP-Elites experiment"""
        print(f"Starting MAP-Elites Baseline (seed={self.seed})...")
        
        # Initialize with random agents
        for _ in range(100):
            agent = self.create_random_agent()
            self.add_to_archive(agent)
        
        for gen in range(self.generations):
            # Sample random agent from archive
            if len(self.archive) > 0:
                parent = np.random.choice(list(self.archive.values()))
                
                # Create and mutate offspring
                for _ in range(10):  # 10 offspring per generation
                    child = self.mutate(parent)
                    self.add_to_archive(child)
            
            # Track metrics
            if len(self.archive) > 0:
                mean_gac = np.mean([a['gene_count'] for a in self.archive.values()])
                coverage = len(self.archive) / (self.grid_size[0] * self.grid_size[1])
            else:
                mean_gac = 0
                coverage = 0
            
            self.metrics['generation'].append(gen)
            self.metrics['archive_size'].append(len(self.archive))
            self.metrics['mean_gac'].append(mean_gac)
            self.metrics['coverage'].append(coverage)
            
            if gen % 1000 == 0:
                print(f"Gen {gen}: Archive = {len(self.archive)}, "
                      f"GAC = {mean_gac:.2f}, Coverage = {coverage*100:.1f}%")
        
        return self.metrics
    
    def save_results(self, output_dir='results/baselines'):
        """Save metrics and archive state"""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Save metrics JSON
        json_file = output_path / f'mapelites_seed_{self.seed}.json'
        with open(json_file, 'w') as f:
            json.dump(self.metrics, f, indent=2)
        
        # Save CSV
        csv_file = output_path / f'mapelites_seed_{self.seed}.csv'
        with open(csv_file, 'w') as f:
            f.write('generation,archive_size,mean_gac,coverage\n')
            for i in range(len(self.metrics['generation'])):
                f.write(f"{self.metrics['generation'][i]},"
                       f"{self.metrics['archive_size'][i]},"
                       f"{self.metrics['mean_gac'][i]},"
                       f"{self.metrics['coverage'][i]}\n")
        
        # Save final archive state
        archive_file = output_path / f'mapelites_archive_seed_{self.seed}.json'
        archive_data = {
            f"{k[0]},{k[1]}": {
                'gene_count': v['gene_count'],
                'lz_complexity': v['lz_complexity'],
                'quality': v['quality']
            }
            for k, v in self.archive.items()
        }
        with open(archive_file, 'w') as f:
            json.dump(archive_data, f, indent=2)
        
        print(f"Results saved to {json_file}, {csv_file}, and {archive_file}")
        return json_file, csv_file

if __name__ == '__main__':
    # Run with 3 different seeds
    seeds = [42, 123, 456]
    
    for seed in seeds:
        exp = MAPElitesBaseline(
            grid_size=(20, 20),
            generations=10000,
            seed=seed
        )
        metrics = exp.run()
        exp.save_results()
    
    print("\nMAP-Elites baseline complete!")
