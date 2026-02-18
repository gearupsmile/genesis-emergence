"""
CRISIS DIAGNOSIS SCRIPT
Analyzes checkpoint data to confirm metabolic constraint enforcement failure.
"""
import pickle
import numpy as np
import os
import sys

def analyze_checkpoint(path):
    """Analyze a checkpoint file for constraint violations"""
    print(f"\nAnalyzing checkpoint: {path}")
    
    with open(path, 'rb') as f:
        data = pickle.load(f)
    
    print("\n" + "="*70)
    print("CRISIS DIAGNOSIS REPORT")
    print("="*70)
    print(f"Generation: {data.get('generation')}")
    
    agents = data.get('population', [])
    print(f"Population: {len(agents)} agents")
    
    if not agents:
        print("ERROR: No agents in checkpoint!")
        return None
    
    print("\n" + "-"*70)
    print("AGENT SAMPLE (First 10 agents)")
    print("-"*70)
    
    gene_counts = []
    energies = []
    metabolic_costs = []
    
    # Sample agents
    sample_size = min(10, len(agents))
    for i in range(sample_size):
        agent = agents[i]
        
        # Extract agent data (structure may vary)
        if hasattr(agent, 'genes'):
            genes = agent.genes
            energy = getattr(agent, 'energy', 0)
        elif isinstance(agent, dict):
            genes = agent.get('genes', [])
            energy = agent.get('energy', 0)
        else:
            print(f"Warning: Unknown agent structure: {type(agent)}")
            continue
        
        gene_count = len(genes)
        
        # Calculate EXPECTED metabolic cost
        expected_cost = 0.005 * (gene_count ** 1.5)
        
        gene_counts.append(gene_count)
        energies.append(energy)
        metabolic_costs.append(expected_cost)
        
        # Check if agent should be dead
        should_be_dead = energy < expected_cost
        status = "💀 SHOULD BE DEAD" if should_be_dead else "✓ Viable"
        
        print(f"Agent {i:2d}: Genes={gene_count:4d}, Energy={energy:7.1f}, "
              f"ExpectedCost={expected_cost:7.1f}, Ratio={energy/expected_cost if expected_cost>0 else float('inf'):6.2f} {status}")
    
    print("\n" + "-"*70)
    print("SYSTEM DIAGNOSIS")
    print("-"*70)
    
    avg_genes = np.mean(gene_counts)
    avg_energy = np.mean(energies)
    avg_cost = np.mean(metabolic_costs)
    
    print(f"Average genes/agent:     {avg_genes:8.1f}")
    print(f"Average energy:          {avg_energy:8.1f}")
    print(f"Average expected cost:   {avg_cost:8.1f}")
    print(f"Energy surplus/deficit:  {avg_energy - avg_cost:8.1f}")
    
    # CRITICAL TEST: Count constraint violations
    violations = 0
    for i, (energy, cost) in enumerate(zip(energies, metabolic_costs)):
        if energy < cost:
            violations += 1
    
    print("\n" + "="*70)
    print(f"VERDICT: {violations}/{sample_size} agents VIOLATING CONSTRAINTS")
    print("="*70)
    
    if violations > sample_size * 0.5:
        print("🚨 CRITICAL: >50% of agents should be DEAD but are alive!")
        print("🚨 METABOLIC CONSTRAINT IS NOT BEING ENFORCED!")
    elif avg_genes > 100:
        print("🚨 CRITICAL: Genome bloat detected (avg genes > 100)")
        print("🚨 Constraint parameters may be too weak")
    else:
        print("✓ Constraints appear to be working correctly")
    
    return {
        'generation': data.get('generation'),
        'population': len(agents),
        'avg_genes': avg_genes,
        'avg_energy': avg_energy,
        'avg_cost': avg_cost,
        'violations': violations,
        'sample_size': sample_size
    }

def main():
    # Find the latest checkpoint
    checkpoint_dir = "runs/overnight_200k_20260105_061217/"
    
    if not os.path.exists(checkpoint_dir):
        print(f"ERROR: Checkpoint directory not found: {checkpoint_dir}")
        sys.exit(1)
    
    # Find all checkpoints
    files = os.listdir(checkpoint_dir)
    checkpoints = [f for f in files if f.startswith("checkpoint_") and f.endswith(".pkl")]
    
    if not checkpoints:
        print(f"ERROR: No checkpoint files found in {checkpoint_dir}")
        sys.exit(1)
    
    # Sort by generation number
    checkpoints.sort(key=lambda x: int(x.split('_')[1].split('.')[0]))
    
    print(f"Found {len(checkpoints)} checkpoints")
    print(f"Analyzing latest checkpoint: {checkpoints[-1]}")
    
    # Analyze the latest checkpoint
    latest_path = os.path.join(checkpoint_dir, checkpoints[-1])
    result = analyze_checkpoint(latest_path)
    
    # Also analyze an earlier checkpoint for comparison
    if len(checkpoints) > 1:
        print("\n\n" + "="*70)
        print("COMPARISON: Earlier checkpoint")
        print("="*70)
        earlier_path = os.path.join(checkpoint_dir, checkpoints[0])
        earlier_result = analyze_checkpoint(earlier_path)

if __name__ == "__main__":
    main()
