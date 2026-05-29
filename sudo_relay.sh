#!/usr/bin/env bash
# Launcher shim — delegates to the real sudoer daemon in the tree.
exec "/home/akien/dev/src/UnseenUniversity/devices/igor/tools/sudoer_daemon.sh" "$@"
