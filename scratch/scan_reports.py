import os
import glob
import re

terms = [
    'original gate',
    '10/10',
    'gate passed',
    'synergy',
    'super-additive',
    '-0.428',
    '0.669',
    '+930.55',
    '930.55',
    '20,000',
    '20000',
    '15.51',
    '0.04',
    'RELEASE CERTIFIED',
    'QUALIFIED',
    'FAIL',
    'PASS'
]

print("Scanning report files for keywords...")
report_files = glob.glob('reports/**/*.md', recursive=True) + glob.glob('*.md')

for filepath in sorted(report_files):
    print(f"\n==================================================")
    print(f"FILE: {filepath}")
    print(f"==================================================")
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()
    
    for i, line in enumerate(lines):
        line_lower = line.lower()
        for term in ['10/10', 'passed', 'fail', 'synergy', 'super-additive', '-0.428', '0.669', '930.55', '20,000', '15.51']:
            if term in line_lower:
                print(f"  L{i+1:4d}: {line.strip()[:120]}")
