import hashlib
import glob
import os

files = sorted(glob.glob('experiments/EXP-ARCH-003_H1_TERMINAL_REPAIR/**/*', recursive=True))
for f in files:
    if os.path.isfile(f):
        h = hashlib.sha256(open(f, 'rb').read()).hexdigest()
        rel = f.replace(os.sep, '/')
        print(f"{h}  {rel}")
