#!/usr/bin/env bash
# Launcher shim — delegates to the real sudoer daemon in the tree.
exec "$(dirname "$0")/wild_igor/igor/tools/sudoer_daemon.sh" "$@"
