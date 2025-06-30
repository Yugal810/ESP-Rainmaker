import subprocess
import os
import sys

# Helper to get absolute path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Log file paths
LOGS = {
    'OTA Server': os.path.join(BASE_DIR, 'ota_server.log'),
    'ESP Flashing Tool': os.path.join(BASE_DIR, 'esp_flashing_tool.log'),
    'Main FastAPI Server': os.path.join(BASE_DIR, 'main_fastapi_server.log'),
}

# Commands and working directories
servers = [
    {
        'name': 'OTA Server',
        'cmd': [sys.executable, 'app.py'],
        'cwd': os.path.join(BASE_DIR, 'OTA', 'ota_server')
    },
    {
        'name': 'ESP Flashing Tool',
        'cmd': [sys.executable, '-m', 'uvicorn', 'app:app', '--host', '0.0.0.0', '--port', '8000'],
        'cwd': os.path.join(BASE_DIR, 'esp_flashing_tool')
    },
    {
        'name': 'Main FastAPI Server',
        'cmd': [sys.executable, '-m', 'uvicorn', 'main:app', '--host', '0.0.0.0', '--port', '9000'],
        'cwd': BASE_DIR
    }
]

processes = []
for server in servers:
    print(f"Starting {server['name']}...")
    log_file = open(LOGS[server['name']], 'a')
    p = subprocess.Popen(server['cmd'], cwd=server['cwd'], stdout=log_file, stderr=log_file)
    processes.append((p, log_file))
    print(f"{server['name']} started. Logging to {LOGS[server['name']]}")

print("All servers started! Press Ctrl+C to exit.")
try:
    for p, log_file in processes:
        p.wait()
except KeyboardInterrupt:
    print("\nShutting down all servers...")
    for p, log_file in processes:
        p.terminate()
        log_file.close()
    print("All servers stopped.") 