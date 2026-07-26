"""
Local storage helpers - Week 4 additions
--------------------------------------------
Saves chat history and vaccination reminders to local JSON files so they
persist between app restarts. Everything stays on-device (no cloud), same
offline-first principle as the rest of the app.
"""

import json
import os

CHAT_HISTORY_FILE = "chat_history.json"
SESSIONS_FILE = "chat_sessions.json"
REMINDERS_FILE = "vaccination_reminders.json"


def _load_json(path, default):
    if not os.path.exists(path):
        return default
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return default


def _save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_chat_history():
    """Returns a list of [role, text] pairs from previous sessions."""
    return _load_json(CHAT_HISTORY_FILE, [])


def save_chat_history(history):
    _save_json(CHAT_HISTORY_FILE, history)


def clear_chat_history():
    _save_json(CHAT_HISTORY_FILE, [])


def load_reminders():
    """Returns a list of reminder dicts: {id, animal, vaccine, due_date}."""
    return _load_json(REMINDERS_FILE, [])


def save_reminders(reminders):
    _save_json(REMINDERS_FILE, reminders)


def load_sessions():
    """
    Returns a dict of separate saved conversations, keyed by session id:
    { session_id: {title, timestamp, messages: [[role, text], ...]} }
    This powers the 'Recent' chat list in the sidebar.
    """
    return _load_json(SESSIONS_FILE, {})


def save_sessions(sessions):
    _save_json(SESSIONS_FILE, sessions)
