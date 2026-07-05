# -*- coding: utf-8 -*-
"""Database engine configuration tests."""

import importlib
from pathlib import Path


def test_database_module_imports_with_sqlite_url(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "sqlite+aiosqlite:///./test_import.db")

    import config
    import database

    importlib.reload(config)
    reloaded_database = importlib.reload(database)

    assert reloaded_database.engine.url.drivername == "sqlite+aiosqlite"

    monkeypatch.delenv("DATABASE_URL", raising=False)
    importlib.reload(config)
    importlib.reload(database)


def test_settings_load_backend_env_from_project_root(monkeypatch):
    import config

    project_root = Path(__file__).resolve().parents[2]
    env_file = project_root / "backend" / ".env"
    expected_password = next(
        line.split("=", 1)[1].strip()
        for line in env_file.read_text(encoding="utf-8").splitlines()
        if line.startswith("MYSQL_PASSWORD=")
    )

    monkeypatch.chdir(project_root)
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("MYSQL_PASSWORD", raising=False)

    settings = config.Settings()

    assert settings.MYSQL_PASSWORD == expected_password
