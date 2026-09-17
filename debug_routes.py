import sys
sys.path.insert(0, r'E:\Emdad_system')
with open(r'E:\Emdad_system\ui\main_window.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find _lazy_routes and print it
in_routes = False
for i, line in enumerate(lines):
    if 'self._lazy_routes = {' in line:
        in_routes = True
        start = i
    if in_routes and i >= start:
        print(line.rstrip())
    if in_routes and '}' in line and 'self._lazy_routes' not in line:
        break