from fitness import mongo
from werkzeug.security import generate_password_hash, check_password_hash
from bson.objectid import ObjectId


class User:
    collection = mongo.db.user

    @classmethod
    def create(cls, data):
        return cls.collection.insert_one(data)

    @classmethod
    def get_all(cls):
        return list(cls.collection.find())

    @classmethod
    def update(cls, user_id, data):
        return cls.collection.update_one({"_id": user_id}, {"$set": data})

    @classmethod
    def get_by_id(cls, user_id):
        return cls.collection.find_one({"_id": user_id})

    @classmethod
    def delete(cls, user_id):
        return cls.collection.delete_one({"_id": user_id})

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
    def update_membership_id(cls, user_id, membership_id):
        return cls.collection.update_one(
            {"_id": ObjectId(user_id)}, {"$set": {"membership_id": membership_id}}
        )

    @classmethod
    def update_password(cls, user_id, new_password):
        cls.collection.update_one(
            {"_id": ObjectId(user_id)}, {"$set": {"password": new_password}}
        )

    @classmethod
    def update_field(cls, user_id, fields):
        cls.collection.update_one({"_id": ObjectId(user_id)}, {"$set": fields})
