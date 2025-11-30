#!/bin/bash
# Check for root-owned files in the repository
# Prevents accidental commits after running commands with sudo

root_files=$(find . -user root 2>/dev/null | grep -v "^$" | head -5)

if [ -n "$root_files" ]; then
    echo "ERROR: Root-owned files detected!"
    echo "$root_files"
    echo ""
    echo "Fix with: sudo chown -R \$USER:\$USER ."
    exit 1
fi

exit 0
