# import sqlite3

from typing import List, Optional
from sqlalchemy import create_engine, ForeignKey, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship




'''---
Copy Pasted these
---'''

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "user_account"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(30))
    fullname: Mapped[Optional[str]]

    addresses: Mapped[List["Address"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"User(id={self.id!r}, name={self.name!r}, fullname={self.fullname!r})"


class Address(Base):
    __tablename__ = "address"

    id: Mapped[int] = mapped_column(primary_key=True)
    email_address: Mapped[str]
    user_id: Mapped[int] = mapped_column(ForeignKey("user_account.id"))

    user: Mapped["User"] = relationship(back_populates="addresses")

    def __repr__(self) -> str:
        return (f"Address(id={self.id!r}, email_address={self.email_address!r}") 


connectionPath = 'hexBoy/db/hex_sqlite.db'
connectionString = 'sqlite:///' + connectionPath

engine = create_engine(connectionString, echo=True)
print(type(engine))
