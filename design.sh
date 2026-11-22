#!/bin/sh
# Open the ExTetris Variant Designer on macOS or Linux.
cd "$(dirname "$0")" || exit 1
for py in python3 python; do
    if command -v "$py" >/dev/null 2>&1 && "$py" -c 'import sys; sys.exit(sys.version_info < (3, 9))' 2>/dev/null; then
        exec "$py" design.py "$@"
    fi
done
echo "Python 3.9 or newer was not found. Install it from https://www.python.org" >&2
exit 1
