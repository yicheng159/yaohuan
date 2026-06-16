#!/usr/bin/env python
import os
import subprocess
import sys

def main():
    port = os.environ.get('PORT', '8000')
    print(f"[START] Reading PORT from environment: {port}", flush=True)
    
    print("[START] Running migrations...", flush=True)
    subprocess.run([sys.executable, 'manage.py', 'migrate', '--noinput'], check=True, stdout=sys.stdout, stderr=sys.stderr)
    
    cmd = [
        'gunicorn',
        '--bind', f'0.0.0.0:{port}',
        'myproject.wsgi:application'
    ]
    print(f"[START] Running: {' '.join(cmd)}", flush=True)
    subprocess.run(cmd, check=True, stdout=sys.stdout, stderr=sys.stderr)

if __name__ == '__main__':
    main()