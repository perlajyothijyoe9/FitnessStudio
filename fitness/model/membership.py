from fitness import mongo
from werkzeug.security import generate_password_hash, check_password_hash


class Membership:
    collection = mongo.db.membership

    @classmethod
    def create(cls, data):
        return cls.collection.insert_one(data)

    @classmethod
    def get_all(cls):
        return list(cls.collection.find())

    @classmethod
    def update(cls, membership_id, data):
        return cls.collection.update_one({"_id": membership_id}, {"$set": data})

    @classmethod
    def get_by_id(cls, membership_id):
        return cls.collection.find_one({"_id": membership_id})

    @classmethod
    def delete(cls, membership_id):
        return cls.collection.delete_one({"_id": membership_id})

