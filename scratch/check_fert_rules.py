eng_file = r'C:\Users\Sundareswaran\AppData\Local\Python\pythoncore-3.14-64\Lib\site-packages\kaggle_environments\envs\kaggriculture\kaggriculture.py'
with open(eng_file, 'r') as f:
    lines = f.readlines()

for idx, line in enumerate(lines):
    if 'op == "FERTILIZE"' in line:
        for j in range(idx, min(len(lines), idx + 25)):
            print(f"{j+1}: {lines[j]}", end='')
