
from core.database_pgsql import Base
from datetime import datetime
from typing import Optional, List
from sqlalchemy import String, Text, DateTime, Integer, Float, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
import uuid
from sqlalchemy.dialects.postgresql import JSON



class Experiment(Base):
    __tablename__ = "experiments"
    __table_args__ = {'extend_existing': True}

    test_id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4())[:8])
    test_name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    owner: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, default="draft")
    start_date: Mapped[Optional[datetime]] = mapped_column(DateTime)
    end_date: Mapped[Optional[datetime]] = mapped_column(DateTime)
    planned_duration_days: Mapped[Optional[int]] = mapped_column(Integer)
    significance_level: Mapped[float] = mapped_column(Float, default=0.05)
    mde: Mapped[Optional[float]] = mapped_column(Float)
    power: Mapped[float] = mapped_column(Float, default=0.8)
    expected_daily_users: Mapped[int] = mapped_column(Integer, default=1000)

    # --- Гипотеза ---
    hypothesis_change_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    hypothesis_expected_impact: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    hypothesis_measurement_method: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    hypothesis_h0: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    hypothesis_h1: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # --- Источник данных ---
    source_type: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    source_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    source_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    source_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    source_platform: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    source_contact_person: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    source_additional_info: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # --- Статистические расчёты ---
    sample_size_control: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    sample_size_treatment: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    sample_size_total: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    days_needed: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)


    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    # Relationships
    variations: Mapped[List["ExperimentVariation"]] = relationship(
        back_populates="experiment",
        cascade="all, delete-orphan"
    )
    metrics: Mapped[List["ExperimentMetric"]] = relationship(
        back_populates="experiment",
        cascade="all, delete-orphan"
    )
    file_uploads: Mapped[List["FileUpload"]] = relationship(
        back_populates="experiment"
    )
    mapping_schemas: Mapped[List["MappingSchema"]] = relationship(
        back_populates="experiment"
    )


class ExperimentVariation(Base):
    __tablename__ = "experiment_variations"
    __table_args__ = {'extend_existing': True}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    test_id: Mapped[str] = mapped_column(
        ForeignKey("experiments.test_id", ondelete="CASCADE")
    )
    variation_id: Mapped[Optional[str]] = mapped_column(String)
    name: Mapped[str] = mapped_column(String, nullable=False)
    traffic_percentage: Mapped[float] = mapped_column(Float, nullable=False)

    # Relationships
    experiment: Mapped["Experiment"] = relationship(back_populates="variations")


class ExperimentMetric(Base):
    __tablename__ = "experiment_metrics"
    __table_args__ = {'extend_existing': True}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    test_id: Mapped[str] = mapped_column(
        ForeignKey("experiments.test_id", ondelete="CASCADE")
    )
    metric_id: Mapped[Optional[str]] = mapped_column(String)
    purpose: Mapped[Optional[str]] = mapped_column(String)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    baseline_value: Mapped[float] = mapped_column(Float, default=0.0)
    sql_query: Mapped[Optional[str]] = mapped_column(Text)

    distribution: Mapped[Optional[str]] = mapped_column(String, default="unknown")
    variance_assumption: Mapped[Optional[str]] = mapped_column(String, default="unknown")
    outliers: Mapped[Optional[str]] = mapped_column(String, default="insignificant")

    statistical_type: Mapped[str] = mapped_column(String, nullable=False, default="proportion")
    variance_estimate: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    # Relationships
    experiment: Mapped["Experiment"] = relationship(back_populates="metrics")
    recommended_test: Mapped[Optional[str]] = mapped_column(String, nullable=True)
