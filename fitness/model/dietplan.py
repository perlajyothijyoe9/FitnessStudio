from fitness import mongo
from werkzeug.security import generate_password_hash, check_password_hash


class DietPlan:
    collection = mongo.db.dietplan

    @classmethod
    def create(cls, data):
        return cls.collection.insert_one(data)

    @classmethod
    def get_all(cls):
        return list(cls.collection.find())

    @classmethod
    def update(cls, dietplan_id, data):
        return cls.collection.update_one({"_id": dietplan_id}, {"$set": data})

    @classmethod
    def get_by_id(cls, dietplan_id):
        return cls.collection.find_one({"_id": dietplan_id})

    @classmethod
    def delete(cls, dietplan_id):
        return cls.collection.delete_one({"_id": dietplan_id})
