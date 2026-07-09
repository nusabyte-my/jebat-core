#!/usr/bin/env bash
# Manage the Jebat inference stack (systemd --user services). No sudo.
# Usage: jebat-infer [start|stop|restart|status|logs <svc>|disable]
set -u
TARGET=jebat-infer.target
case "${1:-status}" in
  start)   systemctl --user start   "$TARGET" ;;
  stop)    systemctl --user stop    "$TARGET" ;;
  restart) systemctl --user restart "$TARGET" ;;
  status)  systemctl --user status  "$TARGET" --no-pager ;;
  disable) systemctl --user disable "$TARGET" ;;
  logs)
    SVC="${2:-jebat-router.service}"
    journalctl --user -u "$SVC" -f ;;
  *) echo "Usage: $0 [start|stop|restart|status|disable|logs <svc>]"; exit 1 ;;
esac
