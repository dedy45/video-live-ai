import subprocess, sys

with open("test_results.txt", "w") as f:
    result = subprocess.run([".venv\\Scripts\\python.exe", "-m", "pytest", "tests/", "-v"], stdout=f, stderr=subprocess.STDOUT)
    
sys.exit(result.returncode)
