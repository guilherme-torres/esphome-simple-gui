from src.models.component import Component
from src.repositories.base import BaseRepository


class ComponentRepository(BaseRepository):
    def __init__(self):
        super().__init__(Component)
