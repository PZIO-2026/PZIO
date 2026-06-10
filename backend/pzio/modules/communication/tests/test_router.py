from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from pzio.modules.communication import service
from pzio.modules.communication.router import _is_mime_type_allowed


def test_mime_type_validation() -> None:
    """Test MIME type whitelist validation with wildcard patterns."""
    # Allowed types
    assert _is_mime_type_allowed("image/png") is True
    assert _is_mime_type_allowed("image/jpeg") is True
    assert _is_mime_type_allowed("image/gif") is True
    assert _is_mime_type_allowed("image/webp") is True
    assert _is_mime_type_allowed("application/pdf") is True
    
    # Disallowed types
    assert _is_mime_type_allowed("application/x-msdownload") is False
    assert _is_mime_type_allowed("application/x-executable") is False
    # Plain text, html and json are now allowed by the relaxed whitelist
    assert _is_mime_type_allowed("text/plain") is True
    assert _is_mime_type_allowed("text/html") is True
    assert _is_mime_type_allowed("application/json") is True
    assert _is_mime_type_allowed(None) is False
    assert _is_mime_type_allowed("") is False


def test_get_comments_returns_history(
    client: TestClient, user_factory, auth_headers, comment_factory
) -> None:
    user = user_factory(avatar="https://example.com/avatar.png")
    first = comment_factory(task_id=1, author_id=user.user_id, content="First")
    second = comment_factory(task_id=1, author_id=user.user_id, content="Second")
    comment_factory(task_id=2, author_id=user.user_id, content="Other task")

    response = client.get("/api/tasks/1/comments", headers=auth_headers(user))

    assert response.status_code == 200
    payload = response.json()
    assert {item["commentId"] for item in payload} == {first.comment_id, second.comment_id}
    assert {item["content"] for item in payload} == {"First", "Second"}
    assert all(item["user"]["firstName"] == user.first_name for item in payload)
    assert all(item["user"]["lastName"] == user.last_name for item in payload)
    assert all(item["user"]["avatar"] == user.avatar for item in payload)


def test_get_comments_task_id_out_of_range(
    client: TestClient, user_factory, auth_headers
) -> None:
    user = user_factory()

    response = client.get("/api/tasks/9999999999/comments", headers=auth_headers(user))

    assert response.status_code == 400


def test_edit_comment_success(
    client: TestClient, user_factory, auth_headers, comment_factory
) -> None:
    user = user_factory()
    comment = comment_factory(task_id=1, author_id=user.user_id, content="Old")

    response = client.patch(
        f"/api/comments/{comment.comment_id}",
        json={"content": "New"},
        headers=auth_headers(user),
    )

    assert response.status_code == 200
    assert response.json()["content"] == "New"


def test_edit_comment_not_found(
    client: TestClient, user_factory, auth_headers
) -> None:
    user = user_factory()

    response = client.patch(
        "/api/comments/999",
        json={"content": "New"},
        headers=auth_headers(user),
    )

    assert response.status_code == 404


def test_edit_comment_forbidden(
    client: TestClient, user_factory, auth_headers, comment_factory
) -> None:
    owner = user_factory(email="owner@example.com")
    other = user_factory(email="other@example.com")
    comment = comment_factory(task_id=1, author_id=owner.user_id, content="Hello")

    response = client.patch(
        f"/api/comments/{comment.comment_id}",
        json={"content": "Nope"},
        headers=auth_headers(other),
    )

    assert response.status_code == 403


def test_delete_comment_success(
    client: TestClient, user_factory, auth_headers, comment_factory, db_session
) -> None:
    user = user_factory()
    comment = comment_factory(task_id=1, author_id=user.user_id, content="To delete")

    response = client.delete(
        f"/api/comments/{comment.comment_id}",
        headers=auth_headers(user),
    )

    assert response.status_code == 204
    with pytest.raises(service.CommentNotFoundError):
        service.get_comment(db_session, comment.comment_id)


def test_delete_comment_not_found(
    client: TestClient, user_factory, auth_headers
) -> None:
    user = user_factory()

    response = client.delete(
        "/api/comments/999",
        headers=auth_headers(user),
    )

    assert response.status_code == 404


def test_delete_comment_forbidden(
    client: TestClient, user_factory, auth_headers, comment_factory
) -> None:
    owner = user_factory(email="owner2@example.com")
    other = user_factory(email="other2@example.com")
    comment = comment_factory(task_id=1, author_id=owner.user_id, content="Cannot delete")

    response = client.delete(
        f"/api/comments/{comment.comment_id}",
        headers=auth_headers(other),
    )

    assert response.status_code == 403


def test_upload_attachment_success(
    client: TestClient, user_factory, auth_headers, upload_dir: Path
) -> None:
    user = user_factory()

    response = client.post(
        "/api/tasks/1/attachments",
        files={"file": ("note.txt", b"hello", "text/plain")},
        headers=auth_headers(user),
    )

    assert response.status_code == 201
    assert response.json()["filename"] == "note.txt"
    assert upload_dir.exists()
    assert len(list(upload_dir.iterdir())) == 1


