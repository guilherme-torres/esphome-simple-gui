from typing import Optional
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.database.db import db


class Component(db.Model):
    __tablename__ = "component"

    id: Mapped[int] = mapped_column(primary_key=True)
    component_type: Mapped[str]
    platform: Mapped[str]
    name: Mapped[str]
    pin: Mapped[str]
    config_json: Mapped[str]
    device_id: Mapped[int] = mapped_column(ForeignKey("device.id"))

    device: Mapped["Device"] = relationship(back_populates="components")
