"""
SQLAlchemy models for the persistence layer.
"""
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

from sqlalchemy import JSON, DateTime, ForeignKey, String, Text, Float
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Scan(Base):
    __tablename__ = "scans"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid4()))
    project_name: Mapped[str] = mapped_column(String, index=True)
    status: Mapped[str] = mapped_column(String, default="queued")  # queued, running, complete, failed
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    duration_seconds: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # Summary statistics
    components_count: Mapped[int] = mapped_column(default=0)
    violations_count: Mapped[int] = mapped_column(default=0)
    warnings_count: Mapped[int] = mapped_column(default=0)
    
    # JSON blobs for detailed report and context
    context: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    report: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    
    # Relationships
    components: Mapped[List["Component"]] = relationship(back_populates="scan", cascade="all, delete-orphan")


class Component(Base):
    __tablename__ = "components"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid4()))
    scan_id: Mapped[str] = mapped_column(ForeignKey("scans.id"))
    
    type: Mapped[str] = mapped_column(String)
    name: Mapped[str] = mapped_column(String, index=True)
    version: Mapped[str] = mapped_column(String)
    purl: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    
    license_expression: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    license_confidence: Mapped[float] = mapped_column(Float, default=0.0)
    
    # Policy evaluation result for this component
    policy_status: Mapped[Optional[str]] = mapped_column(String, nullable=True)  # pass, warning, violation
    policy_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # JSON blobs for metadata and evidence
    metadata_: Mapped[Dict[str, Any]] = mapped_column("metadata", JSON, default=dict)
    evidence: Mapped[List[Dict[str, Any]]] = mapped_column(JSON, default=list)

    scan: Mapped["Scan"] = relationship(back_populates="components")
