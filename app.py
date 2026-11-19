"""API REST local para la práctica de DevSecOps."""

import hmac
import os
import sqlite3
from contextlib import closing
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, jsonify, request
from werkzeug.security import check_password_hash, generate_password_hash

BASE_DIR = Path(__file__).resolve().parent


def create_app(test_config=None):
    load_dotenv(BASE_DIR / ".env")
    app = Flask(__name__)
    app.config.from_mapping(
        DATABASE=BASE_DIR / "practica.db",
        PROFILE_TOKEN=os.getenv("PRACTICA_API_KEY"),
        DEMO_PASSWORD=os.getenv("PRACTICA_DEMO_PASSWORD"),
    )
    if test_config is not None:
        app.config.update(test_config)

    init_db(app.config["DATABASE"], app.config["DEMO_PASSWORD"])

    @app.get("/api/health")
    def health():
        return jsonify(status="ok", service="API de práctica")

    @app.get("/api/profile")
    def profile():
        expected = app.config["PROFILE_TOKEN"]
        supplied = request.headers.get("X-API-Key", "")
        if not expected or not hmac.compare_digest(
            supplied.encode("utf-8"), expected.encode("utf-8")
        ):
            return jsonify(error="No autorizado"), 401
        return jsonify(user="admin", message="Acceso de demostración")

    @app.post("/api/login")
    def login():
        data = request.get_json(silent=True)
        if not isinstance(data, dict):
            return jsonify(error="Se esperaba un objeto JSON"), 400

        username = data.get("username")
        password = data.get("password")
        if not isinstance(username, str) or not isinstance(password, str):
            return jsonify(error="Usuario y contraseña deben ser texto"), 400

        with closing(sqlite3.connect(app.config["DATABASE"])) as conn:
            row = conn.execute(
                "SELECT id, username, password FROM users WHERE username = ?",
                (username,),
            ).fetchone()

        if row and check_password_hash(row[2], password):
            return jsonify(message="Login correcto", user={"id": row[0], "username": row[1]})
        return jsonify(error="Credenciales inválidas"), 401

    return app


def init_db(db_path, demo_password):
    with closing(sqlite3.connect(db_path)) as conn, conn:
        conn.execute("BEGIN IMMEDIATE")
        conn.execute("PRAGMA secure_delete = ON")
        conn.execute(
            "CREATE TABLE IF NOT EXISTS users "
            "(id INTEGER PRIMARY KEY, username TEXT, password TEXT)"
        )
        # Migra los datos del esquema original una sola vez.
        if conn.execute("PRAGMA user_version").fetchone()[0] == 0:
            for user_id, legacy_password in conn.execute("SELECT id, password FROM users"):
                conn.execute(
                    "UPDATE users SET password = ? WHERE id = ?",
                    (generate_password_hash(legacy_password), user_id),
                )
            conn.execute("PRAGMA user_version = 1")

        if demo_password:
            for user_id, username in ((1, "admin"), (2, "estudiante")):
                if not conn.execute("SELECT 1 FROM users WHERE id = ?", (user_id,)).fetchone():
                    conn.execute(
                        "INSERT INTO users (id, username, password) VALUES (?, ?, ?)",
                        (user_id, username, generate_password_hash(demo_password)),
                    )


if __name__ == "__main__":
    create_app().run(host="127.0.0.1", port=5000, debug=False)
