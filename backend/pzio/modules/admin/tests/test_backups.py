from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from pzio.config import settings
from pzio.modules.admin.models import Backup
from pzio.modules.auth.models import UserRole

from ._helpers import auth_header, seed_user


@pytest.fixture
def fake_sqlite_db(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Point settings at a real on-disk SQLite file we can copy.

    The integration test DB is in-memory (sqlite://), so we need a separate
    physical file for the backup endpoint to copy. Contents are irrelevant —
    we only check that the destination file is byte-identical.
    """
    db_file = tmp_path / "pzio.db"
    db_file.write_bytes(b"SQLite format 3\x00 fake-content")

    backup_dir = tmp_path / "backups"
    monkeypatch.setattr(settings, "database_url", f"sqlite:///{db_file}")
    monkeypatch.setattr(settings, "backup_dir", str(backup_dir))
    return db_file


def test_force_backup_as_admin_returns_201_and_creates_file(
    client: TestClient,
    db_session: Session,
    fake_sqlite_db: Path,
    tmp_path: Path,
) -> None:
    admin = seed_user(db_session, email="admin@example.com", role=UserRole.ADMINISTRATOR)

    response = client.post("/api/admin/backups", headers=auth_header(admin))

    assert response.status_code == 201
    body = response.json()
    assert isinstance(body["backupId"], int)
    assert body["status"] == "completed"
    assert "timestamp" in body

    # A new backup file lives in the configured directory and matches the source.
    backup_dir = tmp_path / "backups"
    files = list(backup_dir.iterdir())
    assert len(files) == 1
    assert files[0].read_bytes() == fake_sqlite_db.read_bytes()

    record = db_session.get(Backup, body["backupId"])
    assert record is not None
    assert record.status == "completed"
    assert record.file_path == str(files[0])


def test_force_backup_as_non_admin_returns_403(
    client: TestClient,
    db_session: Session,
    fake_sqlite_db: Path,  # noqa: ARG001 — fixture sets settings even if not used directly
) -> None:
    member = seed_user(db_session, email="member@example.com", role=UserRole.TEAM_MEMBER)

    response = client.post("/api/admin/backups", headers=auth_header(member))

    assert response.status_code == 403


def test_force_backup_without_token_returns_401(client: TestClient) -> None:
    response = client.post("/api/admin/backups")
    assert response.status_code == 401


def test_force_backup_when_db_file_missing_returns_500(
    client: TestClient,
    db_session: Session,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """If the on-disk SQLite file does not exist, the endpoint must fail clearly."""
    monkeypatch.setattr(settings, "database_url", f"sqlite:///{tmp_path / 'missing.db'}")
    monkeypatch.setattr(settings, "backup_dir", str(tmp_path / "backups"))
    admin = seed_user(db_session, email="admin@example.com", role=UserRole.ADMINISTRATOR)

    response = client.post("/api/admin/backups", headers=auth_header(admin))

    assert response.status_code == 500
    assert "Backup failed" in response.json()["detail"]
