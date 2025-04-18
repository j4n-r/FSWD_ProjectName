import sqlite3
from datetime import datetime
from werkzeug.security import check_password_hash, generate_password_hash

import click
from flask import current_app
from flask import g


def get_db():
    """Connect to the application's configured database. The connection
    is unique for each request and will be reused if this is called
    again.
    """
    if "db" not in g:
        g.db = sqlite3.connect(
            current_app.config["DATABASE"], detect_types=sqlite3.PARSE_DECLTYPES
        )
        g.db.row_factory = sqlite3.Row

    return g.db


def close_db(e=None):
    """If this request connected to the database, close the
    connection.
    """
    db = g.pop("db", None)

    if db is not None:
        db.close()


def init_db():
    """Run schema.sql"""
    try:
        db = get_db()

        with current_app.open_resource("schema.sql") as f:
            db.executescript(f.read().decode("utf8"))
        add_default_users()
        return "Initialized DB"
    except Exception:
        raise Exception


@click.command("init-db")  
def init_db_command():
    """Register command `flask init-db`"""
    res = init_db()
    click.echo(res)


sqlite3.register_converter("timestamp", lambda v: datetime.fromisoformat(v.decode())) # unixtimestamps


def init_app(app):
    """Register database functions with the Flask app. This is called by
    the application factory.
    """
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)

def add_default_users():
    email = "admin@admin.com"
    password = "admin"
    name = "admin"
    db = get_db()
    try:
        db.execute(
            "INSERT INTO users (email, password, name) VALUES (?, ?, ?)",
            (email, generate_password_hash(password), name),
        )
        db.commit()
    except db.IntegrityError:
        error = f"User {email} is already registered."
        print(error)

