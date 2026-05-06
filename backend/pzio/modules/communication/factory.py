
from pzio.modules.communication.base import EmailService
from pzio.modules.communication.mock import MockEmailService


def get_email_service() -> EmailService:
    #in the future we could easily swap between different providers here for now - just this scaffolding
    return MockEmailService()
