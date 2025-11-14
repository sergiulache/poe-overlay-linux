#!/bin/bash
export LD_PRELOAD=/usr/lib/libgtk4-layer-shell.so
exec python src/main.py
