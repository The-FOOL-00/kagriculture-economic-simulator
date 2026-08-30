import os
import kaggle_environments

pkg_dir = os.path.dirname(kaggle_environments.__file__)
for root, dirs, files in os.walk(pkg_dir):
    for f in files:
        if f.endswith('.py'):
            fp = os.path.join(root, f)
            with open(fp, 'r', encoding='utf-8', errors='ignore') as file:
                content = file.read()
                for lno, line in enumerate(content.splitlines()):
                    if 'observation' in line and 'step' in line:
                        rel = os.path.relpath(fp, pkg_dir)
                        print(f"{rel}:{lno+1}: {line.strip()}")
