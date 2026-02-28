#!/bin/bash
# Start Kanban board with ngrok tunnel

set -e

KANBAN_DIR=~/.openclaw/workspace/integrations/kanban
URL_FILE=$KANBAN_DIR/public_url.txt
LOG_FILE=$KANBAN_DIR/kanban.log
NGROK_LOG=$KANBAN_DIR/ngrok.log

echo "Starting Kanban board with public URL..."

# Start Flask app
source ~/.openclaw/venvs/kanban/bin/activate
cd $KANBAN_DIR

# Kill any existing processes
pkill -f "python3 app.py" 2>/dev/null || true
pkill -f "ngrok http" 2>/dev/null || true
sleep 1

# Start Flask in background
python3 app.py > $LOG_FILE 2>&1 &
FLASK_PID=$!
echo "Flask started (PID: $FLASK_PID)"
sleep 2

# Start ngrok tunnel
ngrok http 8000 --log=json > $NGROK_LOG 2>&1 &
NGROK_PID=$!
echo "ngrok started (PID: $NGROK_PID)"
sleep 3

# Extract public URL from ngrok
PUBLIC_URL=$(grep -o '"public_url":"[^"]*' $NGROK_LOG | head -1 | cut -d'"' -f4)

if [ -z "$PUBLIC_URL" ]; then
  # Fallback: check ngrok API
  PUBLIC_URL=$(curl -s http://127.0.0.1:4040/api/tunnels | grep -o '"public_url":"[^"]*' | head -1 | cut -d'"' -f4)
fi

if [ -z "$PUBLIC_URL" ]; then
  PUBLIC_URL="http://localhost:8000"
  echo "⚠ Could not find public URL. Using localhost fallback."
fi

# Save URL to file
echo "$PUBLIC_URL" > $URL_FILE
echo "✓ Kanban board available at: $PUBLIC_URL"
echo "✓ URL saved to: $URL_FILE"

# Show processes
echo ""
echo "Running processes:"
ps aux | grep -E "python3 app.py|ngrok http" | grep -v grep || true

echo ""
echo "Logs:"
echo "  Flask: $LOG_FILE"
echo "  ngrok: $NGROK_LOG"
echo ""
echo "Keeping services running. Press Ctrl+C to stop."

# Keep running
wait
