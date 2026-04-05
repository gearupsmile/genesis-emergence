"""
Multi-world parameter search for optimal evolutionary conditions.

Implements adaptive parameter discovery through parallel world exploration,
learning which conditions create good selection pressure for evolution.
"""

import json
import random
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Tuple
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend

from simulator import SimulationRunner
from parameters import GrayScottParams, get_preset


class ParameterSearcher:
    """Discovers optimal agent parameters through multi-world exploration."""
    
    def __init__(self, output_dir='parameter_search'):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        self.database_path = self.output_dir / 'failure_wisdom.json'
        self.database = self._load_or_create_database()
    
    def _load_or_create_database(self) -> Dict:
        """Load existing database or create new one."""
        if self.database_path.exists():
            with open(self.database_path, 'r') as f:
                return json.load(f)
        
        return {
            'metadata': {
                'created': datetime.now().isoformat(),
                'total_experiments': 0,
                'generations': 0,
                'best_score': 0.0
            },
            'experiments': [],
            'best_parameters': {}
        }
    
    def _save_database(self):
        """Save database to disk."""
        with open(self.database_path, 'w') as f:
            json.dump(self.database, f, indent=2)
        print(f"Database saved: {self.database_path}")
    
    def run_search(self, generations=3, worlds_per_gen=20):
        """Run multi-generation parameter search."""
        
        print(f"\n{'='*70}")
        print(f"ADAPTIVE PARAMETER DISCOVERY")
        print(f"{'='*70}")
        print(f"Generations: {generations}")
        print(f"Worlds per generation: {worlds_per_gen}")
        print(f"Total experiments: {generations * worlds_per_gen}")
        print(f"{'='*70}\n")
        
        for gen in range(1, generations + 1):
            print(f"\n{'='*70}")
            print(f"GENERATION {gen}/{generations}")
            print(f"{'='*70}\n")
            
            # Generate parameter sets
            if gen == 1:
                param_sets = self._generate_random_parameters(worlds_per_gen)
                print(f"Strategy: Random exploration ({worlds_per_gen} worlds)")
            else:
                param_sets = self._generate_focused_parameters(worlds_per_gen)
                print(f"Strategy: 70% focused + 30% exploration ({worlds_per_gen} worlds)")
            
            # Test each parameter set
            gen_scores = []
            for i, params in enumerate(param_sets, 1):
                print(f"\n[Gen {gen}] Testing world {i}/{worlds_per_gen}...")
                print(f"  Parameters: metabolism={params['metabolism']:.3f}, "
                      f"consumption={params['consumption_rate']:.2f}, "
                      f"threshold={params['reproduction_threshold']:.0f}, "
                      f"cost={params['reproduction_cost']:.0f}")
                
                outcomes = self._run_world(params)
                scores = self._score_world(outcomes)
                
                # Record in database
                exp_id = f"exp_{len(self.database['experiments']) + 1:03d}"
                self._record_experiment(exp_id, gen, params, outcomes, scores)
                
                gen_scores.append(scores['total'])
                
                print(f"  Score: {scores['total']:.3f} "
                      f"(pressure={scores['selection_pressure']:.2f}, "
                      f"dynamics={scores['dynamics']:.2f}, "
                      f"survival={scores['survival']:.2f}, "
                      f"health={scores['health']:.2f})")
                print(f"  Outcomes: pop={outcomes['final_population']}, "
                      f"births={outcomes['total_births']}, "
                      f"deaths={outcomes['total_deaths']}, "
                      f"death_rate={outcomes['death_rate']:.1%}")
            
            # Generation summary
            best_gen_score = max(gen_scores)
            avg_gen_score = np.mean(gen_scores)
            print(f"\n{'-'*70}")
            print(f"Generation {gen} Summary:")
            print(f"  Best score: {best_gen_score:.3f}")
            print(f"  Average score: {avg_gen_score:.3f}")
            print(f"{'-'*70}")
            
            # Update best parameters
            self._update_best_parameters(gen)
            
            # Save database after each generation
            self._save_database()
        
        # Final summary
        self._print_final_summary()
        
        # Generate visualization
        self._visualize_results()
        
        # Print recommendations
        self._print_recommendations()
    
    def _generate_random_parameters(self, count: int) -> List[Dict]:
        """Generate random parameter sets for initial exploration."""
        parameter_sets = []
        
        for i in range(count):
            params = {
                'metabolism': random.uniform(0.1, 1.0),
                'consumption_rate': random.uniform(1.0, 10.0),
                'reproduction_threshold': random.uniform(50, 200),
                'reproduction_cost': random.uniform(20, 100)
            }
            parameter_sets.append(params)
        
        return parameter_sets
    
    def _generate_focused_parameters(self, count: int, exploration_ratio=0.3) -> List[Dict]:
        """Generate parameters focused near best findings + continued exploration."""
        
        # Get top 5 performers from previous generations
        top_performers = sorted(
            self.database['experiments'],
            key=lambda x: x['scores']['total'],
            reverse=True
        )[:5]
        
        if not top_performers:
            # Fallback to random if no experiments yet
            return self._generate_random_parameters(count)
        
        parameter_sets = []
        explore_count = int(count * exploration_ratio)
        exploit_count = count - explore_count
        
        # Exploitation: Variations of best performers
        for i in range(exploit_count):
            base = random.choice(top_performers)['parameters']
            
            # Add Gaussian noise (15% std dev)
            params = {
                key: base[key] * random.gauss(1.0, 0.15)
                for key in base.keys()
            }
            
            # Clamp to valid ranges
            params = self._clamp_parameters(params)
            parameter_sets.append(params)
        
        # Exploration: Random new areas
        parameter_sets.extend(self._generate_random_parameters(explore_count))
        
        return parameter_sets
    
    def _clamp_parameters(self, params: Dict) -> Dict:
        """Ensure parameters stay within viable ranges."""
        ranges = {
            'metabolism': (0.1, 1.0),
            'consumption_rate': (1.0, 10.0),
            'reproduction_threshold': (50.0, 200.0),
            'reproduction_cost': (20.0, 100.0)
        }
        
        clamped = {}
        for key, value in params.items():
            min_val, max_val = ranges.get(key, (0.0, float('inf')))
            clamped[key] = max(min_val, min(max_val, value))
        
        return clamped
    
    def _run_world(self, agent_params: Dict) -> Dict:
        """Run a single world simulation with custom agent parameters."""
        
        # Get Gray-Scott parameters
        gs_params = get_preset('spots')
        
        # Create runner with custom agent parameters
        runner = SimulationRunner(
            params=gs_params,
            grid_size=(256, 256),
            output_dir=self.output_dir / 'temp_worlds',
            checkpoint_interval=10000,  # No checkpoints during search
            with_agents=True,
            num_agents=50,
            max_population=1000,
            agent_params=agent_params  # Pass custom parameters
        )
        
        # Initialize
        runner.initialize(initial_pattern='random')
        
        # Run for 2000 cycles
        success = runner.run(
            num_cycles=2000,
            save_snapshots=False
        )
        
        # Collect outcomes
        stats = runner.get_final_statistics()
        
        outcomes = {
            'final_population': stats.get('agent_population', 0),
            'total_births': stats.get('agent_total_births', 0),
            'total_deaths': stats.get('agent_total_deaths', 0),
            'death_rate': 0.0,
            'avg_population': 0.0,
            'population_variance': 0.0,
            'extinction': stats.get('agent_population', 0) == 0,
            'cycles_survived': stats.get('cycle', 0)
        }
        
        # Calculate death rate
        if outcomes['total_births'] > 0:
            outcomes['death_rate'] = outcomes['total_deaths'] / outcomes['total_births']
        
        # Calculate population statistics from history
        if hasattr(runner.population, 'population_history'):
            pop_history = runner.population.population_history
            if pop_history:
                outcomes['avg_population'] = np.mean(pop_history)
                outcomes['population_variance'] = np.var(pop_history)
        
        return outcomes
    
    def _score_world(self, outcomes: Dict) -> Dict:
        """Score a world's evolutionary quality."""
        
        # 1. Selection Pressure (40% weight)
        # Ideal: 60% death rate (40-80% acceptable)
        death_rate = outcomes['death_rate']
        if 0.4 <= death_rate <= 0.8:
            pressure_score = 1.0 - abs(death_rate - 0.6) / 0.2
        else:
            pressure_score = max(0.0, 1.0 - abs(death_rate - 0.6) / 0.6)
        
        # 2. Population Dynamics (30% weight)
        # Variance indicates boom/bust cycles
        variance_score = min(outcomes['population_variance'] / 2000, 1.0)
        
        # 3. Survival (20% weight)
        # Did it run full duration?
        survival_score = 1.0 if not outcomes['extinction'] else 0.0
        
        # 4. Health (10% weight)
        # Average population in 50-150 range
        avg_pop = outcomes['avg_population']
        if 50 <= avg_pop <= 150:
            health_score = 1.0
        else:
            health_score = max(0.0, 1.0 - abs(avg_pop - 100) / 100)
        
        # Weighted total
        total = (
            pressure_score * 0.4 +
            variance_score * 0.3 +
            survival_score * 0.2 +
            health_score * 0.1
        )
        
        return {
            'selection_pressure': pressure_score,
            'dynamics': variance_score,
            'survival': survival_score,
            'health': health_score,
            'total': total
        }
    
    def _record_experiment(self, exp_id: str, generation: int, 
                          params: Dict, outcomes: Dict, scores: Dict):
        """Record experiment in database."""
        experiment = {
            'id': exp_id,
            'generation': generation,
            'timestamp': datetime.now().isoformat(),
            'parameters': params,
            'outcomes': outcomes,
            'scores': scores
        }
        
        self.database['experiments'].append(experiment)
        self.database['metadata']['total_experiments'] = len(self.database['experiments'])
        self.database['metadata']['generations'] = max(
            self.database['metadata']['generations'],
            generation
        )
        
        if scores['total'] > self.database['metadata']['best_score']:
            self.database['metadata']['best_score'] = scores['total']
    
    def _update_best_parameters(self, generation: int):
        """Update best parameters for this generation."""
        gen_experiments = [
            exp for exp in self.database['experiments']
            if exp['generation'] == generation
        ]
        
        if gen_experiments:
            best = max(gen_experiments, key=lambda x: x['scores']['total'])
            self.database['best_parameters'][f'generation_{generation}'] = {
                'parameters': best['parameters'],
                'score': best['scores']['total'],
                'id': best['id']
            }
    
    def _print_final_summary(self):
        """Print final summary of all generations."""
        print(f"\n{'='*70}")
        print(f"SEARCH COMPLETE")
        print(f"{'='*70}")
        print(f"Total experiments: {self.database['metadata']['total_experiments']}")
        print(f"Generations: {self.database['metadata']['generations']}")
        print(f"Best score achieved: {self.database['metadata']['best_score']:.3f}")
        print(f"{'='*70}\n")
    
    def _visualize_results(self):
        """Create comprehensive visualization of search results."""
        
        experiments = self.database['experiments']
        if not experiments:
            print("WARNING: No experiments to visualize")
            return
        
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        fig.suptitle('Adaptive Parameter Discovery Results', fontsize=16, fontweight='bold')
        
        # 1. Fitness over generations
        ax1 = axes[0, 0]
        generations = {}
        for exp in experiments:
            gen = exp['generation']
            if gen not in generations:
                generations[gen] = []
            generations[gen].append(exp['scores']['total'])
        
        gen_nums = sorted(generations.keys())
        means = [np.mean(generations[g]) for g in gen_nums]
        maxs = [np.max(generations[g]) for g in gen_nums]
        mins = [np.min(generations[g]) for g in gen_nums]
        
        ax1.plot(gen_nums, means, 'o-', label='Mean Fitness', linewidth=2, markersize=8)
        ax1.plot(gen_nums, maxs, 's-', label='Best Fitness', linewidth=2, markersize=8)
        ax1.fill_between(gen_nums, mins, maxs, alpha=0.2)
        ax1.set_xlabel('Generation', fontsize=12)
        ax1.set_ylabel('Fitness Score', fontsize=12)
        ax1.set_title('Learning Progress', fontsize=13, fontweight='bold')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        ax1.set_ylim(0, 1)
        
        # 2. Parameter space (metabolism vs consumption_rate)
        ax2 = axes[0, 1]
        x = [e['parameters']['metabolism'] for e in experiments]
        y = [e['parameters']['consumption_rate'] for e in experiments]
        c = [e['scores']['total'] for e in experiments]
        
        scatter = ax2.scatter(x, y, c=c, cmap='viridis', s=100, alpha=0.6, edgecolors='black', linewidth=0.5)
        ax2.set_xlabel('Metabolism', fontsize=12)
        ax2.set_ylabel('Consumption Rate', fontsize=12)
        ax2.set_title('Parameter Space Exploration', fontsize=13, fontweight='bold')
        cbar = plt.colorbar(scatter, ax=ax2, label='Fitness')
        
        # 3. Death rate distribution
        ax3 = axes[1, 0]
        death_rates = [e['outcomes']['death_rate'] for e in experiments]
        
        ax3.hist(death_rates, bins=20, alpha=0.7, edgecolor='black', color='steelblue')
        ax3.axvline(0.6, color='red', linestyle='--', linewidth=2, label='Ideal (60%)')
        ax3.axvline(0.4, color='orange', linestyle='--', alpha=0.7, linewidth=1.5)
        ax3.axvline(0.8, color='orange', linestyle='--', alpha=0.7, linewidth=1.5)
        ax3.set_xlabel('Death Rate', fontsize=12)
        ax3.set_ylabel('Count', fontsize=12)
        ax3.set_title('Selection Pressure Distribution', fontsize=13, fontweight='bold')
        ax3.legend()
        ax3.grid(True, alpha=0.3, axis='y')
        
        # 4. Score components for best world
        ax4 = axes[1, 1]
        best_exp = max(experiments, key=lambda x: x['scores']['total'])
        scores = best_exp['scores']
        
        components = ['Selection\nPressure', 'Dynamics', 'Survival', 'Health']
        values = [scores['selection_pressure'], scores['dynamics'], scores['survival'], scores['health']]
        colors = ['#ff6b6b', '#4ecdc4', '#45b7d1', '#96ceb4']
        
        bars = ax4.barh(components, values, color=colors, alpha=0.8, edgecolor='black', linewidth=1.5)
        ax4.set_xlim(0, 1)
        ax4.set_xlabel('Score', fontsize=12)
        ax4.set_title(f'Best World Score Breakdown\n(Total: {scores["total"]:.3f})', 
                     fontsize=13, fontweight='bold')
        ax4.grid(True, alpha=0.3, axis='x')
        
        # Add value labels on bars
        for bar, value in zip(bars, values):
            width = bar.get_width()
            ax4.text(width + 0.02, bar.get_y() + bar.get_height()/2, 
                    f'{value:.2f}', ha='left', va='center', fontweight='bold')
        
        plt.tight_layout()
        
        viz_path = self.output_dir / 'parameter_exploration.png'
        plt.savefig(viz_path, dpi=150, bbox_inches='tight')
        print(f"\nVisualization saved: {viz_path}")
        plt.close()
    
    def _print_recommendations(self):
        """Print recommended parameters for meta-evolution."""
        
        best_exp = max(
            self.database['experiments'],
            key=lambda x: x['scores']['total']
        )
        
        print(f"\n{'='*70}")
        print(f"RECOMMENDED PARAMETERS FOR META-EVOLUTION")
        print(f"{'='*70}")
        print(f"Based on {self.database['metadata']['total_experiments']} experiments "
              f"across {self.database['metadata']['generations']} generations\n")
        
        print(f"Best World (ID: {best_exp['id']}, Score: {best_exp['scores']['total']:.3f}):")
        print(f"  metabolism: {best_exp['parameters']['metabolism']:.3f}")
        print(f"  consumption_rate: {best_exp['parameters']['consumption_rate']:.2f}")
        print(f"  reproduction_threshold: {best_exp['parameters']['reproduction_threshold']:.1f}")
        print(f"  reproduction_cost: {best_exp['parameters']['reproduction_cost']:.1f}")
        
        print(f"\nOutcome Metrics:")
        print(f"  Death rate: {best_exp['outcomes']['death_rate']:.1%} ", end='')
        if 0.4 <= best_exp['outcomes']['death_rate'] <= 0.8:
            print("[IDEAL RANGE]")
        else:
            print("[Outside ideal range]")
        
        print(f"  Final population: {best_exp['outcomes']['final_population']}")
        print(f"  Total births: {best_exp['outcomes']['total_births']}")
        print(f"  Total deaths: {best_exp['outcomes']['total_deaths']}")
        print(f"  Avg population: {best_exp['outcomes']['avg_population']:.1f}")
        
        print(f"\nScore Breakdown:")
        print(f"  Selection Pressure: {best_exp['scores']['selection_pressure']:.2f}")
        print(f"  Dynamics: {best_exp['scores']['dynamics']:.2f}")
        print(f"  Survival: {best_exp['scores']['survival']:.2f}")
        print(f"  Health: {best_exp['scores']['health']:.2f}")
        
        print(f"{'='*70}\n")


if __name__ == '__main__':
    # Test run
    searcher = ParameterSearcher()
    searcher.run_search(generations=3, worlds_per_gen=20)
