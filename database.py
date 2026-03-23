import sqlite3
import hashlib
import os
from datetime import datetime

DB_PATH = "users.db"


# ─────────────────────────────────────────────
# CONNECTION HELPER
# ─────────────────────────────────────────────
def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


# ─────────────────────────────────────────────
# SCHEMA CREATION  (run once on startup)
# ─────────────────────────────────────────────
def init_db():
    with get_connection() as conn:
        conn.execute("PRAGMA journal_mode=WAL")
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                username    TEXT    NOT NULL UNIQUE,
                email       TEXT    NOT NULL UNIQUE,
                password    TEXT    NOT NULL,
                role        TEXT    NOT NULL DEFAULT 'user',
                created_at  TEXT    NOT NULL DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS history (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id         INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                input_text      TEXT    NOT NULL,
                label           TEXT    NOT NULL,
                real_prob       REAL    NOT NULL,
                fake_prob       REAL    NOT NULL,
                word_count      INTEGER NOT NULL,
                classified_at   TEXT    NOT NULL DEFAULT (datetime('now')),
                deleted_by_user INTEGER NOT NULL DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS messages (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id    INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                subject    TEXT    NOT NULL,
                body       TEXT    NOT NULL,
                status     TEXT    NOT NULL DEFAULT 'open',
                created_at TEXT    NOT NULL DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS replies (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                message_id INTEGER NOT NULL REFERENCES messages(id) ON DELETE CASCADE,
                admin_id   INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                body       TEXT    NOT NULL,
                created_at TEXT    NOT NULL DEFAULT (datetime('now'))
            );
        """)
        # ── Migrate existing databases: add soft-delete column if missing ──
        try:
            conn.execute(
                "ALTER TABLE history ADD COLUMN deleted_by_user INTEGER NOT NULL DEFAULT 0"
            )
        except Exception:
            pass  # Column already exists — safe to ignore


# ─────────────────────────────────────────────
# PASSWORD UTILITIES
# ─────────────────────────────────────────────
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def verify_password(password: str, hashed: str) -> bool:
    return hash_password(password) == hashed


# ─────────────────────────────────────────────
# USER QUERIES
# ─────────────────────────────────────────────
def create_user(username: str, email: str, password: str, role: str = "user") -> bool:
    try:
        with get_connection() as conn:
            conn.execute(
                "INSERT INTO users (username, email, password, role) VALUES (?, ?, ?, ?)",
                (username.strip().lower(), email.strip().lower(), hash_password(password), role),
            )
        return True
    except sqlite3.IntegrityError:
        return False


def get_user_by_username(username: str):
    with get_connection() as conn:
        return conn.execute(
            "SELECT * FROM users WHERE username = ?",
            (username.strip().lower(),),
        ).fetchone()


def get_user_by_id(user_id: int):
    with get_connection() as conn:
        return conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()


def get_all_users():
    with get_connection() as conn:
        return conn.execute(
            "SELECT id, username, email, role, created_at FROM users ORDER BY created_at DESC"
        ).fetchall()


def delete_user(user_id: int):
    with get_connection() as conn:
        conn.execute("DELETE FROM users WHERE id = ?", (user_id,))


def update_user_role(user_id: int, new_role: str):
    with get_connection() as conn:
        conn.execute("UPDATE users SET role = ? WHERE id = ?", (new_role, user_id))


def update_user_password(user_id: int, new_password: str) -> bool:
    try:
        with get_connection() as conn:
            conn.execute(
                "UPDATE users SET password = ? WHERE id = ?",
                (hash_password(new_password), user_id),
            )
        return True
    except Exception:
        return False


# ─────────────────────────────────────────────
# HISTORY QUERIES
# ─────────────────────────────────────────────
def save_classification(user_id: int, input_text: str, result: dict):
    with get_connection() as conn:
        conn.execute(
            """INSERT INTO history
               (user_id, input_text, label, real_prob, fake_prob, word_count)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (
                user_id,
                input_text[:2000],
                result["label"],
                round(result["real_prob"], 4),
                round(result["fake_prob"], 4),
                result["word_count"],
            ),
        )


def get_user_history(user_id: int, limit: int = 50):
    with get_connection() as conn:
        return conn.execute(
            """SELECT * FROM history
               WHERE user_id = ? AND deleted_by_user = 0
               ORDER BY classified_at DESC LIMIT ?""",
            (user_id, limit),
        ).fetchall()


def delete_history_entry(entry_id: int, user_id: int):
    with get_connection() as conn:
        conn.execute(
            "UPDATE history SET deleted_by_user = 1 WHERE id = ? AND user_id = ?",
            (entry_id, user_id),
        )


def clear_user_history(user_id: int):
    with get_connection() as conn:
        conn.execute(
            "UPDATE history SET deleted_by_user = 1 WHERE user_id = ?", (user_id,)
        )


def delete_selected_history(user_id: int, ids: list):
    """Soft-delete specific history records — hidden from user, visible to admin."""
    if not ids:
        return
    placeholders = ",".join("?" * len(ids))
    with get_connection() as conn:
        conn.execute(
            f"UPDATE history SET deleted_by_user = 1 WHERE user_id = ? AND id IN ({placeholders})",
            [user_id, *ids],
        )


# ─────────────────────────────────────────────
# MESSAGES / SUPPORT CHAT QUERIES
# ─────────────────────────────────────────────
def create_message(user_id: int, subject: str, body: str) -> bool:
    """User submits a new support message."""
    try:
        with get_connection() as conn:
            conn.execute(
                "INSERT INTO messages (user_id, subject, body) VALUES (?, ?, ?)",
                (user_id, subject.strip(), body.strip()),
            )
        return True
    except Exception:
        return False


def get_messages_by_user(user_id: int):
    """Return all messages sent by a specific user, newest first."""
    with get_connection() as conn:
        return conn.execute(
            """SELECT m.*, u.username
               FROM messages m
               JOIN users u ON m.user_id = u.id
               WHERE m.user_id = ?
               ORDER BY m.created_at DESC""",
            (user_id,),
        ).fetchall()


def get_all_messages():
    """Return all messages for the admin view, newest first."""
    with get_connection() as conn:
        return conn.execute(
            """SELECT m.*, u.username
               FROM messages m
               JOIN users u ON m.user_id = u.id
               ORDER BY m.created_at DESC"""
        ).fetchall()


def get_replies_for_message(message_id: int):
    """Return all admin replies for a given message, oldest first."""
    with get_connection() as conn:
        return conn.execute(
            """SELECT r.*, u.username AS admin_name
               FROM replies r
               JOIN users u ON r.admin_id = u.id
               WHERE r.message_id = ?
               ORDER BY r.created_at ASC""",
            (message_id,),
        ).fetchall()


def create_reply(message_id: int, admin_id: int, body: str) -> bool:
    """Admin posts a reply to a message."""
    try:
        with get_connection() as conn:
            conn.execute(
                "INSERT INTO replies (message_id, admin_id, body) VALUES (?, ?, ?)",
                (message_id, admin_id, body.strip()),
            )
        return True
    except Exception:
        return False


def update_message_status(message_id: int, status: str):
    """Set message status: 'open' or 'resolved'."""
    with get_connection() as conn:
        conn.execute(
            "UPDATE messages SET status = ? WHERE id = ?", (status, message_id)
        )


def delete_message(message_id: int):
    """Delete a message and all its replies via CASCADE."""
    with get_connection() as conn:
        conn.execute("DELETE FROM messages WHERE id = ?", (message_id,))


def get_open_message_count() -> int:
    """Count of open messages — used for the admin badge."""
    with get_connection() as conn:
        return conn.execute(
            "SELECT COUNT(*) FROM messages WHERE status = 'open'"
        ).fetchone()[0]


# ─────────────────────────────────────────────
# ADMIN STATS
# ─────────────────────────────────────────────
def get_admin_stats() -> dict:
    with get_connection() as conn:
        total_users   = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        total_classif = conn.execute("SELECT COUNT(*) FROM history").fetchone()[0]
        real_count    = conn.execute("SELECT COUNT(*) FROM history WHERE label = 'REAL'").fetchone()[0]
        fake_count    = conn.execute("SELECT COUNT(*) FROM history WHERE label = 'FAKE'").fetchone()[0]
        uncertain     = conn.execute("SELECT COUNT(*) FROM history WHERE label = 'UNCERTAIN'").fetchone()[0]
        recent_7days  = conn.execute(
            "SELECT COUNT(*) FROM history WHERE classified_at >= datetime('now', '-7 days')"
        ).fetchone()[0]

    return {
        "total_users":   total_users,
        "total_classif": total_classif,
        "real_count":    real_count,
        "fake_count":    fake_count,
        "uncertain":     uncertain,
        "recent_7days":  recent_7days,
    }


def get_all_history(limit: int = 200):
    """Return all classifications for admin — includes soft-deleted rows (deleted_by_user = 1)."""
    with get_connection() as conn:
        return conn.execute(
            """SELECT h.*, u.username
               FROM history h
               JOIN users u ON h.user_id = u.id
               ORDER BY h.classified_at DESC
               LIMIT ?""",
            (limit,),
        ).fetchall()