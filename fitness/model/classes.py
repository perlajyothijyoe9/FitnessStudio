from fitness import mongo
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash


class Classes:
    collection = mongo.db.classes

    @classmethod
    def create(cls, data):
        return cls.collection.insert_one(data)

    @classmethod
    def get_all(cls):
        return list(cls.collection.find())

    @classmethod
    def update(cls, class_id, data):
        return cls.collection.update_one({"_id": class_id}, {"$set": data})

    @classmethod
    def get_by_id(cls, class_id):
        return cls.collection.find_one({"_id": class_id})

    @classmethod
    def delete(cls, class_id):
        return cls.collection.delete_one({"_id": class_id})

    @classmethod
    def get_upcoming_classes(cls):
        current_date = datetime.now()
        return list(cls.collection.find({"schedule.start_date": {"$gt": current_date}}))

    @classmethod
    def get_by_trainer_id(cls, trainer_id):
        print(f"-------->{trainer_id}")
        print(type(trainer_id))
        classes = list(cls.collection.find({"schedule.trainer_id": trainer_id}))
        return classes

    @classmethod
    def get_by_query(cls, query):
        print("Executing query:", query)
        results = list(cls.collection.find(query))
        print("Query results:", results)
        return results

    @classmethod
    def update_attendees(cls, class_id, attendees):
        cls.collection.update_one(
            {"_id": class_id}, {"$push": {"attendees": attendees}}
        )

    @classmethod
    def modify_attendees(cls, class_id, attendees):
        cls.collection.update_one({"_id": class_id}, {"$set": {"attendees": attendees}})

    @classmethod
    def add_attendee(cls, class_id, booking_date, attendee_entry):
        """
        Add an attendee for a specific booking date.
        If the date does not exist, initialize the attendee list for that date.
        """

        cls.collection.update_one(
            {"_id": class_id, f"attendees.{booking_date}": {"$exists": False}},
            {"$set": {f"attendees.{booking_date}": []}},
        )

        # Push the attendee entry to the list for the specific date
        cls.collection.update_one(
            {"_id": class_id}, {"$push": {f"attendees.{booking_date}": attendee_entry}}
        )

    @classmethod
    def update_attendees_by_date(cls, class_id, booking_date, updated_attendees):
        """
        Update attendees for a specific booking date.
        This is typically used to remove an attendee or modify the list.
        """
        cls.collection.update_one(
            {"_id": class_id},
            {"$set": {f"attendees.{booking_date}": updated_attendees}},
        )
