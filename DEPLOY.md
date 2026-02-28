# Deploy Kanban Board Publicly

## Option 1: Render.com (Recommended - 5 minutes)

1. **Sign up** at https://render.com (free account with GitHub)

2. **Push code to GitHub**:
```bash
cd ~/.openclaw/workspace/integrations/kanban
git init
git add .
git commit -m "initial kanban"
git remote add origin https://github.com/YOUR_USERNAME/scout-kanban.git
git push -u origin main
```

3. **Deploy on Render**:
   - Go to https://render.com/dashboard
   - Click "New +" → "Web Service"
   - Select your `scout-kanban` repo
   - **Name**: scout-kanban
   - **Runtime**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`
   - **Plan**: Free
   - Click "Create Web Service"

4. **Done!** In 2-3 minutes you'll get a public URL:
   ```
   https://scout-kanban-xxxxx.onrender.com
   ```

## Option 2: Quick Tunnel (No Deployment)

Works on Mac mini running 24/7. No signup needed.

```bash
# Terminal 1: Start Flask
source ~/.openclaw/venvs/kanban/bin/activate
cd ~/.openclaw/workspace/integrations/kanban
python3 app.py

# Terminal 2: Create tunnel with localhost.run
ssh -R 80:localhost:8000 localhost.run
```

You'll get a public URL instantly. Share it with anyone.

## Option 3: Keep Persistent on Mac

Run kanban automatically on startup with launchd:

```bash
bash ~/.openclaw/workspace/integrations/kanban/install_launchd.sh
```

Then it auto-starts and restarts if it crashes.

## Data Persistence

- **Local (Mac)**: Data stored in `kanban_data.json`
- **Render**: Data stored per deployment (reset on redeploy)
  - To persist: upgrade to paid tier or use external database

For production: add PostgreSQL or MongoDB.

## Calendar Sync

Syncing to Google Calendar requires `gog` CLI, which only works on your Mac.

For Render deployment, add an endpoint that the kanban calls:

```
POST /api/sync → calls back to your Mac
```

Or set up IFTTT/Zapier integration.

## Scaling

Free tier limits:
- Render: 750 hours/month (always running)
- localhost.run: Unlimited (PC must stay on)

For serious use: upgrade Render to paid (~$7/month for PostgreSQL + web service).
