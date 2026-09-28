# Import every model here so Base.metadata is fully populated for Alembic autogenerate.
from app.db.base import Base
from app.models.user import User

__all__ = ["Base", "User"]
