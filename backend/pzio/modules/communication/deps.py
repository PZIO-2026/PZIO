"""Communication-module–specific FastAPI dependencies.

Re-exports ``get_current_user`` from the auth module so that routes in this
module can declare a dependency on the authenticated user without importing
from ``pzio.modules.auth.deps`` directly (keeps coupling one-way).
"""

from pzio.modules.auth.deps import get_current_user

__all__ = ["get_current_user"]
