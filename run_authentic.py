import subprocess, sys

with open("authentic_out.txt", "w") as f:
    result = subprocess.run([".venv\\Scripts\\python.exe", "scripts/test_authentic_flow.py"], stdout=f, stderr=subprocess.STDOUT)
    
sys.exit(result.returncode)
