import kaggle_environments.envs.kaggriculture.kaggriculture as kg
import inspect
print("Checking if any collision check exists in kaggriculture:")
src = inspect.getsource(kg._set_farmer_position)
print(src)
