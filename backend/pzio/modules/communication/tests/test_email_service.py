from __future__ import annotations

from pzio.modules.communication.factory import get_email_service
from pzio.modules.communication.mock import MockEmailService


def test_mock_email_service_stores_messages_in_memory() -> None:
    service = MockEmailService()

    result = service.send_email("user@test.com", "Hello", "Body")

    assert result is True
    assert len(service.sent_emails) == 1
    assert service.sent_emails[0] == {
        "to": "user@test.com",
        "subject": "Hello",
        "body": "Body",
    }


def test_factory_returns_mock_service() -> None:
    service = get_email_service()

    assert isinstance(service, MockEmailService)
