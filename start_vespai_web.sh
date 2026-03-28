#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

cd "$SCRIPT_DIR"

LOCK_FILE="$SCRIPT_DIR/.vespai.lock"

# Load .env if it exists
if [ -f .env ]; then
	set -a
	. ./.env
	set +a
fi

if command -v flock >/dev/null 2>&1; then
	# Hold an exclusive lock for the full runtime; fail fast if another instance owns it.
	exec 9>"$LOCK_FILE"
	if ! flock -n 9; then
		echo "Another VespAI instance is already running. Stop it before starting a new one."
		exit 1
	fi
	export PYTHONPATH="/usr/lib/python3/dist-packages${PYTHONPATH:+:$PYTHONPATH}"
	exec "$SCRIPT_DIR/.venv/bin/python" vespai.py --web "$@"
fi

if pgrep -f "[v]espai.py" >/dev/null 2>&1; then
	echo "Another VespAI instance is already running. Stop it before starting a new one."
	exit 1
fi

export PYTHONPATH="/usr/lib/python3/dist-packages${PYTHONPATH:+:$PYTHONPATH}"
exec "$SCRIPT_DIR/.venv/bin/python" vespai.py --web "$@"
