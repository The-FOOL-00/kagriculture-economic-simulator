import os
import glob
import re

patterns = [
    (r'super-additive', 'super-additive'),
    (r'\+930\.55', '+930.55'),
    (r'-0\.428', '-0.428'),
    (r'0\.669', '0.669'),
    (r'10\s*/\s*10.*original', '10/10 original passed'),
    (r'original.*gate.*pass', 'original gate passed')
]

for p in sorted(glob.glob('reports/*.md')):
    with open(p, 'r', encoding='utf-8') as f:
        text = f.read()
    for pat, label in patterns:
        matches = list(re.finditer(pat, text, re.IGNORECASE))
        if matches:
            print(f"{p}: Found {len(matches)} occurrences of '{label}'")
            for m in matches[:5]:
                # find line number
                line_no = text[:m.start()].count('\n') + 1
                snippet = text[max(0, m.start()-40):min(len(text), m.end()+40)].replace('\n', ' ')
                print(f"   L{line_no}: ...{snippet}...")
