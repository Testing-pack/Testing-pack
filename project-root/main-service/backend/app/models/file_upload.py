
from core.database_pgsql import Base
from datetime import datetime
from typing import Optional
from sqlalchemy import String, DateTime, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship


class FileUpload(Base):
    __tablename__ = "file_uploads"
    __table_args__ = {'extend_existing': True}

    upload_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    file_name: Mapped[str] = mapped_column(String, nullable=False)
    file_format: Mapped[Optional[str]] = mapped_column(String)
    s3_path: Mapped[Optional[str]] = mapped_column(String)
    original_hash_sha256: Mapped[Optional[str]] = mapped_column(String)
    verified_hash_sha256: Mapped[Optional[str]] = mapped_column(String)
    file_size_bytes: Mapped[Optional[int]] = mapped_column(Integer)
    upload_status: Mapped[str] = mapped_column(String, default="uploading")
    uploaded_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    experiment_id: Mapped[Optional[str]] = mapped_column(
        ForeignKey("experiments.test_id")
    )
    mapping_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("mapping_schemas.mapping_id", ondelete="SET NULL"),
        nullable=True
    )

    mapping: Mapped[Optional["MappingSchema"]] = relationship()

    # Relationships
    experiment: Mapped[Optional["Experiment"]] = relationship(back_populates="file_uploads")
