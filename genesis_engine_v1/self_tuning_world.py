"""
Self-tuning world that maintains edge of chaos (50-70% death rate).

Tunes agent baseline parameters (metabolism/consumption) to maintain
continuous evolutionary pressure without extinction.

Design Philosophy:
- Tune biology (agent baselines), not chemistry (Gray-Scott F/k)
- Preserve pattern beauty while controlling survival difficulty
- Simple proportional control (no PID, no ML)
- Safety mechanisms to prevent extinction
"""

import numpy as np
from pathlib import Path
import json


class SelfTuningWorld:
    """World that maintains edge of chaos through baseline parameter tuning."""
    
    # Target death rate range (edge of chaos)
    TARGET_DEATH_RATE_MIN = 0.50  # 50%
    TARGET_DEATH_RATE_MAX = 0.70  # 70%
    
    # Tuning parameters (INCREASED for faster response)
    TUNING_INTERVAL = 100  # Adjust every 100 cycles
    ADJUSTMENT_STRENGTH = 0.05  # 5% change per adjustment (was 1%)
    
    # Safety thresholds
    EXTINCTION_THRESHOLD = 10  # Emergency if population < 10
    EMERGENCY_ADJUSTMENT = 0.10  # 10% emergency change (was 5%)
    
    def __init__(self, population, output_dir=None):
        """Initialize self-tuning world.
        
        Args:
            population: Population object to monitor
            output_dir: Directory to save tuning history
        """
        self.population = population
        self.output_dir = Path(output_dir) if output_dir else None
        
        # Import Agent class to access baselines
        from src.agents.base_agent import Agent
        self.Agent = Agent
        
        # Track initial baselines
        self.initial_metabolism = Agent.WORLD_METABOLISM
        self.initial_consumption = Agent.WORLD_CONSUMPTION_RATE
        
        # Tuning history
        self.tuning_history = []
        
        # Tracking for death rate calculation
        self.last_deaths = 0
        self.last_births = 0
        self.last_death_rate = 0.5  # Assume 50% initially
        
        # Current cycle
        self.current_cycle = 0
        
        # Progressive adjustment tracking
        self.consecutive_low = 0  # Count of consecutive below-target readings
        self.consecutive_high = 0  # Count of consecutive above-target readings
        
        print(f"\n{'='*70}")
        print("SELF-TUNING WORLD INITIALIZED (ENHANCED)")
        print(f"{'='*70}")
        print(f"Target death rate: {self.TARGET_DEATH_RATE_MIN:.0%}-{self.TARGET_DEATH_RATE_MAX:.0%}")
        print(f"Initial metabolism: {self.initial_metabolism:.3f}")
        print(f"Initial consumption: {self.initial_consumption:.3f}")
        print(f"Tuning interval: {self.TUNING_INTERVAL} cycles")
        print(f"Base adjustment strength: {self.ADJUSTMENT_STRENGTH:.1%}")
        print(f"Progressive adjustment: ENABLED (increases with consecutive misses)")
        print(f"{'='*70}\n")
    
    def should_tune(self, cycle):
        """Check if it's time to tune parameters."""
        return cycle % self.TUNING_INTERVAL == 0 and cycle > 0
    
    def calculate_death_rate(self):
        """Calculate death rate over last tuning interval.
        
        Returns:
            Death rate as fraction (0.0 to 1.0)
        """
        stats = self.population.get_statistics()
        current_deaths = stats['total_deaths']
        current_births = stats['total_births']
        
        # Calculate deaths and births in this interval
        recent_deaths = current_deaths - self.last_deaths
        recent_births = current_births - self.last_births
        
        # Update tracking
        self.last_deaths = current_deaths
        self.last_births = current_births
        
        # Handle edge cases
        if recent_births == 0:
            # No births this interval
            if stats['population'] == 0:
                # Population extinct
                return 1.0  # 100% death rate
            else:
                # Population stable, no reproduction
                return self.last_death_rate  # Use last known rate
        
        # Calculate death rate
        death_rate = recent_deaths / recent_births
        
        # Clamp to [0, 1] range
        death_rate = np.clip(death_rate, 0.0, 1.0)
        
        # Update last known rate
        self.last_death_rate = death_rate
        
        return death_rate
    
    def tune_parameters(self, death_rate):
        """Adjust world baseline parameters to maintain edge of chaos.
        
        ENHANCED with:
        - Progressive adjustment (increases with consecutive misses)
        - Gene compensation tracking
        - AMPLIFIED ADJUSTMENTS (combat evolutionary arms race)
        - Comprehensive debug output
        
        Logic:
        - Death rate < 50% (too easy) → make HARDER
          - Increase metabolism (higher energy cost)
          - Decrease consumption (lower energy gain)
          - AMPLIFY if agents are compensating via gene evolution
        - Death rate > 70% (too hard) → make EASIER
          - Decrease metabolism (lower energy cost)
          - Increase consumption (higher energy gain)
        
        Args:
            death_rate: Current death rate (0.0 to 1.0)
        
        Returns:
            Action taken ('HARDER', 'EASIER', 'STABLE', 'EMERGENCY')
        """
        current_metabolism = self.Agent.WORLD_METABOLISM
        current_consumption = self.Agent.WORLD_CONSUMPTION_RATE
        
        # Calculate average gene multipliers to detect compensation
        genome_stats = self.population.get_genome_statistics()
        avg_metab_mult = genome_stats.get('metabolism_multiplier', {}).get('mean', 1.0) if genome_stats else 1.0
        avg_cons_mult = genome_stats.get('consumption_multiplier', {}).get('mean', 1.0) if genome_stats else 1.0
        
        # Calculate effective parameters (world × genes)
        effective_metabolism = current_metabolism * avg_metab_mult
        effective_consumption = current_consumption * avg_cons_mult
        
        # Detect gene compensation (genes drifting away from baseline)
        metab_compensation = abs(1.0 - avg_metab_mult)  # How far from baseline (1.0)
        cons_compensation = abs(1.0 - avg_cons_mult)
        total_compensation = (metab_compensation + cons_compensation) / 2
        
        # Check for emergency (near extinction)
        if self.population.get_statistics()['population'] < self.EXTINCTION_THRESHOLD:
            # EMERGENCY: Make much easier immediately
            new_metabolism = current_metabolism * (1 - self.EMERGENCY_ADJUSTMENT)
            new_consumption = current_consumption * (1 + self.EMERGENCY_ADJUSTMENT)
            action = "EMERGENCY"
            self.consecutive_low = 0
            self.consecutive_high = 0
            amplification = 1.0
        
        elif death_rate < self.TARGET_DEATH_RATE_MIN:
            # Too easy (death rate too low) → make HARDER
            # Track consecutive low readings for progressive adjustment
            self.consecutive_low += 1
            self.consecutive_high = 0
            
            # Progressive adjustment: increase strength with consecutive misses
            # Base 5%, +2.5% per consecutive miss (max 15%)
            base_adjustment = min(self.ADJUSTMENT_STRENGTH * (1 + 0.5 * (self.consecutive_low - 1)), 0.15)
            
            # AMPLIFICATION: If agents are compensating, amplify adjustment
            # Compensation > 10% triggers amplification
            if total_compensation > 0.10:
                # Amplify by compensation factor (e.g., 20% compensation → 1.2x multiplier)
                amplification = 1.0 + (total_compensation * 2)  # 2x multiplier for strong response
                amplification = min(amplification, 2.5)  # Cap at 2.5x
            else:
                amplification = 1.0
            
            # Apply amplified adjustment
            final_adjustment = base_adjustment * amplification
            
            # Increase metabolism (higher energy cost)
            # Decrease consumption (lower energy gain)
            new_metabolism = current_metabolism * (1 + final_adjustment)
            new_consumption = current_consumption * (1 - final_adjustment)
            
            if amplification > 1.0:
                action = f"HARDER x{self.consecutive_low} AMPLIFIED {amplification:.1f}x"
            else:
                action = f"HARDER x{self.consecutive_low}"
        
        elif death_rate > self.TARGET_DEATH_RATE_MAX:
            # Too hard (death rate too high) → make EASIER
            # Track consecutive high readings
            self.consecutive_high += 1
            self.consecutive_low = 0
            
            # Progressive adjustment
            base_adjustment = min(self.ADJUSTMENT_STRENGTH * (1 + 0.5 * (self.consecutive_high - 1)), 0.15)
            
            # AMPLIFICATION for easier direction (less aggressive)
            if total_compensation > 0.10:
                amplification = 1.0 + (total_compensation * 1.5)  # 1.5x multiplier (gentler)
                amplification = min(amplification, 2.0)
            else:
                amplification = 1.0
            
            final_adjustment = base_adjustment * amplification
            
            # Decrease metabolism (lower energy cost)
            # Increase consumption (higher energy gain)
            new_metabolism = current_metabolism * (1 - final_adjustment)
            new_consumption = current_consumption * (1 + final_adjustment)
            
            if amplification > 1.0:
                action = f"EASIER x{self.consecutive_high} AMPLIFIED {amplification:.1f}x"
            else:
                action = f"EASIER x{self.consecutive_high}"
        
        else:
            # In target range → no change
            new_metabolism = current_metabolism
            new_consumption = current_consumption
            action = "STABLE"
            self.consecutive_low = 0
            self.consecutive_high = 0
            amplification = 1.0
        
        # Apply adjustments (with clamping via set_world_baselines)
        self.Agent.set_world_baselines(
            metabolism=new_metabolism,
            consumption=new_consumption
        )
        
        # Calculate new effective parameters
        new_effective_metab = new_metabolism * avg_metab_mult
        new_effective_cons = new_consumption * avg_cons_mult
        
        # Record in history with gene compensation data
        self.tuning_history.append({
            'cycle': self.current_cycle,
            'death_rate': float(death_rate),
            'metabolism': float(new_metabolism),
            'consumption': float(new_consumption),
            'avg_metab_multiplier': float(avg_metab_mult),
            'avg_cons_multiplier': float(avg_cons_mult),
            'effective_metabolism': float(new_effective_metab),
            'effective_consumption': float(new_effective_cons),
            'metab_compensation': float(metab_compensation),
            'cons_compensation': float(cons_compensation),
            'total_compensation': float(total_compensation),
            'amplification': float(amplification),
            'action': action,
            'population': self.population.get_statistics()['population'],
            'consecutive_low': self.consecutive_low,
            'consecutive_high': self.consecutive_high
        })
        
        return action
    
    def update(self, cycle):
        """Called every cycle to check if tuning needed.
        
        Args:
            cycle: Current simulation cycle
        """
        self.current_cycle = cycle
        
        # Initialize tracking on first call
        if cycle == 0:
            stats = self.population.get_statistics()
            self.last_deaths = stats['total_deaths']
            self.last_births = stats['total_births']
            return
        
        # Check if time to tune
        if self.should_tune(cycle):
            death_rate = self.calculate_death_rate()
            action = self.tune_parameters(death_rate)
            
            # Get latest history entry for detailed logging
            if self.tuning_history:
                latest = self.tuning_history[-1]
                
                # Comprehensive debug output
                print(f"\n[Cycle {cycle:5d}] TUNING ACTION: {action}")
                print(f"  Death rate: {death_rate:5.1%}")
                print(f"  World baselines: metab={latest['metabolism']:.3f}, cons={latest['consumption']:.3f}")
                print(f"  Avg gene mults:  metab={latest['avg_metab_multiplier']:.3f}, cons={latest['avg_cons_multiplier']:.3f}")
                print(f"  Effective params: metab={latest['effective_metabolism']:.3f}, cons={latest['effective_consumption']:.3f}")
                print(f"  Gene compensation: {latest['total_compensation']:.1%}")
                if latest['amplification'] > 1.0:
                    print(f"  AMPLIFICATION: {latest['amplification']:.2f}x (fighting evolutionary arms race!)")
                print(f"  Population: {latest['population']}")
                if latest['consecutive_low'] > 0:
                    print(f"  WARNING: {latest['consecutive_low']} consecutive LOW readings!")
                if latest['consecutive_high'] > 0:
                    print(f"  WARNING: {latest['consecutive_high']} consecutive HIGH readings!")
            else:
                # Fallback simple logging
                print(f"[Cycle {cycle:5d}] Death rate: {death_rate:5.1%} -> {action:9s} "
                      f"(metab={self.Agent.WORLD_METABOLISM:.3f}, "
                      f"cons={self.Agent.WORLD_CONSUMPTION_RATE:.3f})")
    
    def save_history(self):
        """Save tuning history to JSON file."""
        if self.output_dir is None:
            return
        
        history_path = self.output_dir / 'tuning_history.json'
        
        data = {
            'initial_baselines': {
                'metabolism': self.initial_metabolism,
                'consumption': self.initial_consumption
            },
            'final_baselines': {
                'metabolism': self.Agent.WORLD_METABOLISM,
                'consumption': self.Agent.WORLD_CONSUMPTION_RATE
            },
            'tuning_history': self.tuning_history,
            'config': {
                'target_min': self.TARGET_DEATH_RATE_MIN,
                'target_max': self.TARGET_DEATH_RATE_MAX,
                'tuning_interval': self.TUNING_INTERVAL,
                'adjustment_strength': self.ADJUSTMENT_STRENGTH,
                'extinction_threshold': self.EXTINCTION_THRESHOLD,
                'emergency_adjustment': self.EMERGENCY_ADJUSTMENT
            }
        }
        
        with open(history_path, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"\nTuning history saved: {history_path}")
        
        # Print summary
        if self.tuning_history:
            in_range = sum(1 for h in self.tuning_history 
                          if self.TARGET_DEATH_RATE_MIN <= h['death_rate'] <= self.TARGET_DEATH_RATE_MAX)
            total = len(self.tuning_history)
            percentage = in_range / total if total > 0 else 0
            
            print(f"\nSelf-Tuning Summary:")
            print(f"  Death rate in target range: {percentage:.1%} of time ({in_range}/{total} intervals)")
            print(f"  Metabolism change: {self.initial_metabolism:.3f} -> {self.Agent.WORLD_METABOLISM:.3f}")
            print(f"  Consumption change: {self.initial_consumption:.3f} -> {self.Agent.WORLD_CONSUMPTION_RATE:.3f}")
