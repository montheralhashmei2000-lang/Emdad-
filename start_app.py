import os, sys, subprocess
os.environ['QT_QPA_PLATFORM'] = 'offscreen'
result = subprocess.run([sys.executable, 'main.py'], cwd=r'E:\Emdad_system')
sys.exit(result.returncode)