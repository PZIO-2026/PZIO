import logging
import smtplib
from email.message import EmailMessage

from pzio.config import Settings
from pzio.modules.communication.base import EmailService

logger = logging.getLogger(__name__)


class SmtpEmailService(EmailService):
    def __init__(self, settings: Settings) -> None:
        if not settings.smtp_user:
            raise ValueError("SMTP_USER is required for SmtpEmailService")
        if not settings.smtp_password:
            raise ValueError("SMTP_PASSWORD is required when SMTP_USER is set")
        if not settings.smtp_host:
            raise ValueError("SMTP_HOST is required when SMTP_USER is set")

        self._host = settings.smtp_host
        self._port = settings.smtp_port
        self._user = settings.smtp_user
        self._password = settings.smtp_password
        self._from = settings.smtp_user
        self._use_tls = settings.smtp_use_tls
        self._use_ssl = settings.smtp_use_ssl
        self._timeout = settings.smtp_timeout

    def send_email(self, to: str, subject: str, body: str) -> bool:
        msg = EmailMessage()
        msg["From"] = self._from
        msg["To"] = to
        msg["Subject"] = subject
        msg.set_content(body)

        try:
            if self._use_ssl:
                smtp_class = smtplib.SMTP_SSL
            else:
                smtp_class = smtplib.SMTP

            with smtp_class(self._host, self._port, timeout=self._timeout) as smtp:
                if self._use_tls and not self._use_ssl:
                    smtp.starttls()
                smtp.login(self._user, self._password)
                smtp.send_message(msg)
            return True
        except (smtplib.SMTPException, OSError):
            logger.exception("Failed to send email to %s", to)
            return False
