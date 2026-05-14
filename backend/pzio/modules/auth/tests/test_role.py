from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from pzio.modules.auth.models import User, UserRole

from ._helpers import auth_header, seed_user


def test_admin_promotes_member_to_manager(client: TestClient, db_session: Session) -> None:
    admin = seed_user(db_session, email="admin@example.com", role=UserRole.ADMINISTRATOR)
    member = seed_user(db_session, email="member@example.com", role=UserRole.TEAM_MEMBER)

    response = client.patch(
        f"/api/users/{member.user_id}/role",
        json={"role": UserRole.MANAGER.value},
        headers=auth_header(admin),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["userId"] == member.user_id
    assert body["role"] == UserRole.MANAGER.value

    db_session.refresh(member)
    assert member.role == UserRole.MANAGER


def test_admin_demotes_administrator_to_team_member(
    client: TestClient, db_session: Session
) -> None:
    admin = seed_user(db_session, email="admin@example.com", role=UserRole.ADMINISTRATOR)
    other = seed_user(db_session, email="other-admin@example.com", role=UserRole.ADMINISTRATOR)

    response = client.patch(
        f"/api/users/{other.user_id}/role",
        json={"role": UserRole.TEAM_MEMBER.value},
        headers=auth_header(admin),
    )

    assert response.status_code == 200
    assert response.json()["role"] == UserRole.TEAM_MEMBER.value

    db_session.refresh(other)
    assert other.role == UserRole.TEAM_MEMBER


def test_admin_cannot_change_own_role(client: TestClient, db_session: Session) -> None:
    admin = seed_user(db_session, email="admin@example.com", role=UserRole.ADMINISTRATOR)

    response = client.patch(
        f"/api/users/{admin.user_id}/role",
        json={"role": UserRole.TEAM_MEMBER.value},
        headers=auth_header(admin),
    )

    assert response.status_code == 400
    assert "own role" in response.json()["detail"].lower()

    db_session.refresh(admin)
    assert admin.role == UserRole.ADMINISTRATOR


def test_non_admin_cannot_change_role(client: TestClient, db_session: Session) -> None:
    member = seed_user(db_session, email="member@example.com", role=UserRole.TEAM_MEMBER)
    target = seed_user(db_session, email="target@example.com", role=UserRole.TEAM_MEMBER)

    response = client.patch(
        f"/api/users/{target.user_id}/role",
        json={"role": UserRole.MANAGER.value},
        headers=auth_header(member),
    )

    assert response.status_code == 403


def test_unknown_user_returns_404(client: TestClient, db_session: Session) -> None:
    admin = seed_user(db_session, email="admin@example.com", role=UserRole.ADMINISTRATOR)

    response = client.patch(
        "/api/users/9999/role",
        json={"role": UserRole.MANAGER.value},
        headers=auth_header(admin),
    )

    assert response.status_code == 404


def test_invalid_role_returns_400(client: TestClient, db_session: Session) -> None:
    admin = seed_user(db_session, email="admin@example.com", role=UserRole.ADMINISTRATOR)
    target = seed_user(db_session, email="target@example.com", role=UserRole.TEAM_MEMBER)

    response = client.patch(
        f"/api/users/{target.user_id}/role",
        json={"role": "SuperAdmin"},
        headers=auth_header(admin),
    )

    assert response.status_code == 400
    assert isinstance(response.json()["detail"], str)


def test_missing_token_returns_401(client: TestClient, db_session: Session) -> None:
    target = seed_user(db_session, email="target@example.com", role=UserRole.TEAM_MEMBER)

    response = client.patch(
        f"/api/users/{target.user_id}/role",
        json={"role": UserRole.MANAGER.value},
    )

    assert response.status_code == 401
