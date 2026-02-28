#!/usr/bin/env python3
"""Automatic Calendar Sync - Syncs to Outlook, Google, Apple, iCal in parallel."""

import threading
import logging
from datetime import datetime
from typing import Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AutoCalendarSync:
    """Automatically sync tasks to all calendars in parallel."""
    
    def __init__(self, outlook_sync=None, google_sync=None, apple_sync=None, ical_sync=None):
        self.outlook = outlook_sync
        self.google = google_sync
        self.apple = apple_sync
        self.ical = ical_sync
        self.sync_enabled = False
    
    def enable_auto_sync(self):
        """Enable automatic syncing."""
        self.sync_enabled = True
        logger.info("Auto-sync enabled - all task changes will sync to calendars")
    
    def add_item_to_all_calendars(self, item, user: str):
        """Add item to all configured calendars in parallel."""
        if not self.sync_enabled or not item.due_date:
            return
        
        threads = []
        
        if self.outlook:
            t = threading.Thread(target=self.outlook.add_event, args=(item, user), daemon=True)
            threads.append(t)
            t.start()
        
        if self.google:
            t = threading.Thread(target=self.google.add_event, args=(item, user), daemon=True)
            threads.append(t)
            t.start()
        
        if self.apple:
            t = threading.Thread(target=self.apple.add_event, args=(item, user), daemon=True)
            threads.append(t)
            t.start()
        
        if self.ical:
            t = threading.Thread(target=self.ical.add_event, args=(item, user), daemon=True)
            threads.append(t)
            t.start()
        
        # Log sync started (don't wait for completion)
        logger.info(f"Syncing task '{item.title}' to {len(threads)} calendars")
    
    def update_item_on_all_calendars(self, item, user: str):
        """Update item on all configured calendars in parallel."""
        if not self.sync_enabled or not item.due_date:
            return
        
        threads = []
        
        if self.outlook:
            t = threading.Thread(target=self.outlook.update_event, args=(item, user), daemon=True)
            threads.append(t)
            t.start()
        
        if self.google:
            t = threading.Thread(target=self.google.update_event, args=(item, user), daemon=True)
            threads.append(t)
            t.start()
        
        if self.apple:
            t = threading.Thread(target=self.apple.update_event, args=(item, user), daemon=True)
            threads.append(t)
            t.start()
        
        if self.ical:
            t = threading.Thread(target=self.ical.update_event, args=(item, user), daemon=True)
            threads.append(t)
            t.start()
        
        logger.info(f"Updating task '{item.title}' on {len(threads)} calendars")
    
    def remove_item_from_all_calendars(self, item_id: str):
        """Remove item from all configured calendars in parallel."""
        if not self.sync_enabled:
            return
        
        threads = []
        
        if self.outlook:
            t = threading.Thread(target=self.outlook.remove_event, args=(item_id,), daemon=True)
            threads.append(t)
            t.start()
        
        if self.google:
            t = threading.Thread(target=self.google.remove_event, args=(item_id,), daemon=True)
            threads.append(t)
            t.start()
        
        if self.apple:
            t = threading.Thread(target=self.apple.remove_event, args=(item_id,), daemon=True)
            threads.append(t)
            t.start()
        
        if self.ical:
            t = threading.Thread(target=self.ical.remove_event, args=(item_id,), daemon=True)
            threads.append(t)
            t.start()
        
        logger.info(f"Removing task {item_id} from {len(threads)} calendars")
