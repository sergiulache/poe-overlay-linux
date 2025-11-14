#!/bin/bash
# Show last lines of detected Client.txt to help debug zone detection

echo "=== Detecting Client.txt ==="
export PYTHONPATH="src:$PYTHONPATH"

python3 <<'EOF'
import sys
sys.path.insert(0, 'src')
from monitor.client_log import ClientLogMonitor

monitor = ClientLogMonitor()
if monitor.client_txt_path:
    print(f"\n=== Last 20 lines of Client.txt ===")
    print(f"File: {monitor.client_txt_path}\n")

    with open(monitor.client_txt_path, 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()
        for line in lines[-20:]:
            print(line.rstrip())

    print(f"\n=== Looking for pattern ===")
    print('Pattern: : You have entered <zone_name>.')
    print('\nExample match: 2025/11/14 21:22:11 44933602 cff945bb [INFO Client 312] : You have entered The Submerged Passage.')
else:
    print("\nClient.txt not found!")
EOF
