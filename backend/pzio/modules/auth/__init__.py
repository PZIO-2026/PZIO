from . import models  # noqa: F401  -- ensures SQLAlchemy registers tables on Base.metadata
from .router import router

__all__ = ["router"]
