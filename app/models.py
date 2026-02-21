from sqlalchemy import Column, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship

from app.database import Base


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    template_name = Column(String(255), nullable=False)

    sheets = relationship("ProjectSheet", back_populates="project", cascade="all, delete-orphan")


class ProjectSheet(Base):
    __tablename__ = "project_sheets"
    __table_args__ = (UniqueConstraint("project_id", "display_order", name="uq_project_sheet_project_display_order"),)

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    display_order = Column(Integer, nullable=False)
    name = Column(String(255), nullable=False)
    header_row = Column(Integer, nullable=False)

    project = relationship("Project", back_populates="sheets")
    rows = relationship("ProjectRow", back_populates="sheet", cascade="all, delete-orphan")


class ProjectRow(Base):
    __tablename__ = "project_rows"
    __table_args__ = (UniqueConstraint("project_id", "display_order", name="uq_project_row_project_display_order"),)

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    sheet_id = Column(Integer, ForeignKey("project_sheets.id", ondelete="CASCADE"), nullable=False, index=True)
    display_order = Column(Integer, nullable=False)
    row_offset = Column(Integer, nullable=False)
    values = Column(Text, nullable=False)

    sheet = relationship("ProjectSheet", back_populates="rows")
