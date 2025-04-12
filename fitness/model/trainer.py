from fitness import mongo
from werkzeug.security import generate_password_hash, check_password_hash


class Trainer:
    collection = mongo.db.trainer

    @classmethod
    def create(cls, data):
        return cls.collection.insert_one(data)

    @classmethod
    def get_all(cls):
        return list(cls.collection.find())

    @classmethod
    def update(cls, trainer_id, data):
        return cls.collection.update_one({"_id": trainer_id}, {"$set": data})

    @classmethod
    def get_by_id(cls, trainer_id):
        return cls.collection.find_one({"_id": trainer_id})

    @classmethod
    def delete(cls, trainer_id):
        return cls.collection.delete_one({"_id": trainer_id})

    @classmethod
    def get_by_email(cls, email):
        return cls.collection.find_one({"email": email})

    @classmethod
    def check_password(cls, admin, password):
        return check_password_hash(admin["password"], password)

    @classmethod
    def exists_by_email(cls, email):
        return cls.collection.find_one({"email": email}) is not None

    @classmethod
    def update_schedule(cls, trainer_id, schedule):
        cls.collection.update_one(
            {"_id": trainer_id}, {"$push": {"schedule": schedule}}
        )

    @classmethod
    def remove_class_from_schedule(cls, trainer_id, class_id):
        cls.collection.update_one(
            {"_id": trainer_id},
            {"$pull": {"schedule": {"class_id": class_id}}},
        )

    @classmethod
    def update_password(cls, trainer_id, new_password):
        cls.collection.update_one(
            {"_id": trainer_id}, {"$set": {"password": new_password}}
        )

    @classmethod
    def update_field(cls, trainer_id, fields):
        cls.collection.update_one({"_id": trainer_id}, {"$set": fields})
