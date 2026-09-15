import kaggle_environments
import inspect

eng_file = r'C:\Users\Sundareswaran\AppData\Local\Python\pythoncore-3.14-64\Lib\site-packages\kaggle_environments\envs\kaggriculture\kaggriculture.py'
with open(eng_file, 'r') as f:
    lines = f.readlines()

for idx, line in enumerate(lines):
    if 'op == "WATER"' in line or 'op == "HARVEST"' in line or 'op == "PLANT"' in line:
        print(f"--- Line {idx+1}: {line.strip()} ---")
        for j in range(idx, min(len(lines), idx + 25)):
            print(f"{j+1}: {lines[j]}", end='')
