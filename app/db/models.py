from sqlalchemy import BigInteger, Column, DateTime, Text, func

from .base import Base


class Skills(Base):
    """Tabel legacy: primary key dan created_at diisi oleh PostgreSQL."""

    __tablename__ = "skills"

    id = Column(BigInteger, primary_key=True)
    name = Column(Text, nullable=False)
    url = Column(Text, nullable=False)
    description = Column(Text, nullable=False, server_default="''")
    tags = Column(Text, nullable=False, server_default="''")
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
