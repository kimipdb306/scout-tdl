# Deploy Kanban to Render (Free Tier)

Render provides free hosting with a public URL that's always accessible.

## Steps

1. **Sign up** at https://render.com (free account)

2. **Create a new Web Service**:
   - Click "New +" → "Web Service"
   - Connect your GitHub (or upload files manually)
   - Repository: https://github.com/yourusername/scout-kanban (push this code first)

3. **Configure**:
   - **Name**: scout-kanban
   - **Runtime**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python3 app.py`
   - **Plan**: Free

4. **Environment Variables**:
   - None needed (uses local JSON storage)

5. **Deploy**:
   - Click "Create Web Service"
   - Wait 2-3 minutes
   - Your URL: `https://scout-kanban-xxxx.onrender.com`

## For Immediate Access (No Deployment)

Use **localhost.run** (no auth, no setup):

```bash
# Terminal 1: Start Flask
source ~/.openclaw/venvs/kanban/bin/activate
cd ~/.openclaw/workspace/integrations/kanban
python3 app.py

# Terminal 2: Create tunnel
ssh -R 80:localhost:8000 localhost.run
```

You'll get a URL like: `https://xxxxx.lhr.life`

Share that URL and you can access the kanban from anywhere.

## Best Option: Render Free Tier

- Always-on (doesn't spin down)
- Public HTTPS URL
- Auto-deploys on git push
- 750 hours/month free

## For Persistence on Mac

To keep Flask + tunnel running 24/7 on your Mac mini, use launchd:

```bash
cat > ~/Library/LaunchAgents/com.scout.kanban.plist <<'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.scout.kanban</string>
    <key>ProgramArguments</key>
    <array>
        <string>bash</string>
        <string>~/.openclaw/workspace/integrations/kanban/start_localhost_run.sh</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/tmp/kanban.log</string>
    <key>StandardErrorPath</key>
    <string>/tmp/kanban.log</string>
</dict>
</plist>
EOF

launchctl load ~/Library/LaunchAgents/com.scout.kanban.plist
```

Then the kanban will auto-start and restart if it crashes.
