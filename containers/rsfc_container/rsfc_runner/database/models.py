from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String
from sqlalchemy.dialects.postgresql import JSONB

# modelo base para funcionalidad de sqlalchemy
class Base(DeclarativeBase):
    pass

# tabla jobs (modelo ORM)
class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    target: Mapped[str] = mapped_column(String, nullable=False)
    repo_url: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, default="queued", nullable=False)
    detail: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    result_path: Mapped[str | None] = mapped_column(String, nullable=True)
    