#!/usr/bin/env python3
"""Teams Calendar Sync - OAuth2 flow for Microsoft Teams."""

import msal
import requests
from pathlib import Path
import json
from datetime import datetime

class TeamsCalendarSync:
    def __init__(self, client_id: str, client_secret: str, tenant_id: str = "common"):
        self.client_id = client_id
        self.client_secret = client_secret
        self.tenant_id = tenant_id
        self.graph_endpoint = "https://graph.microsoft.com/v1.0"
        self.tokens_file = Path.home() / ".openclaw/workspace/integrations/kanban/teams_tokens.json"
        self.tokens = self._load_tokens()
    
    def _load_tokens(self) -> dict:
        """Load saved tokens from disk."""
        if self.tokens_file.exists():
            return json.loads(self.tokens_file.read_text())
        return {}
    
    def _save_tokens(self, tokens: dict):
        """Save tokens to disk."""
        self.tokens_file.parent.mkdir(parents=True, exist_ok=True)
        self.tokens_file.write_text(json.dumps(tokens, indent=2))
    
    def get_auth_url(self) -> tuple:
        """Return Azure AD auth URL and state."""
        state = "scout_tdl_state_123"  # In production, use random state
        auth_url = (
            f"https://login.microsoftonline.com/{self.tenant_id}/oauth2/v2.0/authorize?"
            f"client_id={self.client_id}"
            f"&response_type=code"
            f"&scope=https://graph.microsoft.com/.default"
            f"&redirect_uri=http://localhost:5555/auth/teams/callback"
            f"&state={state}"
        )
        return auth_url, state
    
    def get_token(self, code: str, user: str) -> str:
        """Exchange auth code for access token."""
        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": "http://localhost:5555/auth/teams/callback",
            "scope": "https://graph.microsoft.com/.default"
        }
        
        resp = requests.post(
            f"https://login.microsoftonline.com/{self.tenant_id}/oauth2/v2.0/token",
            data=data
        )
        resp.raise_for_status()
        token_data = resp.json()
        
        # Save token for this user
        self.tokens[user] = token_data
        self._save_tokens(self.tokens)
        
        return token_data.get("access_token")
    
    def get_access_token(self, user: str) -> str:
        """Get valid access token, refreshing if needed."""
        if user not in self.tokens:
            raise ValueError(f"No Teams OAuth token for user {user}. Please authenticate first.")
        
        token_data = self.tokens[user]
        
        # Check if expired and refresh if needed
        if "expires_in" in token_data:
            # In production, check actual expiry
            pass
        
        return token_data.get("access_token")
    
    def add_event(self, item, user: str) -> dict:
        """Add calendar event for task."""
        try:
            token = self.get_access_token(user)
        except ValueError:
            return {"error": "Not authenticated with Teams"}
        
        headers = {"Authorization": f"Bearer {token}"}
        
        event = {
            "subject": f"[TDL] {item.title}",
            "start": {
                "dateTime": f"{item.due_date}T09:00:00",
                "timeZone": "Eastern Standard Time"
            },
            "end": {
                "dateTime": f"{item.due_date}T10:00:00",
                "timeZone": "Eastern Standard Time"
            },
            "categories": ["TDL", f"priority-{item.priority.name}"],
            "isReminderOn": True,
            "reminderMinutesBeforeStart": 1440,  # 24 hours
        }
        
        resp = requests.post(
            f"{self.graph_endpoint}/me/events",
            headers=headers,
            json=event
        )
        
        if resp.status_code == 201:
            return resp.json()
        else:
            return {"error": resp.text}
    
    def update_event(self, item, user: str) -> dict:
        """Update calendar event for task."""
        # In a real implementation, track event IDs in the database
        return {"message": "Event update not yet implemented"}
    
    def remove_event(self, item_id: str) -> dict:
        """Remove calendar event for task."""
        # In a real implementation, track event IDs in the database
        return {"message": "Event removal not yet implemented"}
