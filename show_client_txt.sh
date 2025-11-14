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
    print('Pattern: : Generating level <num> area "<zone_name>"')
    print('\nExample match: 2024/11/14 10:00:00 123 [INFO] : Generating level 1 area "Twilight Strand"')
else:
    print("\nClient.txt not found!")
EOF
