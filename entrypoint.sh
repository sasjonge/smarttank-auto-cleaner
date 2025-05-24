#!/usr/bin/env bash
set -eu

# ------------------ required -----------------------------------------------
: "${PRINTER_IP:?Set PRINTER_IP env var}"

# ------------------ decide mode --------------------------------------------
if [[ -n "${SCHEDULE_FILE:-}" ]]; then
    # ── cron mode ───────────────────────────────────────────────────────────
    if [[ ! -f "${SCHEDULE_FILE}" ]]; then
        echo "SCHEDULE_FILE '${SCHEDULE_FILE}' not found" >&2
        exit 1
    fi

    echo "→ Using schedule file: ${SCHEDULE_FILE}"
    # ensure final newline & substitute ${PRINTER_IP}
    envsubst < "${SCHEDULE_FILE}" | sed -e '$a\' > /tmp/cronfile
    crontab /tmp/cronfile
    echo "Loaded cron jobs:"
    cat /tmp/cronfile
    echo "──────────────────────────────────────────────"
    exec cron -f
else
    # ── immediate one-shot ──────────────────────────────────────────────────
    echo "→ No SCHEDULE_FILE set – running job now"
    exec python /app/smarttankclean.py --printer "${PRINTER_IP}" "$@"
fi
