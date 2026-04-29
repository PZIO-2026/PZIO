from __future__ import annotations

from pzio.modules.communication.base import EmailService


class MockEmailService(EmailService):
    def __init__(self) -> None:
        self.sent_emails: list[dict[str, str]] = []

    def send_email(self, to: str, subject: str, body: str) -> bool:
        self.sent_emails.append(
            {
                "to": to,
                "subject": subject,
                "body": body,
            }
        )
        return True
