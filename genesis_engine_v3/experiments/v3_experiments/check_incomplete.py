import glob, pandas as pd
print("Checking for incomplete runs...")
for f in glob.glob('logs/50k_batch_fresh/sham/**/*.csv', recursive=True):
    try:
        df = pd.read_csv(f)
        gen = df['gen'].max() if not df.empty else 0
        if gen < 50000:
            print(f"{f}: {gen}")
    except Exception as e:
        print(f"{f}: ERROR {e}")
