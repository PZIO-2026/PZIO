"""Communication-module FastAPI dependencies.

Keeps the existing authenticated-user dependency available for communication
routes, and also exposes the email-service factory for future notification use.
"""

from pzio.modules.auth.deps import get_current_user
from pzio.modules.communication.base import EmailService
from pzio.modules.communication.factory import get_email_service


def provide_email_service() -> EmailService:
    return get_email_service()


__all__ = ["get_current_user", "provide_email_service"]
