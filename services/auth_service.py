import hashlib
import sqlite3
from typing import Optional

from database import get_connection


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def verify_user(username: str, password: str) -> bool:
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT password_hash FROM users WHERE username=?", (username,)
        ).fetchone()
        if not row:
            return False
        return row["password_hash"] == hash_password(password)
    finally:
        conn.close()


def create_user(username: str, password: str) -> bool:
    conn = get_connection()
    try:
        conn.execute(
            "INSERT INTO users (username, password_hash) VALUES (?, ?)",
            (username, hash_password(password)),
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()
