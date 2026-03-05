from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid

# modelo base para funcionalidad de sqlalchemy
class Base(DeclarativeBase):
    pass

# tabla jobs (modelo ORM)
class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    repo_url: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, default="queued", nullable=False)
    detail: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    result_path: Mapped[str | None] = mapped_column(String, nullable=True)
    