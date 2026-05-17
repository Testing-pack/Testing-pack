from datetime import datetime
from sqlalchemy import String, DateTime, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

class SplitBase(DeclarativeBase):
    pass

class UserAssignment(SplitBase):
    __tablename__ = "user_assignments"
    __table_args__ = (
        UniqueConstraint("test_id", "user_id", name="uq_user_test"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    test_id: Mapped[str] = mapped_column(String, nullable=False)
    user_id: Mapped[str] = mapped_column(String(255), nullable=False)
    variation_id: Mapped[str] = mapped_column(String(50), nullable=False)
    assigned_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)