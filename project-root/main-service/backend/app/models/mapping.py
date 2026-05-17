# backend/app/models/mapping.py
from __future__ import annotations
from datetime import datetime
from sqlalchemy import String, Integer, Boolean, Text, ForeignKey, JSON, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from core.database_pgsql import Base

class MappingSchema(Base):
    __tablename__ = "mapping_schemas"
    __table_args__ = {'extend_existing': True}

    mapping_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    experiment_id: Mapped[str | None] = mapped_column(String, ForeignKey("experiments.test_id"))
    mapping_name: Mapped[str] = mapped_column(String, nullable=False)
    file_format: Mapped[str | None] = mapped_column(String)
    description: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    experiment = relationship("Experiment", back_populates="mapping_schemas")
    fields: Mapped[list["MappingField"]] = relationship(
        back_populates="mapping", cascade="all, delete-orphan"
    )


class MappingField(Base):
    __tablename__ = "mapping_fields"
    __table_args__ = {'extend_existing': True}

    mapping_field_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    mapping_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("mapping_schemas.mapping_id", ondelete="CASCADE"), nullable=False
    )
    input_field_name: Mapped[str] = mapped_column(String(255), nullable=False)
    input_field_type: Mapped[str] = mapped_column(String(50), nullable=False)
    target_field: Mapped[str] = mapped_column(String(50), nullable=False)
    transformation_rules: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    mapping = relationship("MappingSchema", back_populates="fields")