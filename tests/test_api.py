import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path
from secrets import token_urlsafe

from app import create_app
from werkzeug.security import check_password_hash


class ApiTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.path = Path(directory.name) / "test.db"
        demo_value = token_urlsafe(16)
        self.config = {
            "TESTING": True,
            "DATABASE": self.path,
            "PROFILE_TOKEN": "perfil-demo",
            "DEMO_PASSWORD": demo_value,
        }
        self.client = create_app(self.config).test_client()

    def test_health(self):
        response = self.client.get("/api/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["status"], "ok")

    def test_profile_requires_correct_key(self):
        self.assertEqual(self.client.get("/api/profile").status_code, 401)
        self.assertEqual(self.client.get("/api/profile", headers={"X-API-Key": "otra"}).status_code, 401)
        self.assertEqual(self.client.get("/api/profile", headers={"X-API-Key": "perfil-demo"}).status_code, 200)

    def test_profile_without_configuration_stays_closed(self):
        client = create_app(dict(self.config, PROFILE_TOKEN=None)).test_client()
        self.assertEqual(client.get("/api/profile").status_code, 401)

    def test_login_valid_invalid_and_malformed(self):
        for payload, expected in (
            ({"username": "admin", "password": self.config["DEMO_PASSWORD"]}, 200),
            ({"username": "admin", "password": token_urlsafe(16)}, 401),
            ({"username": "desconocido", "password": self.config["DEMO_PASSWORD"]}, 401),
            (["admin"], 400),
            ({"username": 3, "password": self.config["DEMO_PASSWORD"]}, 400),
        ):
            with self.subTest(payload=payload):
                self.assertEqual(self.client.post("/api/login", json=payload).status_code, expected)

    def test_seeded_password_is_hashed(self):
        with closing(sqlite3.connect(self.path)) as conn:
            stored = conn.execute("SELECT password FROM users WHERE id = 1").fetchone()[0]
        self.assertNotEqual(stored, self.config["DEMO_PASSWORD"])
        self.assertTrue(check_password_hash(stored, self.config["DEMO_PASSWORD"]))

    def test_migration_preserves_existing_login_and_is_idempotent(self):
        legacy = self.path.with_name("legacy.db")
        old_value = token_urlsafe(16)
        with closing(sqlite3.connect(legacy)) as conn:
            conn.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, username TEXT, password TEXT)")
            conn.execute("INSERT INTO users VALUES (?, ?, ?)", (7, "legado", old_value))
            conn.commit()
        config = dict(self.config, DATABASE=legacy, DEMO_PASSWORD=None)
        for _ in range(2):
            client = create_app(config).test_client()
            response = client.post("/api/login", json={"username": "legado", "password": old_value})
            self.assertEqual(response.status_code, 200)
        with closing(sqlite3.connect(legacy)) as conn:
            stored = conn.execute("SELECT password FROM users WHERE id = 7").fetchone()[0]
        self.assertTrue(check_password_hash(stored, old_value))
