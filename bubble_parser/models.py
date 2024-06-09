from datetime import datetime

from sqlalchemy import VARCHAR, DateTime, Integer
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Articolul(Base):
    """Articolul entity, in articolul url stores pdfs."""

    __tablename__ = "articoluls"
    articolul_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    number: Mapped[int] = mapped_column(Integer)
    url: Mapped[str] = mapped_column(VARCHAR(150), nullable=True)


class ArticolulPDF(Base):
    """PDF articolul."""

    __tablename__ = "pdfs"
    pdf_id: Mapped[int] = mapped_column(
        Integer, primary_key=False, autoincrement=True, nullable=True
    )
    articolul_num: Mapped[int] = mapped_column(Integer)
    list_name: Mapped[str] = mapped_column(VARCHAR(15), primary_key=True)
    number_order: Mapped[str] = mapped_column(VARCHAR(150), primary_key=True)
    date: Mapped[datetime] = mapped_column(DateTime(timezone=False))
    year: Mapped[int] = mapped_column(Integer, primary_key=True)
    url: Mapped[str] = mapped_column(VARCHAR(150))
    parsed_at: Mapped[int] = mapped_column(Integer)
