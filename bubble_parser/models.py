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


class Dosar(Base):
    """
    Get it on
    https://cetatenie.just.ro/stadiu-dosar/#1576832764783-e9f4e574-df23

    1 - nr.dosar
    2 - data ÎNREGISTRĂRII
    3 - termen
    4 - NUMĂR ORDIN
    5 - data ordin
    6 - articul num
    7 - year (from name of pdf)

    """
    
    __tablename__ = "dosars"
    record_id: Mapped[int] = mapped_column(Integer, autoincrement=True, nullable=True)
    num_dosar: Mapped[int] = mapped_column(Integer, nullable=True)
    date: Mapped[datetime] = mapped_column(
        DateTime(timezone=False), nullable=True
    )
    termen: Mapped[datetime] = mapped_column(DateTime(timezone=False), nullable=True)
    numar_ordin: Mapped[str] = mapped_column(VARCHAR(20), nullable=True)
    data_ordin: Mapped[str] = mapped_column(VARCHAR(15), nullable=True)
    raw_dosar: Mapped[str] = mapped_column(VARCHAR(100), primary_key=True)
    articolul_num: Mapped[int] = mapped_column(Integer, primary_key=True)
    year: Mapped[int] = mapped_column(Integer, primary_key=True)
