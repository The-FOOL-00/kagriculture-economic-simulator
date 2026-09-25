import os
import kaggle_environments.envs.kaggriculture.kaggriculture as kg

engine_file = kg.__file__
with open(engine_file, 'r', encoding='utf-8') as f:
    text = f.read()

lines = text.splitlines()
print(f"Engine path: {engine_file}")
print(f"Total lines: {len(lines)}")

# Find all top-level functions and classes
import ast
tree = ast.parse(text)
for node in tree.body:
    if isinstance(node, ast.FunctionDef):
        print(f"Function: {node.name} (lines {node.lineno}-{node.end_lineno})")
    elif isinstance(node, ast.ClassDef):
        print(f"Class: {node.name} (lines {node.lineno}-{node.end_lineno})")
