"""
Resource Profiler for Genesis Engine Experiments

Tracks memory usage and identifies potential resource leaks.
Uses built-in tracemalloc instead of psutil for portability.
"""

import tracemalloc
import time
from typing import List, Dict
from pathlib import Path


class ResourceProfiler:
    """
    Monitors system resources during experiment execution.
    
    Tracks:
    - Memory usage (current, peak)
    - Memory growth trend
    """
    
    def __init__(self, log_file: str = None):
        """
        Initialize resource profiler.
        
        Args:
            log_file: Path to write resource log
        """
        self.log_file = log_file
        
        # Start memory tracking
        tracemalloc.start()
        
        self.memory_samples = []  # List of (generation, memory_mb)
        
        self.start_time = time.time()
        self.start_memory = self.get_memory_mb()
        
    def get_memory_mb(self) -> float:
        """Get current memory usage in MB."""
        current, peak = tracemalloc.get_traced_memory()
        return current / (1024 ** 2)
    
    def get_peak_memory_mb(self) -> float:
        """Get peak memory usage in MB."""
        current, peak = tracemalloc.get_traced_memory()
        return peak / (1024 ** 2)
    
    def log_resources(self, generation: int):
        """
        Log current resource usage.
        
        Args:
            generation: Current generation number
        """
        memory_mb = self.get_memory_mb()
        self.memory_samples.append((generation, memory_mb))
        
        # Simple warning based on growth
        if len(self.memory_samples) > 10:
            recent_growth = memory_mb - self.memory_samples[-10][1]
            if recent_growth > 100:  # >100MB growth in last 10 samples
                warning = f"[WARNING] Rapid memory growth: +{recent_growth:.1f} MB in last interval"
                print(f"\n{warning}")
                if self.log_file:
                    with open(self.log_file, 'a') as f:
                        f.write(f"{warning}\n")
    
    def calculate_memory_trend(self) -> Dict:
        """
        Calculate memory growth trend.
        
        Returns:
            Dict with trend analysis
        """
        if len(self.memory_samples) < 2:
            return {'trend': 'insufficient_data', 'growth_percent': 0}
        
        # Calculate linear regression slope
        generations = [g for g, _ in self.memory_samples]
        memories = [m for _, m in self.memory_samples]
        
        n = len(generations)
        sum_x = sum(generations)
        sum_y = sum(memories)
        sum_xy = sum(g * m for g, m in zip(generations, memories))
        sum_x2 = sum(g * g for g in generations)
        
        # Slope (MB per generation)
        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
        
        # Total growth
        initial_memory = memories[0]
        final_memory = memories[-1]
        growth_pct = ((final_memory - initial_memory) / initial_memory * 100) if initial_memory > 0 else 0
        
        # Classify trend
        if abs(slope) < 0.001:  # < 1KB per generation
            trend = 'flat'
        elif slope < 0.01:  # < 10KB per generation
            trend = 'slow_creep'
        else:
            trend = 'rapid_increase'
        
        return {
            'trend': trend,
            'slope_mb_per_gen': slope,
            'growth_percent': growth_pct,
            'initial_mb': initial_memory,
            'final_mb': final_memory
        }
    
    def generate_report(self) -> str:
        """
        Generate resource profiling report.
        
        Returns:
            Report text
        """
        if not self.memory_samples:
            return "No resource data collected"
        
        # Calculate statistics
        memories = [m for _, m in self.memory_samples]
        
        peak_memory = self.get_peak_memory_mb()
        current_memory = memories[-1]
        avg_memory = sum(memories) / len(memories)
        
        trend_analysis = self.calculate_memory_trend()
        
        runtime = time.time() - self.start_time
        
        # Build report
        report = []
        report.append("=" * 70)
        report.append("RESOURCE PROFILING REPORT")
        report.append("=" * 70)
        report.append("")
        
        report.append("MEMORY USAGE:")
        report.append(f"  Initial: {self.start_memory:.1f} MB")
        report.append(f"  Current: {current_memory:.1f} MB")
        report.append(f"  Peak: {peak_memory:.1f} MB")
        report.append(f"  Average: {avg_memory:.1f} MB")
        report.append(f"  Growth: {trend_analysis['growth_percent']:.1f}%")
        report.append(f"  Trend: {trend_analysis['trend'].upper()}")
        report.append(f"  Slope: {trend_analysis['slope_mb_per_gen']:.4f} MB/gen")
        report.append("")
        
        report.append("RUNTIME:")
        report.append(f"  Total: {runtime:.1f} seconds ({runtime/60:.1f} minutes)")
        report.append("")
        
        # Recommendation
        report.append("=" * 70)
        report.append("RECOMMENDATION")
        report.append("=" * 70)
        report.append("")
        
        if trend_analysis['trend'] == 'flat' and peak_memory < 500:
            report.append("DECISION: **PROCEED_TO_200K**")
            report.append("  System is stable. Memory usage is flat and reasonable.")
            report.append("  Safe to run full 200,000-generation experiment.")
        elif trend_analysis['growth_percent'] > 50:
            report.append("DECISION: **DEBUG_AND_OPTIMIZE**")
            report.append(f"  Memory grew {trend_analysis['growth_percent']:.1f}% during run.")
            report.append("  Potential memory leak detected. Recommend:")
            report.append("  1. Review code for memory leaks")
            report.append("  2. Reduce population to 50")
            report.append("  3. Re-run diagnostic")
        elif peak_memory > 1000:
            report.append("DECISION: **REDUCE_SCALE**")
            report.append(f"  Peak memory usage ({peak_memory:.1f} MB) is high.")
            report.append("  System may be overloaded. Recommend:")
            report.append("  1. Reduce population to 50-75")
            report.append("  2. Run overnight with reduced scale")
        else:
            report.append("DECISION: **PROCEED_WITH_CAUTION**")
            report.append("  System is functional but monitor closely during 200k run.")
            report.append(f"  Memory trend: {trend_analysis['trend']}, Growth: {trend_analysis['growth_percent']:.1f}%")
        
        report.append("")
        
        return "\n".join(report)
    
    def save_report(self):
        """Save report to log file."""
        if not self.log_file:
            return
        
        report = self.generate_report()
        
        with open(self.log_file, 'w') as f:
            f.write(report)
            f.write("\n\nDETAILED SAMPLES:\n")
            f.write("Generation,Memory_MB\n")
            for gen, mem in self.memory_samples:
                f.write(f"{gen},{mem:.2f}\n")
    
    def cleanup(self):
        """Stop memory tracking."""
        tracemalloc.stop()
