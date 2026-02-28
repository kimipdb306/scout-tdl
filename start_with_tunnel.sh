#!/bin/bash
# Start Kanban with localhost.run tunnel (no auth needed)

KANBAN_DIR=~/.openclaw/workspace/integrations/kanban
URL_FILE=$KANBAN_DIR/public_url.txt

echo "Starting Kanban board with public tunnel..."

# Kill existing processes
pkill -f "python3 app.py" 2>/dev/null || true
sleep 1

# Start Flask
source ~/.openclaw/venvs/kanban/bin/activate
cd $KANBAN_DIR
python3 app.py > kanban.log 2>&1 &
FLASK_PID=$!

echo "✓ Flask started (PID: $FLASK_PID)"
echo ""
echo "In another terminal, run:"
echo "  ssh -R 80:localhost:8000 localhost.run"
echo ""
echo "This will give you a public URL like: https://xxxxx.lhr.life"
echo "Share that URL to access your kanban from anywhere."
echo ""
echo "Or deploy to Render (see deploy_to_render.md)"
echo ""
echo "Flask running at http://localhost:8000"
echo "Logs: $KANBAN_DIR/kanban.log"

wait
