from fitness import mongo
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash


class Booking:
    collection = mongo.db.booking

    @classmethod
    def create(cls, data):
        return cls.collection.insert_one(data)

    @classmethod
    def get_all(cls):
        return list(cls.collection.find())

    @classmethod
    def update(cls, booking_id, data):
        return cls.collection.update_one({"_id": booking_id}, {"$set": data})

    @classmethod
    def get_by_id(cls, booking_id):
        return cls.collection.find_one({"_id": booking_id})

    @classmethod
    def delete(cls, booking_id):
        return cls.collection.delete_one({"_id": booking_id})

    @classmethod
    def get_active_by_user_id(cls, user_id):
        # Get today's date as a string in the format YYYY-MM-DD
        today_date = datetime.now().strftime("%Y-%m-%d")

        # Query for active bookings
        return list(
            cls.collection.find(
                {
                    "user_id": user_id,
                    "status": {"$in": ["Confirmed", "Pending"]},
                    "$expr": {
                        "$gte": [
                            {
                                "$dateFromString": {
                                    "dateString": "$booking_date",
                                    "format": "%Y-%m-%d",
                                }
                            },
                            {
                                "$dateFromString": {
                                    "dateString": today_date,
                                    "format": "%Y-%m-%d",
                                }
                            },
                        ]
                    },
                }
            )
        )

    @classmethod
    def get_past_by_user_id(cls, user_id):
        # Get today's date in the format YYYY-MM-DD
        today_date = datetime.now().strftime("%Y-%m-%d")

        return list(
            cls.collection.find(
                {
                    "user_id": user_id,
                    "$expr": {
                        "$lt": [
                            {
                                "$dateFromString": {
                                    "dateString": "$booking_date",
                                    "format": "%Y-%m-%d",
                                }
                            },
                            {
                                "$dateFromString": {
                                    "dateString": today_date,
                                    "format": "%Y-%m-%d",
                                }
                            },
                        ]
                    },
                }
            )
        )

    @classmethod
    def get_pending_by_class_id(cls, class_id):
        return cls.collection.find({"status": "Pending", "class_id": class_id})

    @classmethod
    def update_status(cls, booking_id, status):
        cls.collection.update_one({"_id": booking_id}, {"$set": {"status": status}})
