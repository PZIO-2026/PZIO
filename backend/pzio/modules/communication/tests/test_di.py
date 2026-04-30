
from pzio.modules.communication.mock import MockEmailService


def test_mock_service_allows_explicit_injection_pattern() -> None:
    email_service = MockEmailService()

    email_service.send_email("user@test.com", "Subject", "Body")

    assert email_service.sent_emails[0]["to"] == "user@test.com"