# database.py  — Firebase Firestore version
# Drop-in replacement for the SQLite version.
# All function signatures are IDENTICAL so authentication.py needs zero changes.

import hashlib
import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime, timezone


# ─────────────────────────────────────────────
# CONNECTION HELPER
# ─────────────────────────────────────────────
def get_db():
    """Return a Firestore client, initialising Firebase once per session."""
    if not firebase_admin._apps:
        key_dict = dict(st.secrets["firebase"])
        # Streamlit stores the private key with literal \n — convert to real newlines
        key_dict["private_key"] = key_dict["private_key"].replace("\\n", "\n")
        cred = credentials.Certificate(key_dict)
        firebase_admin.initialize_app(cred)
    return firestore.client()


def init_db():
    """
    No-op on Firestore — collections are created automatically on first write.
    Kept so existing calls to init_db() in your app don't break.
    """
    pass


# ─────────────────────────────────────────────
# PASSWORD UTILITIES  (unchanged)
# ─────────────────────────────────────────────
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def verify_password(password: str, hashed: str) -> bool:
    return hash_password(password) == hashed


# ─────────────────────────────────────────────
# USER QUERIES
# ─────────────────────────────────────────────
def create_user(username: str, email: str, password: str, role: str = "user") -> bool:
    """Returns False if username or email already taken."""
    db = get_db()
    username = username.strip().lower()
    email    = email.strip().lower()

    # Check username uniqueness
    if db.collection("users").document(username).get().exists:
        return False

    # Check email uniqueness
    existing_email = db.collection("users").where("email", "==", email).limit(1).get()
    if existing_email:
        return False

    db.collection("users").document(username).set({
        "username":   username,
        "email":      email,
        "password":   hash_password(password),
        "role":       role,
        "created_at": datetime.now(timezone.utc).isoformat(),
    })
    return True


def get_user_by_username(username: str):
    """Returns a dict with id, username, email, password, role — or None."""
    db = get_db()
    doc = db.collection("users").document(username.strip().lower()).get()
    if not doc.exists:
        return None
    data = doc.to_dict()
    data["id"] = doc.id   # use username as the id (Firestore document ID)
    return data


def get_user_by_id(user_id):
    """user_id is the username string (Firestore document ID)."""
    return get_user_by_username(str(user_id))


def get_all_users():
    """Returns a list of dicts — same fields as the old SQLite rows."""
    db = get_db()
    docs = db.collection("users").order_by("created_at", direction=firestore.Query.DESCENDING).get()
    users = []
    for doc in docs:
        data = doc.to_dict()
        data["id"] = doc.id
        users.append(data)
    return users


def delete_user(user_id):
    db = get_db()
    username = str(user_id)
    db.collection("users").document(username).delete()
    # Cascade: delete all history and messages for this user
    _delete_collection_where(db, "history",  "user_id", username)
    _delete_collection_where(db, "messages", "user_id", username)


def update_user_role(user_id, new_role: str):
    db = get_db()
    db.collection("users").document(str(user_id)).update({"role": new_role})


def update_user_password(user_id, new_password: str) -> bool:
    try:
        db = get_db()
        db.collection("users").document(str(user_id)).update({
            "password": hash_password(new_password)
        })
        return True
    except Exception:
        return False


# ─────────────────────────────────────────────
# HISTORY QUERIES
# ─────────────────────────────────────────────
def save_classification(user_id, input_text: str, result: dict):
    db = get_db()
    db.collection("history").add({
        "user_id":         str(user_id),
        "input_text":      input_text[:2000],
        "label":           result["label"],
        "real_prob":       round(result["real_prob"], 4),
        "fake_prob":       round(result["fake_prob"], 4),
        "word_count":      result["word_count"],
        "deleted_by_user": False,
        "classified_at":   datetime.now(timezone.utc).isoformat(),
    })


def get_user_history(user_id, limit: int = 50):
    db = get_db()
    docs = (
        db.collection("history")
        .where("user_id", "==", str(user_id))
        .where("deleted_by_user", "==", False)
        .order_by("classified_at", direction=firestore.Query.DESCENDING)
        .limit(limit)
        .get()
    )
    return _docs_to_dicts(docs)


def delete_history_entry(entry_id, user_id):
    db = get_db()
    db.collection("history").document(str(entry_id)).update({"deleted_by_user": True})


def clear_user_history(user_id):
    db = get_db()
    docs = db.collection("history").where("user_id", "==", str(user_id)).get()
    for doc in docs:
        doc.reference.update({"deleted_by_user": True})


def delete_selected_history(user_id, ids: list):
    if not ids:
        return
    db = get_db()
    for entry_id in ids:
        db.collection("history").document(str(entry_id)).update({"deleted_by_user": True})


