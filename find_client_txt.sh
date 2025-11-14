#!/bin/bash
# Helper script to find Client.txt on your system

echo "=== Searching for Client.txt ==="
echo ""

# Search in common locations
echo "Checking Steam library locations..."
find ~/.steam -name "Client.txt" 2>/dev/null | grep -i "path of exile"
find ~/.local/share/Steam -name "Client.txt" 2>/dev/null | grep -i "path of exile"

echo ""
echo "Checking Lutris prefixes..."
find ~/.var/app/net.lutris.Lutris/data/lutris -name "Client.txt" 2>/dev/null
find ~/Games -name "Client.txt" 2>/dev/null

echo ""
echo "If found above, set the environment variable:"
echo "  export POE_CLIENT_TXT='/full/path/to/Client.txt'"
echo "  ./run.sh"
