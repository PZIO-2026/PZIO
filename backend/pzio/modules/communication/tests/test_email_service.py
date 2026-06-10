
import smtplib
from unittest.mock import MagicMock, patch

import pytest

from pzio.config import Settings
from pzio.modules.communication import factory
from pzio.modules.communication.base import EmailService
from pzio.modules.communication.factory import get_email_service
from pzio.modules.communication.mock import MockEmailService
from pzio.modules.communication.smtp import SmtpEmailService


def _smtp_settings(**overrides: object) -> Settings:
    defaults = {
        "smtp_host": "smtp.example.com",
        "smtp_port": 587,
        "smtp_user": "sender@example.com",
        "smtp_password": "secret",
        "smtp_use_tls": True,
        "smtp_use_ssl": False,
        "smtp_timeout": 30,
    }
    defaults.update(overrides)
    return Settings(**defaults)


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


def test_email_service_base_raises() -> None:
    with pytest.raises(NotImplementedError):
        EmailService().send_email("user@test.com", "Subject", "Body")


def test_get_email_service_returns_mock_when_smtp_user_unset(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(factory, "settings", Settings(smtp_host=None, smtp_user=None, smtp_password=None))

    service = get_email_service()

    assert isinstance(service, MockEmailService)


def test_get_email_service_returns_smtp_when_smtp_user_set(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(factory, "settings", _smtp_settings())

    service = get_email_service()

    assert isinstance(service, SmtpEmailService)


@pytest.mark.parametrize(
    "missing_field",
    ["smtp_user", "smtp_password", "smtp_host"],
)
def test_smtp_email_service_requires_credentials(missing_field: str) -> None:
    kwargs = {
        "smtp_host": "smtp.example.com",
        "smtp_user": "sender@example.com",
        "smtp_password": "secret",
    }
    kwargs[missing_field] = None

    with pytest.raises(ValueError):
        SmtpEmailService(Settings(**kwargs))


def test_smtp_email_service_send_success() -> None:
    service = SmtpEmailService(_smtp_settings())
    mock_smtp = MagicMock()
    mock_smtp.__enter__ = MagicMock(return_value=mock_smtp)
    mock_smtp.__exit__ = MagicMock(return_value=False)

    with patch("pzio.modules.communication.smtp.smtplib.SMTP", return_value=mock_smtp):
        result = service.send_email("user@test.com", "Hello", "Body")

    assert result is True
    mock_smtp.starttls.assert_called_once()
    mock_smtp.login.assert_called_once_with("sender@example.com", "secret")
    mock_smtp.send_message.assert_called_once()
    sent = mock_smtp.send_message.call_args[0][0]
    assert sent["From"] == "sender@example.com"
    assert sent["To"] == "user@test.com"
    assert sent["Subject"] == "Hello"
    assert sent.get_content().strip() == "Body"


def test_smtp_email_service_send_failure_returns_false() -> None:
    service = SmtpEmailService(_smtp_settings())
    mock_smtp = MagicMock()
    mock_smtp.__enter__ = MagicMock(return_value=mock_smtp)
    mock_smtp.__exit__ = MagicMock(return_value=False)
    mock_smtp.login.side_effect = smtplib.SMTPAuthenticationError(535, b"Auth failed")

    with patch("pzio.modules.communication.smtp.smtplib.SMTP", return_value=mock_smtp):
        result = service.send_email("user@test.com", "Hello", "Body")

    assert result is False


def test_smtp_email_service_uses_ssl_when_configured() -> None:
    service = SmtpEmailService(_smtp_settings(smtp_use_ssl=True, smtp_use_tls=False))
    mock_smtp = MagicMock()
    mock_smtp.__enter__ = MagicMock(return_value=mock_smtp)
    mock_smtp.__exit__ = MagicMock(return_value=False)

    with patch("pzio.modules.communication.smtp.smtplib.SMTP_SSL", return_value=mock_smtp) as smtp_ssl:
        result = service.send_email("user@test.com", "Hello", "Body")

    assert result is True
    smtp_ssl.assert_called_once_with("smtp.example.com", 587, timeout=30)
    mock_smtp.starttls.assert_not_called()
