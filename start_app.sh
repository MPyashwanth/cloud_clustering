#!/usr/bin/env bash
set -euo pipefail

APP_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
APP_URL="http://localhost:8501"
LOG_FILE="${TMPDIR:-/tmp}/global-development-clustering-streamlit.log"

if [[ ! -f "$APP_DIR/app.py" ]]; then
    echo "Could not find app.py next to this script." >&2
    exit 1
fi

if [[ -x "$APP_DIR/.venv/Scripts/python.exe" ]]; then
    PYTHON="$APP_DIR/.venv/Scripts/python.exe"
elif [[ -x "$APP_DIR/.venv/bin/python" ]]; then
    PYTHON="$APP_DIR/.venv/bin/python"
else
    if command -v python3 >/dev/null 2>&1; then
        SYSTEM_PYTHON=(python3)
    elif command -v python >/dev/null 2>&1; then
        SYSTEM_PYTHON=(python)
    elif command -v py >/dev/null 2>&1; then
        SYSTEM_PYTHON=(py -3)
    else
        echo "Python 3 is required to set up the app environment." >&2
        exit 1
    fi

    echo "Creating the project's virtual environment..."
    "${SYSTEM_PYTHON[@]}" -m venv "$APP_DIR/.venv"
    if [[ -x "$APP_DIR/.venv/Scripts/python.exe" ]]; then
        PYTHON="$APP_DIR/.venv/Scripts/python.exe"
    elif [[ -x "$APP_DIR/.venv/bin/python" ]]; then
        PYTHON="$APP_DIR/.venv/bin/python"
    else
        echo "Could not find the Python executable in the new virtual environment." >&2
        exit 1
    fi
fi

if [[ ! -f "$APP_DIR/requirements.txt" ]]; then
    echo "Could not find requirements.txt next to this script." >&2
    exit 1
fi

if ! "$PYTHON" -c "import matplotlib, numpy, openpyxl, pandas, sklearn, streamlit" >/dev/null 2>&1; then
    echo "Installing the app dependencies into the project's virtual environment..."
    "$PYTHON" -m pip install -r "$APP_DIR/requirements.txt"
fi

open_browser() {
    if command -v cmd.exe >/dev/null 2>&1; then
        cmd.exe /c start "" "$APP_URL" >/dev/null 2>&1
    elif command -v xdg-open >/dev/null 2>&1; then
        xdg-open "$APP_URL" >/dev/null 2>&1 &
    elif command -v open >/dev/null 2>&1; then
        open "$APP_URL" >/dev/null 2>&1 &
    else
        echo "Open this URL in your browser: $APP_URL"
    fi
}

if curl --silent --fail "$APP_URL" >/dev/null 2>&1; then
    echo "The app is already running."
    open_browser
    exit 0
fi

nohup "$PYTHON" -m streamlit run "$APP_DIR/app.py" \
    --server.headless true \
    --server.address 0.0.0.0 \
    --server.port 8501 \
    >"$LOG_FILE" 2>&1 &

for _ in {1..30}; do
    if curl --silent --fail "$APP_URL" >/dev/null 2>&1; then
        echo "The app is running at $APP_URL"
        open_browser
        exit 0
    fi
    sleep 1
done

echo "The app did not start. Check the Streamlit log at:" >&2
echo "  $LOG_FILE" >&2
exit 1
