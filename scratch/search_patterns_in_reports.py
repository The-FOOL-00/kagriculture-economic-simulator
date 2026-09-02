import glob
import re

reports = sorted(glob.glob('reports/*.md'))

search_patterns = [
    (r'10\s*/\s*10.*pass', 'Claims of 10/10 passed'),
    (r'original.*gate.*pass', 'Claims of original gate passed'),
    (r'-0\.428', '-0.428 placeholder'),
    (r'0\.669', '0.669 p-value placeholder'),
    (r'super-additive', 'super-additive claim'),
    (r'\+?930\.55', '930.55 synergy claim'),
    (r'statistically indistinguishable from zero', 'zero interaction claim'),
    (r'interaction is zero', 'interaction is zero claim'),
    (r'15\.51\s*ms', '15.51 ms runtime claim'),
    (r'0\.04\s*ms', '0.04 ms runtime claim')
]

for rep in reports:
    print(f"\n==========================================")
    print(f"AUDITING: {rep}")
    print(f"==========================================")
    with open(rep, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        
    for pat, desc in search_patterns:
        for idx, line in enumerate(lines):
            if re.search(pat, line, re.IGNORECASE):
                print(f"  [{desc}] Line {idx+1}: {line.strip()[:140]}")
