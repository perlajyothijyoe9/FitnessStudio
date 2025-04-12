from fitness import mongo
from werkzeug.security import generate_password_hash, check_password_hash


class Payment:
    collection = mongo.db.payment

    @classmethod
    def create(cls, data):
        return cls.collection.insert_one(data)

    @classmethod
    def get_all(cls):
        return list(cls.collection.find())

    @classmethod
    def update(cls, payment_id, data):
        return cls.collection.update_one({"_id": payment_id}, {"$set": data})

    @classmethod
    def get_by_id(cls, payment_id):
        return cls.collection.find_one({"_id": payment_id})

    @classmethod
    def delete(cls, payment_id):
        return cls.collection.delete_one({"_id": payment_id})

    @classmethod
    def get_all_by_user_id(cls, user_id):
        return cls.collection.find({"user_id": user_id})

    @classmethod
    def get_latest_payment_record(cls, user_id, membership_id):
        return list(
            cls.collection.find(
                {"membership_id": membership_id, "user_id": user_id},
            )
            .sort("payment_date", -1)
            .limit(1)
        )
