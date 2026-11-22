#!/bin/sh
# macOS: double-click this file in Finder to open the Variant Designer.
# (The first time, macOS may ask: right-click it, choose Open, then Open.)
cd "$(dirname "$0")" || exit 1
./design.sh "$@"
status=$?
if [ $status -ne 0 ]; then
    echo
    echo "The Variant Designer stopped with a problem (see above). Press Enter to close."
    read -r _
fi
exit $status
