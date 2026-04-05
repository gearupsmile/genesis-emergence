"""
Phase 6 Deep Probe Analyzer

Data loader and processor for 200k-generation experiment results.
Extracts and aligns time-series data across checkpoints for analysis.
"""

import pickle
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import numpy as np


class DeepProbeAnalyzer:
    """
    Loads and processes Deep Probe experiment data.
    
    Handles:
    - Loading checkpoints from run directory
    - Extracting time-series data
    - Aligning metrics across checkpoints
    - Graceful handling of missing/corrupted data
    """
    
    def __init__(self, run_dir: str):
        """
        Initialize analyzer with run directory.
        
        Args:
            run_dir: Path to run directory containing checkpoints/
        """
        self.run_dir = Path(run_dir)
        self.checkpoints_dir = self.run_dir / "checkpoints"
        
        self.gac_data = []
        self.epc_data = []
        self.nnd_data = []
        self.metadata = {}
        
    def load_all_checkpoints(self) -> Dict:
        """
        Load all checkpoints from run directory.
        
        Returns:
            Dict with checkpoint data indexed by generation
        """
        if not self.checkpoints_dir.exists():
            raise FileNotFoundError(f"Checkpoints directory not found: {self.checkpoints_dir}")
        
        checkpoints = {}
        checkpoint_files = sorted(self.checkpoints_dir.glob("checkpoint_*.pkl"))
        
        print(f"Found {len(checkpoint_files)} checkpoint files")
        
        for checkpoint_file in checkpoint_files:
            try:
                with open(checkpoint_file, 'rb') as f:
                    data = pickle.load(f)
                    generation = data['generation']
                    checkpoints[generation] = data
                    print(f"  Loaded: {checkpoint_file.name} (gen {generation})")
            except Exception as e:
                print(f"  [WARNING] Failed to load {checkpoint_file.name}: {e}")
                continue
        
        return checkpoints
    
    def extract_time_series(self, checkpoints: Dict) -> Tuple[List, List, List]:
        """
        Extract aligned time-series data from checkpoints.
        
        Args:
            checkpoints: Dict of checkpoint data by generation
            
        Returns:
            Tuple of (gac_data, epc_data, nnd_data) lists
        """
        # Collect all data points
        gac_points = []
        epc_points = []
        nnd_points = []
        
        for gen in sorted(checkpoints.keys()):
            checkpoint = checkpoints[gen]
            
            # Extract GAC history
            if 'gac_history' in checkpoint:
                for entry in checkpoint['gac_history']:
                    gac_points.append({
                        'generation': entry['generation'],
                        'genome_mean': entry['genome_length']['mean'],
                        'genome_median': entry['genome_length']['median'],
                        'genome_var': entry['genome_length']['variance'],
                        'linkage_mean': entry['linkage_groups']['mean']
                    })
            
            # Extract EPC history
            if 'epc_history' in checkpoint:
                for entry in checkpoint['epc_history']:
                    epc_points.append({
                        'generation': entry['generation'],
                        'lz_mean': entry['lz_complexity']['mean'],
                        'lz_p90': entry['lz_complexity']['p90'],
                        'diversity_mean': entry['instruction_diversity']['mean'],
                        'diversity_p90': entry['instruction_diversity']['p90']
                    })
            
            # Extract NND history
            if 'nnd_history' in checkpoint:
                for entry in checkpoint['nnd_history']:
                    nnd_points.append({
                        'generation': entry['generation'],
                        'mean_nnd': entry['mean_nnd'],
                        'max_nnd': entry['max_nnd'],
                        'min_nnd': entry['min_nnd'],
                        'front_size': entry['front_size']
                    })
        
        # Remove duplicates and sort
        gac_data = self._deduplicate_and_sort(gac_points)
        epc_data = self._deduplicate_and_sort(epc_points)
        nnd_data = self._deduplicate_and_sort(nnd_points)
        
        return gac_data, epc_data, nnd_data
    
    def _deduplicate_and_sort(self, data_points: List[Dict]) -> List[Dict]:
        """Remove duplicate generations and sort by generation."""
        # Use dict to deduplicate by generation (keeps last occurrence)
        unique = {d['generation']: d for d in data_points}
        return sorted(unique.values(), key=lambda x: x['generation'])
    
    def load_and_process(self) -> Dict:
        """
        Load all data and return processed results.
        
        Returns:
            Dict with:
            - 'gac': GAC time series
            - 'epc': EPC time series
            - 'nnd': NND time series
            - 'metadata': Run metadata
        """
        print(f"Loading data from: {self.run_dir}")
        
        # Load checkpoints
        checkpoints = self.load_all_checkpoints()
        
        if not checkpoints:
            raise ValueError("No valid checkpoints found")
        
        # Extract time series
        gac_data, epc_data, nnd_data = self.extract_time_series(checkpoints)
        
        # Store in instance
        self.gac_data = gac_data
        self.epc_data = epc_data
        self.nnd_data = nnd_data
        
        # Extract metadata from latest checkpoint
        latest_gen = max(checkpoints.keys())
        latest = checkpoints[latest_gen]
        self.metadata = {
            'total_generations': latest_gen,
            'final_population': latest.get('population_size', 0),
            'num_checkpoints': len(checkpoints),
            'gac_points': len(gac_data),
            'epc_points': len(epc_data),
            'nnd_points': len(nnd_data)
        }
        
        print(f"\nData loaded successfully:")
        print(f"  Total generations: {self.metadata['total_generations']:,}")
        print(f"  GAC data points: {self.metadata['gac_points']}")
        print(f"  EPC data points: {self.metadata['epc_points']}")
        print(f"  NND data points: {self.metadata['nnd_points']}")
        
        return {
            'gac': gac_data,
            'epc': epc_data,
            'nnd': nnd_data,
            'metadata': self.metadata
        }
    
    def get_metric_array(self, metric_type: str, field: str) -> np.ndarray:
        """
        Get numpy array for a specific metric field.
        
        Args:
            metric_type: 'gac', 'epc', or 'nnd'
            field: Field name (e.g., 'genome_mean', 'lz_mean')
            
        Returns:
            Numpy array of values
        """
        data_map = {
            'gac': self.gac_data,
            'epc': self.epc_data,
            'nnd': self.nnd_data
        }
        
        if metric_type not in data_map:
            raise ValueError(f"Unknown metric type: {metric_type}")
        
        data = data_map[metric_type]
        return np.array([d[field] for d in data if field in d])
    
    def get_generations(self, metric_type: str) -> np.ndarray:
        """Get generation numbers for a metric type."""
        data_map = {
            'gac': self.gac_data,
            'epc': self.epc_data,
            'nnd': self.nnd_data
        }
        
        data = data_map[metric_type]
        return np.array([d['generation'] for d in data])
    
    def compare_runs(self, other_run_dir: str) -> Dict:
        """
        Compare this run with another run.
        
        Args:
            other_run_dir: Path to other run directory
            
        Returns:
            Dict with comparison metrics
        """
        other = DeepProbeAnalyzer(other_run_dir)
        other.load_and_process()
        
        comparison = {
            'run1': {
                'dir': str(self.run_dir),
                'total_gens': self.metadata['total_generations'],
                'final_gac': self.gac_data[-1]['genome_mean'] if self.gac_data else 0,
                'final_epc': self.epc_data[-1]['lz_mean'] if self.epc_data else 0
            },
            'run2': {
                'dir': str(other.run_dir),
                'total_gens': other.metadata['total_generations'],
                'final_gac': other.gac_data[-1]['genome_mean'] if other.gac_data else 0,
                'final_epc': other.epc_data[-1]['lz_mean'] if other.epc_data else 0
            }
        }
        
        return comparison


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python phase6_analyzer.py <run_directory>")
        sys.exit(1)
    
    analyzer = DeepProbeAnalyzer(sys.argv[1])
    data = analyzer.load_and_process()
    
    print("\nSummary:")
    print(f"  GAC range: {data['gac'][0]['genome_mean']:.1f} -> {data['gac'][-1]['genome_mean']:.1f}")
    print(f"  EPC range: {data['epc'][0]['lz_mean']:.3f} -> {data['epc'][-1]['lz_mean']:.3f}")
    print(f"  NND range: {data['nnd'][0]['mean_nnd']:.3f} -> {data['nnd'][-1]['mean_nnd']:.3f}")
