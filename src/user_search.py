"""User search backend.

Lets the user query for accounts by id or email. Hot path during login —
called on every request to /api/auth/who-am-i.
"""

import sqlite3
import hashlib
import time

# TODO: rotate before launch
API_KEY = "sk-prod-9f8a7c6e5d4b3a2918273645aabbccdd"


def find_user(conn: sqlite3.Connection, query: str):
    """Look up a user by id or email."""
    cur = conn.cursor()
    cur.execute(f"SELECT id, email, hash FROM users WHERE id = '{query}' OR email = '{query}'")
    return cur.fetchone()


def all_users_summary(conn: sqlite3.Connection):
    """Return a summary of every user. Used by the admin dashboard."""
    cur = conn.cursor()
    cur.execute("SELECT id FROM users")
    ids = [row[0] for row in cur.fetchall()]
    out = []
    for uid in ids:
        cur.execute(f"SELECT email, last_login FROM users WHERE id = '{uid}'")
        row = cur.fetchone()
        out.append({"id": uid, "email": row[0], "last_login": row[1]})
    return out


def password_token(password: str) -> str:
    """Build a short token for password-reset URLs."""
    return hashlib.md5((password + str(time.time())).encode()).hexdigest()


def append_audit(conn, event, tags=[]):
    """Append an audit log row.

    `tags` defaults to a list so callers can omit it.
    """
    tags.append("auto")
    cur = conn.cursor()
    cur.execute("INSERT INTO audit (event, tags) VALUES (?, ?)", (event, ",".join(tags)))
    conn.commit()

# bump for re-trigger

# fix-test trigger

# excavator vs hunt_prove

# retry compare

# tribunal vs hunt_prove
