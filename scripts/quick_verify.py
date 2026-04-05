import subprocess
import sys
import os

def run_verify():
    # Make sure docs exist
    os.makedirs("docs", exist_ok=True)
    
    versions = {
        "V1": ["python", "genesis_engine_v1/simulator.py", "--cycles", "100", "--with-agents", "--no-snapshots"],
        "V2": ["python", "-m", "pytest", "genesis_engine_v2/test_minimal_smoke.py"],
        "V3": ["python", "-m", "pytest", "genesis_engine_v3/tests/validate_stage1.py"],
        "V4": ["python", "-m", "pytest", "genesis_engine_v3/tests/test_cppn.py"],
    }
    
    log_file = "docs/verification_log.md"
    results = {}
    
    with open(log_file, "w") as f:
        f.write("# Quick Verification Log\n\n")
        
        for v, cmd in versions.items():
            print(f"Running {v} verification...")
            f.write(f"## {v} Execution\n```\nCommand: {' '.join(cmd)}\n")
            
            try:
                # Use sys.executable to ensure we use the current python environment
                cmd[0] = sys.executable 
                res = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
                
                if res.returncode == 0:
                    results[v] = "PASS"
                    f.write(res.stdout + "\n```\n\n**STATUS: PASS**\n\n")
                else:
                    results[v] = "FAIL"
                    f.write(res.stdout + "\n" + res.stderr + "\n```\n\n**STATUS: FAIL**\n\n")
                    
            except Exception as e:
                results[v] = "FAIL"
                f.write(f"{str(e)}\n```\n\n**STATUS: FAIL**\n\n")
                
            print(f"[{results[v]}] {v} Verification")
            
    print("\n--- FINAL VERIFICATION RESULTS ---")
    for v, status in results.items():
        print(f"{v}: {status}")
        
    if "FAIL" in results.values():
        sys.exit("\nERROR: Verification failed on one or more versions. Check docs/verification_log.md")
    else:
        print("\nAll codebase versions successfully validated!")

if __name__ == "__main__":
    run_verify()
