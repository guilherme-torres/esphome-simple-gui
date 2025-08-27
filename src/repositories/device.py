from src.models.device import Device
from src.repositories.base import BaseRepository


class DeviceRepository(BaseRepository):
    def __init__(self):
        super().__init__(Device)
