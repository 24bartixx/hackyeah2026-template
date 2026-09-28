from sqlalchemy import Identity, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class User(Base):
    # "user" is a reserved word in PostgreSQL, hence the plural table name
    __tablename__ = "users"

    user_id: Mapped[int] = mapped_column(Identity(always=True), primary_key=True)
    first_name: Mapped[str] = mapped_column(String(100))
    last_name: Mapped[str] = mapped_column(String(100))
    # Stored lower-cased so lookups and the unique constraint are case-insensitive
    email: Mapped[str] = mapped_column(String(320), unique=True)
    # Argon2id encoded hash (PHC string format)
    password_hash: Mapped[str] = mapped_column(String(255))
    # Hex-encoded random per-user salt used for the Argon2 hash
    salt: Mapped[str] = mapped_column(String(64))

    def __repr__(self) -> str:
        return (
            f"User(user_id={self.user_id!r}, email={self.email!r}, "
            f"first_name={self.first_name!r}, last_name={self.last_name!r})"
        )