def test_list_attachments_filters_by_task(
    client: TestClient,
    user_factory,
    auth_headers,
    attachment_factory,
) -> None:
    user = user_factory()
    first = attachment_factory(
        task_id=1,
        uploader_id=user.user_id,
        filename="first.txt",
        content_type="text/plain",
        data=b"first",
    )
    attachment_factory(
        task_id=2,
        uploader_id=user.user_id,
        filename="second.txt",
        content_type="text/plain",
        data=b"second",
    )

    response = client.get("/api/tasks/1/attachments", headers=auth_headers(user))

    assert response.status_code == 200
    assert {item["attachmentId"] for item in response.json()} == {first.attachment_id}


def test_download_attachment_success(
    client: TestClient,
    user_factory,
    auth_headers,
    attachment_factory,
) -> None:
    user = user_factory()
    attachment = attachment_factory(
        task_id=1,
        uploader_id=user.user_id,
        filename="file.bin",
        content_type="application/octet-stream",
        data=b"data",
    )

    response = client.get(
        f"/api/attachments/{attachment.attachment_id}/download",
        headers=auth_headers(user),
    )

    assert response.status_code == 200
    assert response.content == b"data"
    assert response.headers["content-type"].startswith("application/octet-stream")


def test_download_attachment_not_found(
    client: TestClient, user_factory, auth_headers
) -> None:
    user = user_factory()

    response = client.get(
        "/api/attachments/999/download",
        headers=auth_headers(user),
    )

    assert response.status_code == 404


def test_download_attachment_missing_file_returns_404(
    client: TestClient,
    user_factory,
    auth_headers,
    attachment_factory,
) -> None:
    user = user_factory()
    attachment = attachment_factory(
        task_id=1,
        uploader_id=user.user_id,
        filename="file.bin",
        content_type="application/octet-stream",
        data=b"data",
    )

    Path(attachment.file_path).unlink()

    response = client.get(
        f"/api/attachments/{attachment.attachment_id}/download",
        headers=auth_headers(user),
    )

    assert response.status_code == 404


def test_delete_attachment_success(
    client: TestClient,
    user_factory,
    auth_headers,
    attachment_factory,
) -> None:
    user = user_factory()
    attachment = attachment_factory(
        task_id=1,
        uploader_id=user.user_id,
        filename="file.bin",
        content_type="application/octet-stream",
        data=b"data",
    )

    response = client.delete(
        f"/api/attachments/{attachment.attachment_id}",
        headers=auth_headers(user),
    )

    assert response.status_code == 204


def test_delete_attachment_forbidden(
    client: TestClient,
    user_factory,
    auth_headers,
    attachment_factory,
) -> None:
    owner = user_factory(email="owner3@example.com")
    other = user_factory(email="other3@example.com")
    attachment = attachment_factory(
        task_id=1,
        uploader_id=owner.user_id,
        filename="file.bin",
        content_type="application/octet-stream",
        data=b"data",
    )

    response = client.delete(
        f"/api/attachments/{attachment.attachment_id}",
        headers=auth_headers(other),
    )

    assert response.status_code == 403


def test_delete_attachment_not_found(
    client: TestClient, user_factory, auth_headers
) -> None:
    user = user_factory()

    response = client.delete(
        "/api/attachments/999",
        headers=auth_headers(user),
    )

    assert response.status_code == 404


def test_upload_attachment_file_too_large(
    client: TestClient, user_factory, auth_headers
) -> None:
    user = user_factory()
    # Create a file larger than 10MB (11MB)
    large_file_data = b"x" * (11 * 1024 * 1024)

    response = client.post(
        "/api/tasks/1/attachments",
        files={"file": ("large.png", large_file_data, "image/png")},
        headers=auth_headers(user),
    )

    assert response.status_code == 400
    assert "too large" in response.json()["detail"].lower()


def test_upload_attachment_unsupported_mime_type(
    client: TestClient, user_factory, auth_headers
) -> None:
    user = user_factory()

    response = client.post(
        "/api/tasks/1/attachments",
        files={"file": ("script.exe", b"MZ\x90\x00", "application/x-msdownload")},
        headers=auth_headers(user),
    )

    assert response.status_code == 400
    assert "not allowed" in response.json()["detail"].lower()


def test_upload_attachment_pdf_allowed(
    client: TestClient, user_factory, auth_headers, upload_dir: Path
) -> None:
    user = user_factory()

    response = client.post(
        "/api/tasks/1/attachments",
        files={"file": ("document.pdf", b"%PDF-1.4", "application/pdf")},
        headers=auth_headers(user),
    )

    assert response.status_code == 201
    assert response.json()["filename"] == "document.pdf"


def test_upload_attachment_image_types_allowed(
    client: TestClient, user_factory, auth_headers, upload_dir: Path
) -> None:
    user = user_factory()

    for mime_type in ["image/png", "image/jpeg", "image/gif", "image/webp"]:
        response = client.post(
            "/api/tasks/1/attachments",
            files={"file": ("image.bin", b"imagedata", mime_type)},
            headers=auth_headers(user),
        )

        assert response.status_code == 201, f"Failed for {mime_type}"
