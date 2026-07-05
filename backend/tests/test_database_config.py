# -*- coding: utf-8 -*-
"""Database engine configuration tests."""

import importlib


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
