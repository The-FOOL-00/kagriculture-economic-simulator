import pandas as pd
import sys
import os

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

csv_path = "replays/raw/kaggle_index/manifest.csv"
print(f"Reading {csv_path} (Size: {os.path.getsize(csv_path)/1024/1024:.2f} MB)...")

df = pd.read_csv(csv_path)
print(f"Total Rows (Episodes/Records): {len(df):,}")
print("Columns:", list(df.columns))
print("\nFirst 5 rows:")
print(df.head())

print("\n--- Summary Statistics ---")
if 'Date' in df.columns or 'submissionDate' in df.columns:
    date_col = 'Date' if 'Date' in df.columns else 'submissionDate'
    print(f"Date range: {df[date_col].min()} to {df[date_col].max()}")

# Look for user submissions
user_terms = ["55893176", "Sundareswaran", "Apex"]
for term in user_terms:
    matches = df[df.astype(str).apply(lambda row: row.str.contains(term, case=False).any(), axis=1)]
    print(f"Matches for '{term}': {len(matches)} rows")
    if len(matches) > 0:
        print(matches.head(10))

# Save summary to scratch
df.describe(include='all').to_csv("scratch/manifest_summary.csv")
