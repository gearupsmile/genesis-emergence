"""
Comprehensive stability and validation tests for Gray-Scott system.

This module tests numerical stability, pattern formation, and long-term
behavior for all parameter presets.
"""

import numpy as np
import sys
import time
from pathlib import Path
from typing import Dict, List, Tuple
import argparse

from physics_engine import GrayScottEngine
from parameters import GrayScottParams, get_preset, get_initial_conditions, PRESETS


class StabilityTester:
    """Test suite for Gray-Scott system stability."""
    
    def __init__(self, verbose: bool = True):
        self.verbose = verbose
        self.results: Dict[str, Dict] = {}
        
    def log(self, message: str) -> None:
        """Print message if verbose mode is enabled."""
        if self.verbose:
            print(message)
    
    def test_numerical_stability(
        self,
        preset_name: str,
        num_cycles: int = 10000,
        grid_size: Tuple[int, int] = (256, 256)
    ) -> Dict:
        """Test numerical stability for a parameter preset.
        
        Args:
            preset_name: Name of the parameter preset
            num_cycles: Number of cycles to run
            grid_size: Grid size for simulation
            
        Returns:
            Dictionary with test results
        """
        self.log(f"\n{'='*60}")
        self.log(f"Testing: {preset_name}")
        self.log(f"{'='*60}")
        
        # Get parameters
        params = get_preset(preset_name)
        
        # Create engine
        engine = GrayScottEngine(params, grid_size, enable_checks=True)
        
        # Initialize
        U, V = get_initial_conditions(grid_size, 'random')
        engine.set_initial_conditions(U, V)
        
        # Track statistics
        start_time = time.time()
        stats_history = []
        check_interval = 100
        
        # Run simulation
        for i in range(num_cycles):
            success = engine.step()
            
            if not success:
                elapsed = time.time() - start_time
                return {
                    'success': False,
                    'failed_at_cycle': engine.cycle_count,
                    'elapsed_seconds': elapsed,
                    'error': 'Numerical instability detected'
                }
            
            # Record statistics periodically
            if engine.cycle_count % check_interval == 0:
                stats = engine.get_statistics()
                stats_history.append(stats)
                
                if self.verbose and engine.cycle_count % 1000 == 0:
                    self.log(
                        f"  Cycle {engine.cycle_count:5d} | "
                        f"V: [{stats['V_min']:.3f}, {stats['V_max']:.3f}] "
                        f"mean={stats['V_mean']:.3f} std={stats['V_std']:.3f} | "
                        f"Mass error: {stats['mass_conservation_error']:.6f}"
                    )
        
        elapsed = time.time() - start_time
        final_stats = engine.get_statistics()
        
        # Analyze results
        result = {
            'success': True,
            'preset': preset_name,
            'cycles_completed': num_cycles,
            'elapsed_seconds': elapsed,
            'cycles_per_second': num_cycles / elapsed,
            'final_stats': final_stats,
            'stability_warnings': engine.stability_warnings,
            'stats_history': stats_history
        }
        
        # Check for issues
        if final_stats['mass_conservation_error'] > 0.1:
            result['warnings'] = ['High mass conservation error']
        
        if final_stats['V_std'] < 0.01:
            result['warnings'] = result.get('warnings', []) + ['Pattern appears uniform']
        
        self.log(f"\n[OK] Completed {num_cycles} cycles in {elapsed:.1f}s ({result['cycles_per_second']:.1f} cycles/s)")
        self.log(f"  Final V std: {final_stats['V_std']:.3f}")
        self.log(f"  Mass conservation error: {final_stats['mass_conservation_error']:.6f}")
        self.log(f"  Stability warnings: {engine.stability_warnings}")
        
        return result
    
    def test_all_presets(
        self,
        num_cycles: int = 10000,
        grid_size: Tuple[int, int] = (256, 256)
    ) -> Dict[str, Dict]:
        """Test all parameter presets.
        
        Args:
            num_cycles: Number of cycles to run for each preset
            grid_size: Grid size for simulations
            
        Returns:
            Dictionary mapping preset names to test results
        """
        self.log(f"\n{'#'*60}")
        self.log(f"# TESTING ALL PRESETS ({num_cycles} cycles each)")
        self.log(f"# Grid size: {grid_size}")
        self.log(f"{'#'*60}")
        
        results = {}
        
        for preset_name in PRESETS.keys():
            try:
                result = self.test_numerical_stability(
                    preset_name,
                    num_cycles=num_cycles,
                    grid_size=grid_size
                )
                results[preset_name] = result
            except Exception as e:
                self.log(f"\n[FAIL] FAILED: {preset_name}")
                self.log(f"  Error: {str(e)}")
                results[preset_name] = {
                    'success': False,
                    'error': str(e)
                }
        
        # Summary
        self.log(f"\n{'='*60}")
        self.log("SUMMARY")
        self.log(f"{'='*60}")
        
        passed = sum(1 for r in results.values() if r.get('success', False))
        total = len(results)
        
        self.log(f"Passed: {passed}/{total}")
        
        for preset_name, result in results.items():
            status = "[PASS]" if result.get('success', False) else "[FAIL]"
            self.log(f"  {status} - {preset_name}")
            
            if result.get('success', False):
                stats = result['final_stats']
                self.log(f"        V std: {stats['V_std']:.3f}, Mass error: {stats['mass_conservation_error']:.6f}")
        
        self.log(f"{'='*60}\n")
        
        return results
    
    def test_mass_conservation(
        self,
        preset_name: str = 'spots',
        num_cycles: int = 5000,
        tolerance: float = 0.01
    ) -> bool:
        """Test mass conservation over long run.
        
        Args:
            preset_name: Parameter preset to test
            num_cycles: Number of cycles to run
            tolerance: Maximum allowed relative error
            
        Returns:
            True if mass is conserved within tolerance
        """
        self.log(f"\nTesting mass conservation for {preset_name}...")
        
        params = get_preset(preset_name)
        engine = GrayScottEngine(params, (128, 128))
        
        U, V = get_initial_conditions((128, 128), 'random')
        engine.set_initial_conditions(U, V)
        
        initial_mass = np.sum(U) + np.sum(V)
        
        for _ in range(num_cycles):
            engine.step()
        
        final_mass = np.sum(engine.U) + np.sum(engine.V)
        error = abs(final_mass - initial_mass) / initial_mass
        
        passed = error < tolerance
        status = "[PASS]" if passed else "[FAIL]"
        
        self.log(f"  {status} - Mass error: {error:.6f} (tolerance: {tolerance})")
        
        return passed
    
    def test_grid_size_independence(
        self,
        preset_name: str = 'spots',
        num_cycles: int = 1000
    ) -> bool:
        """Test that patterns form consistently across different grid sizes.
        
        Args:
            preset_name: Parameter preset to test
            num_cycles: Number of cycles to run
            
        Returns:
            True if patterns are consistent
        """
        self.log(f"\nTesting grid size independence for {preset_name}...")
        
        params = get_preset(preset_name)
        grid_sizes = [(64, 64), (128, 128), (256, 256)]
        
        v_stds = []
        
        for size in grid_sizes:
            engine = GrayScottEngine(params, size)
            U, V = get_initial_conditions(size, 'random')
            engine.set_initial_conditions(U, V)
            
            for _ in range(num_cycles):
                engine.step()
            
            stats = engine.get_statistics()
            v_stds.append(stats['V_std'])
            
            self.log(f"  Grid {size[0]}x{size[1]}: V std = {stats['V_std']:.3f}")
        
        # Check if standard deviations are similar (within 50% of each other)
        min_std = min(v_stds)
        max_std = max(v_stds)
        ratio = max_std / min_std if min_std > 0 else float('inf')
        
        passed = ratio < 2.0
        status = "[PASS]" if passed else "[FAIL]"
        
        self.log(f"  {status} - Std ratio: {ratio:.2f}")
        
        return passed


