import kaggle_environments.envs.kaggriculture.kaggriculture as kg
import inspect
for name, fn in inspect.getmembers(kg, inspect.isfunction):
    if "plant" in name.lower():
        print(f"Function: {name}")
        print(inspect.getsource(fn))
