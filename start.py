#!/usr/bin/env python
import os
import subprocess
import sys

def main():
    port = os.environ.get('PORT', '8000')
    print(f"Starting server on port {port}", flush=True)
    
    subprocess.run([sys.executable, 'manage.py', 'migrate', '--noinput'], check=True)
    
    cmd = [
        'gunicorn',
        '--bind', f'0.0.0.0:{port}',
        'myproject.wsgi:application'
    ]
    print(f"Running: {' '.join(cmd)}", flush=True)
    subprocess.run(cmd, check=True)

if __name__ == '__main__':
    main()