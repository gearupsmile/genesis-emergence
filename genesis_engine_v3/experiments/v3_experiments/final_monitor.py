import time
import os
import pandas as pd
import subprocess

TARGET_GEN = 50000
CSV_FILE = "logs/50k_batch_fresh/sham/seed_2021/metrics_sham_2021.csv"
REAL_DIR = "logs/50k_batch_fresh/real"
SHAM_DIR = "logs/50k_batch_fresh/sham"
OUTPUT_PLOT = "final_comparison.png"
OUTPUT_MD = "final_results.md"

def get_current_gen():
    try:
        if os.path.exists(CSV_FILE):
            df = pd.read_csv(CSV_FILE)
            if not df.empty and 'gen' in df.columns:
                return df['gen'].max()
    except Exception:
        pass
    return 0

print("Starting Final Run Monitor...")
while True:
    gen = get_current_gen()
    print(f"Current Gen: {gen}/{TARGET_GEN}")
    if gen >= TARGET_GEN:
        print("Final run reached 50,000! Executing analysis...")
        break
    time.sleep(60)

# Run Analysis
cmd = [
    "python", "analysis/compare_runs_multi.py",
    "--real", REAL_DIR,
    "--sham", SHAM_DIR,
    "--output", OUTPUT_PLOT,
    "--stats"
]
print(f"Running: {' '.join(cmd)}")
result = subprocess.run(cmd, capture_output=True, text=True)

# Parse stats
stdout = result.stdout
print(stdout)

p_val = "N/A"
conclusion = "Niche construction [DOES NOT] significantly break the EPC plateau (p < 0.01)"

# Very crude parsing of the p-value for EPC at Gen 50k
for block in stdout.split("[Gen"):
    if "50000" in block[:15]:
        for line in block.split("\n"):
            if "avg_fitness" in line and "p=" in line:
                try:
                    p_str = line.split("p=")[1].strip().split()[0]
                    p_val_num = float(p_str)
                    p_val = p_str
                    if p_val_num < 0.01:
                        conclusion = "Niche construction [DOES] significantly break the EPC plateau (p < 0.01)"
                except:
                    pass

# Write Report
md_content = f"""# Final 50k Experiment Results

## Conclusion
**{conclusion}**

## P-Value (at 50k Generations for EPC)
**p = {p_val}**

## Analysis Stats
```text
{stdout}
```

## Graph
![Final Comparison]({OUTPUT_PLOT})
"""

with open(OUTPUT_MD, "w") as f:
    f.write(md_content)

print(f"Saved complete report to {OUTPUT_MD}")