# ─────────────────────────────────────────────
# MESSAGES / SUPPORT CHAT QUERIES
# ─────────────────────────────────────────────
def create_message(user_id, subject: str, body: str) -> bool:
    try:
        db = get_db()
        db.collection("messages").add({
            "user_id":    str(user_id),
            "subject":    subject.strip(),
            "body":       body.strip(),
            "status":     "open",
            "created_at": datetime.now(timezone.utc).isoformat(),
        })
        return True
    except Exception:
        return False


def get_messages_by_user(user_id):
    db = get_db()
    docs = (
        db.collection("messages")
        .where("user_id", "==", str(user_id))
        .order_by("created_at", direction=firestore.Query.DESCENDING)
        .get()
    )
    rows = _docs_to_dicts(docs)
    # Attach username to each row (authentication.py expects m.username)
    user = get_user_by_id(user_id)
    username = user["username"] if user else str(user_id)
    for row in rows:
        row["username"] = username
    return rows


def get_all_messages():
    db = get_db()
    docs = (
        db.collection("messages")
        .order_by("created_at", direction=firestore.Query.DESCENDING)
        .get()
    )
    rows = _docs_to_dicts(docs)
    # Attach username to each message row
    for row in rows:
        user = get_user_by_id(row["user_id"])
        row["username"] = user["username"] if user else row["user_id"]
    return rows


def get_replies_for_message(message_id):
    db = get_db()
    docs = (
        db.collection("replies")
        .where("message_id", "==", str(message_id))
        .order_by("created_at")
        .get()
    )
    rows = _docs_to_dicts(docs)
    for row in rows:
        admin = get_user_by_id(row["admin_id"])
        row["admin_name"] = admin["username"] if admin else row["admin_id"]
    return rows


def create_reply(message_id, admin_id, body: str) -> bool:
    try:
        db = get_db()
        db.collection("replies").add({
            "message_id": str(message_id),
            "admin_id":   str(admin_id),
            "body":       body.strip(),
            "created_at": datetime.now(timezone.utc).isoformat(),
        })
        return True
    except Exception:
        return False


def update_message_status(message_id, status: str):
    db = get_db()
    db.collection("messages").document(str(message_id)).update({"status": status})


def delete_message(message_id):
    db = get_db()
    db.collection("messages").document(str(message_id)).delete()
    # Cascade delete replies
    _delete_collection_where(db, "replies", "message_id", str(message_id))


def get_open_message_count() -> int:
    db = get_db()
    docs = db.collection("messages").where("status", "==", "open").get()
    return len(docs)


# ─────────────────────────────────────────────
# ADMIN STATS
# ─────────────────────────────────────────────
def get_admin_stats() -> dict:
    db = get_db()
    all_users   = db.collection("users").get()
    all_history = db.collection("history").get()

    total_users   = len(all_users)
    total_classif = len(all_history)
    real_count    = sum(1 for d in all_history if d.to_dict().get("label") == "REAL")
    fake_count    = sum(1 for d in all_history if d.to_dict().get("label") == "FAKE")
    uncertain     = sum(1 for d in all_history if d.to_dict().get("label") == "UNCERTAIN")

    cutoff = datetime.now(timezone.utc).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    from datetime import timedelta
    cutoff_str = (cutoff - timedelta(days=7)).isoformat()
    recent_7days = sum(
        1 for d in all_history
        if d.to_dict().get("classified_at", "") >= cutoff_str
    )

    return {
        "total_users":   total_users,
        "total_classif": total_classif,
        "real_count":    real_count,
        "fake_count":    fake_count,
        "uncertain":     uncertain,
        "recent_7days":  recent_7days,
    }


def get_all_history(limit: int = 200):
    db = get_db()
    docs = (
        db.collection("history")
        .order_by("classified_at", direction=firestore.Query.DESCENDING)
        .limit(limit)
        .get()
    )
    rows = _docs_to_dicts(docs)
    for row in rows:
        user = get_user_by_id(row["user_id"])
        row["username"] = user["username"] if user else row["user_id"]
    return rows


# ─────────────────────────────────────────────
# INTERNAL HELPERS
# ─────────────────────────────────────────────
def _docs_to_dicts(docs) -> list:
    """Convert Firestore document snapshots to plain dicts, adding 'id' field."""
    rows = []
    for doc in docs:
        data = doc.to_dict()
        data["id"] = doc.id
        rows.append(data)
    return rows


def _delete_collection_where(db, collection: str, field: str, value: str):
    """Delete all documents in a collection where field == value."""
    docs = db.collection(collection).where(field, "==", value).get()
    for doc in docs:
        doc.reference.delete()