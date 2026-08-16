import sqlite3
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "sunday.db"


class MemoryStore:
    def __init__(self):
        self.connection = sqlite3.connect(
            DB_PATH,
            check_same_thread=False,
        )

        self._create_tables()

    def _create_tables(self):
        self.connection.execute(
            """
            CREATE TABLE IF NOT EXISTS memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key TEXT UNIQUE NOT NULL,
                value TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        self.connection.commit()

    def set(self, key: str, value: str) -> None:
        key = key.strip()
        value = value.strip()

        if not key or not value:
            raise ValueError(
                "Memory key and value cannot be empty."
            )

        self.connection.execute(
            """
            INSERT INTO memories (
                key,
                value
            )
            VALUES (?, ?)

            ON CONFLICT(key)
            DO UPDATE SET
                value = excluded.value,
                updated_at = CURRENT_TIMESTAMP
            """,
            (key, value),
        )

        self.connection.commit()

    def get(self, key: str) -> str | None:
        row = self.connection.execute(
            """
            SELECT value
            FROM memories
            WHERE key = ?
            """,
            (key.strip(),),
        ).fetchone()

        if row is None:
            return None

        return row[0]

    def delete(self, key: str) -> bool:
        cursor = self.connection.execute(
            """
            DELETE FROM memories
            WHERE key = ?
            """,
            (key.strip(),),
        )

        self.connection.commit()

        return cursor.rowcount > 0

    def all(self) -> list[tuple[str, str]]:
        rows = self.connection.execute(
            """
            SELECT key, value
            FROM memories
            ORDER BY updated_at DESC
            """
        ).fetchall()

        return rows

    def close(self):
        self.connection.close()


memory = MemoryStore()