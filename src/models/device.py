from typing import Optional, List
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.database.db import db


class Device(db.Model):
    __tablename__ = "device"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(unique=True)
    platform: Mapped[str]
    board: Mapped[str]
    wifi_ssid: Mapped[str]
    wifi_password: Mapped[Optional[str]]
    ota_password: Mapped[Optional[str]]
    config_file: Mapped[str] = mapped_column(unique=True)

    components: Mapped[List["Component"]] = relationship(back_populates="device")