def main():
    """Main entry point for testing."""
    parser = argparse.ArgumentParser(description="Test Gray-Scott stability")
    
    parser.add_argument(
        '--cycles',
        type=int,
        default=10000,
        help='Number of cycles to test (default: 10000)'
    )
    
    parser.add_argument(
        '--preset',
        type=str,
        help='Test specific preset only'
    )
    
    parser.add_argument(
        '--all-presets',
        action='store_true',
        help='Test all presets'
    )
    
    parser.add_argument(
        '--grid-size',
        type=int,
        default=256,
        help='Grid size for testing (default: 256)'
    )
    
    parser.add_argument(
        '--mass-conservation',
        action='store_true',
        help='Run mass conservation test'
    )
    
    parser.add_argument(
        '--grid-independence',
        action='store_true',
        help='Run grid size independence test'
    )
    
    parser.add_argument(
        '--quick',
        action='store_true',
        help='Quick test mode (1000 cycles)'
    )
    
    args = parser.parse_args()
    
    if args.quick:
        args.cycles = 1000
    
    tester = StabilityTester(verbose=True)
    
    # Run requested tests
    all_passed = True
    
    if args.all_presets:
        results = tester.test_all_presets(
            num_cycles=args.cycles,
            grid_size=(args.grid_size, args.grid_size)
        )
        all_passed = all(r.get('success', False) for r in results.values())
    
    elif args.preset:
        result = tester.test_numerical_stability(
            args.preset,
            num_cycles=args.cycles,
            grid_size=(args.grid_size, args.grid_size)
        )
        all_passed = result.get('success', False)
    
    if args.mass_conservation:
        preset = args.preset or 'spots'
        passed = tester.test_mass_conservation(preset, num_cycles=args.cycles)
        all_passed = all_passed and passed
    
    if args.grid_independence:
        preset = args.preset or 'spots'
        passed = tester.test_grid_size_independence(preset, num_cycles=min(args.cycles, 1000))
        all_passed = all_passed and passed
    
    # If no specific test was requested, run default test
    if not (args.all_presets or args.preset or args.mass_conservation or args.grid_independence):
        print("No test specified. Use --help for options.")
        print("\nQuick test: python test_stability.py --quick --all-presets")
        return 1
    
    return 0 if all_passed else 1


if __name__ == '__main__':
    sys.exit(main())
