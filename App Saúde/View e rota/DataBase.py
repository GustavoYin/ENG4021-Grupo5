"""Conexão com o banco (SQLite, biblioteca padrão). Uma conexão por requisição."""
import sqlite3
from pathlib import Path

from flask import current_app, g


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(current_app.config["DATABASE"])
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


def close_db(_erro=None):
    conn = g.pop("db", None)
    if conn is not None:
        conn.close()


def init_app(app):
    Path(app.config["DATABASE"]).parent.mkdir(parents=True, exist_ok=True)
    app.teardown_appcontext(close_db)
    schema = Path(__file__).with_name("schema.sql").read_text(encoding="utf-8")
    with app.app_context():
        get_db().executescript(schema)
