"""Histórico de posts (SQLite) para não repetir promoções."""
import sqlite3
import time

from .config import config


def _conn():
    conn = sqlite3.connect(config.db_path)
    conn.execute(
        "CREATE TABLE IF NOT EXISTS posts (product_id TEXT PRIMARY KEY, price REAL, posted_at REAL)"
    )
    return conn


def can_post(product_id: str, price: float) -> bool:
    with _conn() as c:
        row = c.execute(
            "SELECT price, posted_at FROM posts WHERE product_id = ?", (product_id,)
        ).fetchone()
    if not row:
        return True
    last_price, posted_at = row
    old = time.time() - posted_at > config.repost_after_days * 86400
    return old or price < last_price * 0.95  # repost se caiu 5%+


def mark_posted(product_id: str, price: float) -> None:
    with _conn() as c:
        c.execute(
            "INSERT OR REPLACE INTO posts VALUES (?, ?, ?)", (product_id, price, time.time())
        )
