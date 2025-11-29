"""
Simulation runner for Gray-Scott reaction-diffusion system.

This module provides the main simulation loop with checkpoint system,
progress logging, and data export functionality.
"""

import numpy as np
import json
import time
from pathlib import Path
from typing import Optional, Dict, List
from datetime import datetime
import argparse

from physics_engine import GrayScottEngine
from parameters import GrayScottParams, get_preset, get_initial_conditions, list_presets


class SimulationRunner:
    """Manages long-running Gray-Scott simulations with checkpoints and logging."""
    
    def __init__(
        self,
        params: GrayScottParams,
        grid_size: tuple = (256, 256),
        output_dir: str = "output",
        checkpoint_interval: int = 1000,
    ):
        """Initialize simulation runner.
        
        Args:
            params: Gray-Scott parameters
            grid_size: (height, width) of simulation grid
            output_dir: Directory for output files
            checkpoint_interval: Save checkpoint every N cycles
        """
        self.params = params
        self.grid_size = grid_size
        self.output_dir = Path(output_dir)
        self.checkpoint_interval = checkpoint_interval
        
        # Create output directory
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize physics engine
        self.engine = GrayScottEngine(params, grid_size)
        
        # Logging
        self.log_file = self.output_dir / "simulation.log"
        self.metrics_file = self.output_dir / "metrics.json"
        self.metrics_history: List[Dict] = []
        
        # Performance tracking
        self.start_time = None
        self.last_checkpoint_time = None
        
    def initialize(self, initial_pattern: str = "random") -> None:
        """Initialize simulation with initial conditions.
        
        Args:
            initial_pattern: Type of initial pattern ('random', 'center_spot', etc.)
        """
        U, V = get_initial_conditions(self.grid_size, initial_pattern)
        self.engine.set_initial_conditions(U, V)
        
        self._log(f"Initialized with pattern: {initial_pattern}")
        self._log(f"Grid size: {self.grid_size}")
        self._log(f"Parameters: F={self.params.F}, k={self.params.k}, "
                 f"Du={self.params.Du}, Dv={self.params.Dv}")
        
    def _log(self, message: str) -> None:
        """Write message to log file and print to console.
        
        Args:
            message: Message to log
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        
        print(log_entry)
        
        with open(self.log_file, 'a') as f:
            f.write(log_entry + '\n')
    
    def _save_checkpoint(self, cycle: int) -> None:
        """Save simulation checkpoint.
        
        Args:
            cycle: Current cycle number
        """
        checkpoint_file = self.output_dir / f"checkpoint_{cycle:06d}.npz"
        self.engine.save_state(str(checkpoint_file))
        self._log(f"Checkpoint saved: {checkpoint_file.name}")
    
    def _save_snapshot(self, cycle: int) -> None:
        """Save visualization snapshot.
        
        Args:
            cycle: Current cycle number
        """
        from PIL import Image
        
        # Get current state
        U, V = self.engine.get_state()
        
        # Convert V to image (V shows the pattern best)
        # Scale to 0-255 range
        V_img = (V * 255).astype(np.uint8)
        
        # Save as PNG
        snapshot_file = self.output_dir / f"snapshot_{cycle:06d}.png"
        Image.fromarray(V_img, mode='L').save(snapshot_file)
    
    def _record_metrics(self) -> None:
        """Record current simulation metrics."""
        stats = self.engine.get_statistics()
        
        # Add timing information
        if self.start_time is not None:
            elapsed = time.time() - self.start_time
            stats['elapsed_seconds'] = elapsed
            stats['cycles_per_second'] = stats['cycle'] / elapsed if elapsed > 0 else 0
        
        self.metrics_history.append(stats)
        
        # Save metrics to file
        with open(self.metrics_file, 'w') as f:
            json.dump(self.metrics_history, f, indent=2)
    
    def run(
        self,
        num_cycles: int,
        save_snapshots: bool = True,
        snapshot_interval: int = 500,
    ) -> bool:
        """Run simulation for specified number of cycles.
        
        Args:
            num_cycles: Number of cycles to run
            save_snapshots: Whether to save visual snapshots
            snapshot_interval: Save snapshot every N cycles
            
        Returns:
            True if completed successfully, False if crashed
        """
        self._log(f"Starting simulation for {num_cycles} cycles")
        self.start_time = time.time()
        self.last_checkpoint_time = self.start_time
        
        try:
            for i in range(num_cycles):
                # Run one cycle
                success = self.engine.step()
                
                if not success:
                    self._log(f"ERROR: Numerical instability at cycle {self.engine.cycle_count}")
                    self._save_checkpoint(self.engine.cycle_count)
                    return False
                
                current_cycle = self.engine.cycle_count
                
                # Periodic logging
                if current_cycle % 100 == 0:
                    stats = self.engine.get_statistics()
                    elapsed = time.time() - self.start_time
                    cps = current_cycle / elapsed if elapsed > 0 else 0
                    
                    self._log(
                        f"Cycle {current_cycle}/{num_cycles} | "
                        f"V: [{stats['V_min']:.3f}, {stats['V_max']:.3f}] "
                        f"mean={stats['V_mean']:.3f} | "
                        f"Mass error: {stats['mass_conservation_error']:.6f} | "
                        f"{cps:.1f} cycles/sec"
                    )
                
                # Save checkpoint
                if current_cycle % self.checkpoint_interval == 0:
                    self._save_checkpoint(current_cycle)
                    self._record_metrics()
                
                # Save snapshot
                if save_snapshots and current_cycle % snapshot_interval == 0:
                    self._save_snapshot(current_cycle)
            
            # Final checkpoint and metrics
            self._save_checkpoint(self.engine.cycle_count)
            self._record_metrics()
            
            if save_snapshots:
                self._save_snapshot(self.engine.cycle_count)
            
            elapsed = time.time() - self.start_time
            self._log(f"Simulation completed successfully in {elapsed:.1f} seconds")
            self._log(f"Average: {num_cycles / elapsed:.1f} cycles/second")
            
            return True
            
        except Exception as e:
            self._log(f"ERROR: Simulation crashed: {str(e)}")
            import traceback
            self._log(traceback.format_exc())
            
            # Try to save emergency checkpoint
            try:
                self._save_checkpoint(self.engine.cycle_count)
            except:
                pass
            
            return False
    
    def get_final_statistics(self) -> Dict:
        """Get final simulation statistics.
        
        Returns:
            Dictionary with final statistics
        """
        stats = self.engine.get_statistics()
        
        if self.start_time is not None:
            elapsed = time.time() - self.start_time
            stats['total_elapsed_seconds'] = elapsed
            stats['average_cycles_per_second'] = stats['cycle'] / elapsed if elapsed > 0 else 0
        
        return stats


def main():
    """Main entry point for command-line usage."""
    parser = argparse.ArgumentParser(
        description="Run Gray-Scott reaction-diffusion simulation"
    )
    
    parser.add_argument(
        '--preset',
        type=str,
        default='spots',
        help=f"Parameter preset to use. Available: {', '.join(list_presets().keys())}"
    )
    
    parser.add_argument(
        '--cycles',
        type=int,
        default=10000,
        help="Number of cycles to run (default: 10000)"
    )
    
    parser.add_argument(
        '--grid-size',
        type=int,
        default=256,
        help="Grid size (creates square grid, default: 256)"
    )
    
    parser.add_argument(
        '--output-dir',
        type=str,
        default='output',
        help="Output directory (default: output)"
    )
    
    parser.add_argument(
        '--initial-pattern',
        type=str,
        default='random',
        choices=['random', 'center_spot', 'multiple_spots'],
        help="Initial pattern type (default: random)"
    )
    
    parser.add_argument(
        '--checkpoint-interval',
        type=int,
        default=1000,
        help="Checkpoint interval in cycles (default: 1000)"
    )
    
    parser.add_argument(
        '--snapshot-interval',
        type=int,
        default=500,
        help="Snapshot interval in cycles (default: 500)"
    )
    
    parser.add_argument(
        '--no-snapshots',
        action='store_true',
        help="Disable snapshot saving"
    )
    
    args = parser.parse_args()
    
    # Get parameters
    try:
        params = get_preset(args.preset)
    except KeyError as e:
        print(f"Error: {e}")
        return 1
    
    # Create runner
    runner = SimulationRunner(
        params=params,
        grid_size=(args.grid_size, args.grid_size),
        output_dir=args.output_dir,
        checkpoint_interval=args.checkpoint_interval,
    )
    
    # Initialize
    runner.initialize(initial_pattern=args.initial_pattern)
    
    # Run simulation
    success = runner.run(
        num_cycles=args.cycles,
        save_snapshots=not args.no_snapshots,
        snapshot_interval=args.snapshot_interval,
    )
    
    # Print final statistics
    if success:
        print("\n" + "="*60)
        print("FINAL STATISTICS")
        print("="*60)
        stats = runner.get_final_statistics()
        for key, value in stats.items():
            print(f"{key}: {value}")
        print("="*60)
        return 0
    else:
        print("\nSimulation failed!")
        return 1


if __name__ == '__main__':
    exit(main())
