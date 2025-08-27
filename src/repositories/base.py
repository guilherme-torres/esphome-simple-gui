from src.database.db import db


class BaseRepository:
    
    def __init__(self, model):
        self.model = model

    def create(self, data: dict):
        instance = self.model(**data)
        db.session.add(instance)
        db.session.commit()
        return instance

    def get(self, instance_id):
        return db.session.get(self.model, instance_id)

    def list_all(self):
        return db.session.execute(db.select(self.model)).scalars().all()

    def update(self, instance_id, data: dict):
        instance = self.get(instance_id)
        if instance:
            for key, value in data.items():
                setattr(instance, key, value)
            db.session.commit()
        return instance

    def delete(self, instance_id):
        instance = self.get(instance_id)
        if instance:
            db.session.delete(instance)
            db.session.commit()
        return instance

    def filter_by(self, data: dict):
        return db.session.execute(
            db.select(self.model).filter_by(**data)
        ).scalars().all()

    def find_one(self, data: dict):
        return db.session.execute(
            db.select(self.model).filter_by(**data)
        ).scalar_one_or_none()
    
    def create_all(self, data_list: list[dict]):
        instances = []
        for data in data_list:
            instances.append(self.model(**data))
        db.session.add_all(instances)
        db.session.commit()
        return instances
