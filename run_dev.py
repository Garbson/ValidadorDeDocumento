#!/usr/bin/env python3
"""Run backend (FastAPI) and frontend (Vite) concurrently for development.

Usage:
  python3 run_dev.py            # default: backend :8000, frontend :3000
  BACKEND_PORT=9000 FRONTEND_PORT=3100 python3 run_dev.py

Requirements:
  - Python deps installed: pip install -r requirements.txt
  - Node deps installed: (cd frontend && npm install)

Stops all on Ctrl+C.
"""
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).parent
FRONTEND_DIR = ROOT / 'frontend'

BACKEND_PORT = os.environ.get('BACKEND_PORT', '8000')
FRONTEND_PORT = os.environ.get('FRONTEND_PORT', '3000')

processes = []

def start_process(cmd, cwd=None, name=None):
    print(f"[START] {name or cmd[0]} -> {' '.join(cmd)}")
    proc = subprocess.Popen(cmd, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    processes.append((name, proc))
    return proc

def stream_output(name, proc):
    assert proc.stdout
    for line in proc.stdout:
        sys.stdout.write(f"[{name}] {line}")
        sys.stdout.flush()

def main():
    if not FRONTEND_DIR.exists():
        print('Frontend directory not found: frontend/')
        sys.exit(1)

    # Detect uvicorn availability
    use_uvicorn = True
    try:
        import uvicorn  # noqa: F401
    except Exception:
        use_uvicorn = False
        print('[WARN] uvicorn not installed, fallback to python api/main.py (no reload).')

    env = os.environ.copy()
    # Ensure frontend knows API base if served separately
    if 'VITE_API_URL' not in env:
        env['VITE_API_URL'] = '/api'

    backend_cmd = [
        sys.executable, '-m', 'uvicorn', f'api.main:app', '--reload', '--port', BACKEND_PORT, '--host', '0.0.0.0'
    ] if use_uvicorn else [sys.executable, 'api/main.py']

    frontend_cmd = ['npm', 'run', 'dev', '--', '--port', FRONTEND_PORT]

    backend = start_process(backend_cmd, cwd=ROOT, name='backend')
    time.sleep(1.5)
    frontend = start_process(frontend_cmd, cwd=FRONTEND_DIR, name='frontend')

    try:
        # Non-blocking stream of both outputs
        while True:
            alive = False
            for name, proc in processes:
                if proc.poll() is None:
                    alive = True
                    # Drain available lines without blocking
                    if proc.stdout:
                        while True:
                            try:
                                line = proc.stdout.readline()
                            except Exception:
                                line = ''
                            if not line:
                                break
                            sys.stdout.write(f"[{name}] {line}")
                else:
                    code = proc.returncode
                    print(f"[EXIT] {name} exited with code {code}")
                    # If any process dies, shut down all
                    raise KeyboardInterrupt
            if not alive:
                break
            time.sleep(0.5)
    except KeyboardInterrupt:
        print('\n[SHUTDOWN] Stopping processes...')
    finally:
        for name, proc in processes:
            if proc.poll() is None:
                print(f"[KILL] {name}")
                try:
                    proc.send_signal(signal.SIGINT)
                    time.sleep(0.5)
                    if proc.poll() is None:
                        proc.terminate()
                    time.sleep(0.5)
                    if proc.poll() is None:
                        proc.kill()
                except Exception as e:
                    print(f"[ERR] killing {name}: {e}")
        print('[DONE] All processes stopped.')

if __name__ == '__main__':
    main()
