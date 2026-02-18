"""
Master script to run all baseline experiments and generate figures
"""

import subprocess
import sys
from pathlib import Path

def run_script(script_name, description):
    """Run a Python script and report status"""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run(
            [sys.executable, script_name],
            cwd=Path(__file__).parent,
            capture_output=False,
            text=True
        )
        
        if result.returncode == 0:
            print(f"✓ {description} completed successfully")
            return True
        else:
            print(f"✗ {description} failed with code {result.returncode}")
            return False
    except Exception as e:
        print(f"✗ Error running {description}: {e}")
        return False

def main():
    """Run complete baseline experiment pipeline"""
    
    print("="*60)
    print("JAIR PAPER BASELINE EXPERIMENTS")
    print("="*60)
    print("\nThis will:")
    print("1. Run random search baseline (3 seeds × 10k gens)")
    print("2. Run fixed constraints baseline (3 seeds × 10k gens)")
    print("3. Generate comparison figures")
    print("\nEstimated time: ~30-60 minutes")
    
    response = input("\nProceed? (y/n): ")
    if response.lower() != 'y':
        print("Aborted.")
        return
    
    # Step 1: Random search
    success = run_script('run_baseline_random.py', 'Random Search Baseline')
    if not success:
        print("\n⚠ Random search failed, but continuing...")
    
    # Step 2: Fixed constraints
    success = run_script('run_baseline_fixed.py', 'Fixed Constraints Baseline')
    if not success:
        print("\n⚠ Fixed constraints failed, but continuing...")
    
    # Step 3: Generate figures
    print("\n" + "="*60)
    print("Generating Figures")
    print("="*60)
    
    run_script('generate_figure_2.py', 'Figure 2: Phase Transition Plot')
    run_script('generate_figure_3_comparison.py', 'Figure 3: Comparison Plot')
    
    print("\n" + "="*60)
    print("✓ BASELINE EXPERIMENTS COMPLETE")
    print("="*60)
    print("\nGenerated files:")
    print("  - results/baselines/random_search_seed*.json")
    print("  - results/baselines/fixed_constraints_seed*.json")
    print("  - figure_2_phase_transition.pdf/png")
    print("  - figure_3_comparison.pdf/png")
    print("\nNext steps:")
    print("  1. Review generated figures")
    print("  2. Update genesis_jair_final.tex with actual data")
    print("  3. Compile LaTeX paper")

if __name__ == '__main__':
    main()
