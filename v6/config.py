import dataclasses
from typing import Optional, Tuple

@dataclasses.dataclass
class V6Config:
    baseline_mode: bool = False
    
    # Experiment 1: Rugged Landscape
    # If None, uses V5 CPPN maps. If tuple (F, k), uses scalar values.
    gray_scott_scalars: Optional[Tuple[float, float]] = None
    
    # Experiment 2: Cost Exponent
    cost_exponent: Optional[float] = None
    
    # Experiment 3: Per-Step Maintenance Cost
    per_step_maintenance_cost: bool = False
    
    # Experiment 4: Relative Reproduction
    relative_reproduction: bool = False
    
    def get_description(self):
        desc = []
        if self.baseline_mode:
            desc.append("Baseline V5")
        if self.gray_scott_scalars:
            desc.append(f"Rugged Landscape F={self.gray_scott_scalars[0]}, k={self.gray_scott_scalars[1]}")
        if self.cost_exponent:
            desc.append(f"Cost Exponent = {self.cost_exponent}")
        if self.per_step_maintenance_cost:
            desc.append("Per-Step Maintenance")
        if self.relative_reproduction:
            desc.append("Relative Reproduction")
        return " | ".join(desc) if desc else "Custom"

# Pre-defined Configurations
EXPERIMENTS = {
    "Exp0_Control": V6Config(baseline_mode=True),
    "Exp1_Rugged_Chaotic": V6Config(baseline_mode=False, gray_scott_scalars=(0.022, 0.051)),
    "Exp1_Rugged_Waves": V6Config(baseline_mode=False, gray_scott_scalars=(0.018, 0.050)),
    "Exp2_Exponent_1.5": V6Config(baseline_mode=False, cost_exponent=1.5),
    "Exp2_Exponent_1.8": V6Config(baseline_mode=False, cost_exponent=1.8),
    "Exp2_Exponent_2.0": V6Config(baseline_mode=False, cost_exponent=2.0),
    "Exp2_Exponent_2.5": V6Config(baseline_mode=False, cost_exponent=2.5),
    "Exp3_Maintenance": V6Config(baseline_mode=False, per_step_maintenance_cost=True),
    "Exp4_RelativeRepro": V6Config(baseline_mode=False, relative_reproduction=True),
    "Exp5_Combined": V6Config(
        baseline_mode=False, 
        gray_scott_scalars=(0.022, 0.051), 
        cost_exponent=2.0, 
        per_step_maintenance_cost=True, 
        relative_reproduction=True
    )
}
