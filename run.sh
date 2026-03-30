#!/usr/bin/env bash
# Launch Redundant File Remover on macOS / Linux
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
python3 "$SCRIPT_DIR/redundant_file_remover.py" &
