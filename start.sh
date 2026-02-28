#!/bin/bash
# Start Kanban board server

source ~/.openclaw/venvs/kanban/bin/activate
cd ~/.openclaw/workspace/integrations/kanban
python3 app.py
