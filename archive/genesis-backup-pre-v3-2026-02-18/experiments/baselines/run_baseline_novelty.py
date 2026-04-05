"""
Novelty Search Baseline
Pure novelty-driven evolution without fitness objectives
"""

import numpy as np
import json
from pathlib import Path
from collections import deque

class NoveltySearchBaseline:
    """
    Novelty Search baseline that replaces fitness with behavioral novelty.
    Uses PNCT metrics (GAC, EPC, NND) as behavioral characterization.
    """
    
    def __init__(self, population_size=50, generations=10000, seed=42, k_nearest=15):
        self.population_size = population_size
        self.generations = generations
        self.seed = seed
        self.k_nearest = k_nearest  # For novelty calculation
        
        np.random.seed(seed)
        
        # Novelty archive
        self.archive = []
        self.archive_threshold = 0.5  # Minimum novelty to enter archive
        
        # Metrics tracking
        self.metrics = {
            'generation': [],
            'gac': [],
            'mean_novelty': [],
            'archive_size': []
        }
        
    def initialize_population(self):
        """Create initial random population"""
        population = []
        for i in range(self.population_size):
            agent = {
                'id': i,
                'genome_length': np.random.randint(5, 15),
                'behavior': self._random_behavior()
            }
            population.append(agent)
        return population
    
    def _random_behavior(self):
        """Generate random behavioral descriptor (GAC, EPC, NND)"""
        return np.array([
            np.random.uniform(10, 30),   # GAC
            np.random.uniform(5, 20),    # EPC
            np.random.uniform(0.5, 0.9)  # NND
        ])
    
    def calculate_novelty(self, agent, population):
        """Calculate novelty as average distance to k-nearest neighbors"""
        # Combine population and archive for comparison
        all_behaviors = [a['behavior'] for a in population] + \
                       [a['behavior'] for a in self.archive]
        
        if len(all_behaviors) < self.k_nearest:
            return 1.0  # High novelty if not enough neighbors
        
        # Calculate distances to all other behaviors
        distances = []
        for behavior in all_behaviors:
            if not np.array_equal(behavior, agent['behavior']):
                dist = np.linalg.norm(agent['behavior'] - behavior)
                distances.append(dist)
        
        # Average distance to k-nearest neighbors
        distances.sort()
        k = min(self.k_nearest, len(distances))
        novelty = np.mean(distances[:k])
        
        return novelty
    
    def select_by_novelty(self, population):
        """Select individuals based on novelty scores"""
        # Calculate novelty for each agent
        novelties = []
        for agent in population:
            novelty = self.calculate_novelty(agent, population)
            novelties.append((agent, novelty))
        
        # Sort by novelty (highest first)
        novelties.sort(key=lambda x: x[1], reverse=True)
        
        # Update archive with highly novel individuals
        for agent, novelty in novelties[:5]:  # Top 5 most novel
            if novelty > self.archive_threshold:
                self.archive.append({
                    'behavior': agent['behavior'].copy(),
                    'genome_length': agent['genome_length']
                })
        
        # Limit archive size
        if len(self.archive) > 200:
            self.archive = self.archive[-200:]
        
        # Return top half by novelty
        selected = [agent for agent, _ in novelties[:self.population_size//2]]
        return selected, np.mean([n for _, n in novelties])
    
    def mutate(self, agent):
        """Create offspring with mutation"""
        child = {
            'id': agent['id'],
            'genome_length': agent['genome_length'],
            'behavior': agent['behavior'].copy()
        }
        
        # Mutate genome length
        if np.random.random() < 0.3:
            child['genome_length'] += np.random.randint(-2, 3)
            child['genome_length'] = max(5, child['genome_length'])
        
        # Mutate behavior (exploration in behavior space)
        child['behavior'] += np.random.normal(0, 0.1, size=3)
        child['behavior'] = np.clip(child['behavior'], 0, None)
        
        return child
    
    def run(self):
        """Execute novelty search experiment"""
        print(f"Starting Novelty Search Baseline (seed={self.seed})...")
        
        population = self.initialize_population()
        
        for gen in range(self.generations):
            # Select by novelty
            selected, mean_novelty = self.select_by_novelty(population)
            
            # Create offspring
            new_population = []
            for i in range(self.population_size):
                parent = selected[i % len(selected)]
                child = self.mutate(parent)
                child['id'] = i
                new_population.append(child)
            
            population = new_population
            
            # Track metrics
            mean_gac = np.mean([a['genome_length'] for a in population])
            self.metrics['generation'].append(gen)
            self.metrics['gac'].append(mean_gac)
            self.metrics['mean_novelty'].append(mean_novelty)
            self.metrics['archive_size'].append(len(self.archive))
            
            if gen % 1000 == 0:
                print(f"Gen {gen}: GAC = {mean_gac:.2f}, Novelty = {mean_novelty:.3f}, Archive = {len(self.archive)}")
        
        return self.metrics
    
    def save_results(self, output_dir='results/baselines'):
        """Save metrics to CSV and JSON"""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Save JSON
        json_file = output_path / f'novelty_seed_{self.seed}.json'
        with open(json_file, 'w') as f:
            json.dump(self.metrics, f, indent=2)
        
        # Save CSV for easy plotting
        csv_file = output_path / f'novelty_seed_{self.seed}.csv'
        with open(csv_file, 'w') as f:
            f.write('generation,gac,mean_novelty,archive_size\n')
            for i in range(len(self.metrics['generation'])):
                f.write(f"{self.metrics['generation'][i]},"
                       f"{self.metrics['gac'][i]},"
                       f"{self.metrics['mean_novelty'][i]},"
                       f"{self.metrics['archive_size'][i]}\n")
        
        print(f"Results saved to {json_file} and {csv_file}")
        return json_file, csv_file

if __name__ == '__main__':
    # Run with 3 different seeds
    seeds = [42, 123, 456]
    
    for seed in seeds:
        exp = NoveltySearchBaseline(
            population_size=50,
            generations=10000,
            seed=seed,
            k_nearest=15
        )
        metrics = exp.run()
        exp.save_results()
    
    print("\nNovelty Search baseline complete!")
