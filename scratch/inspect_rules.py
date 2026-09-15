path = r"C:\Users\Sundareswaran\AppData\Local\Python\pythoncore-3.14-64\Lib\site-packages\kaggle_environments\envs\kaggriculture\kaggriculture.py"
with open(path) as f:
    text = f.read()

idx = text.find('def _drop_inventories_to_shed')
print(text[idx:idx+800])
