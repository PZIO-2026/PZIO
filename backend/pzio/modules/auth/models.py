import enum
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Enum, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from pzio.db import Base


class UserRole(str, enum.Enum):
    """Roles per System Analysis Document §4 (UML class diagram)."""

    GUEST = "Guest"
    TEAM_MEMBER = "TeamMember"
    MANAGER = "Manager"
    ADMINISTRATOR = "Administrator"


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    user_id: Mapped[int] = mapped_column("user_id", Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(254), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column("password_hash", String(255), nullable=False)
    first_name: Mapped[str] = mapped_column("first_name", String(100), nullable=False)
    last_name: Mapped[str] = mapped_column("last_name", String(100), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, native_enum=False, length=20),
        nullable=False,
        default=UserRole.TEAM_MEMBER,
    )
    is_active: Mapped[bool] = mapped_column("is_active", Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        "created_at",
        DateTime(timezone=True),
        nullable=False,
        default=_utcnow,
    )
