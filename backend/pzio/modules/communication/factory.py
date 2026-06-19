
from pzio.config import settings
from pzio.modules.communication.base import EmailService
from pzio.modules.communication.mock import MockEmailService
from pzio.modules.communication.smtp import SmtpEmailService


def get_email_service() -> EmailService:
    if settings.smtp_user:
        return SmtpEmailService(settings)
    return MockEmailService()
