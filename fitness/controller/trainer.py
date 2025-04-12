from flask import render_template, request, redirect, url_for, session, flash
from fitness import fitness
import logging
from datetime import datetime, timedelta
from bson.objectid import ObjectId
from flask import jsonify
from fitness.model.user import User
from fitness.model.membership import Membership
from fitness.model.dietplan import DietPlan
from fitness.model.booking import Booking
from fitness.model.classes import Classes
from fitness.model.trainer import Trainer
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Edit Trainer
@fitness.route("/edit_trainer/<trainer_id>", methods=["GET", "POST"])
def edit_trainer(trainer_id):
    trainer = Trainer.get_by_id(ObjectId(trainer_id))
    if not trainer:
        flash("Trainer not found.", "error")
        return redirect(url_for("admin_dashboard"))

    if request.method == "POST":
        updated_data = {
            "firstname": request.form.get("firstname"),
            "lastname": request.form.get("lastname"),
            "email": request.form.get("email"),
            "phone_number": request.form.get("phone_number"),
            "city": request.form.get("city"),
            "zipcode": request.form.get("zipcode"),
            "ssn": request.form.get("ssn"),
            "expertise": request.form.get("expertise"),
            "experience": request.form.get("experience", type=int),
        }

        try:
            # Update trainer details in the database
            Trainer.update(ObjectId(trainer_id), updated_data)
            flash("Trainer updated successfully!", "success")
            return redirect(url_for("admin_dashboard"))
        except Exception as e:
            flash(f"An error occurred while updating trainer: {e}", "error")
            return redirect(url_for("edit_trainer", trainer_id=trainer_id))

    return render_template("trainer/edit_trainer.html", trainer=trainer)


@fitness.route("/view_attendees/<class_id>")
def view_attendees(class_id):
    booking_date = request.args.get(
        "date", ""
    ).strip()  # Get date from query or empty string
    if not booking_date:  # Default to today's date if not provided
        booking_date = datetime.now().strftime("%Y-%m-%d")

    class_info = Classes.get_by_id(ObjectId(class_id))
    print(f"------Booking date {booking_date}")

    if class_info and "attendees" in class_info:
        # Convert the booking_date string to datetime.date for comparison
        # booking_date_obj = datetime.strptime(booking_date, "%Y-%m-%d").date()

        # Get attendees for the specific booking_date
        attendees_by_date = class_info.get("attendees", {}).get(booking_date, [])
        attendees_list = []

        for attendee in attendees_by_date:
            user = User.get_by_id(ObjectId(attendee["user_id"]))
            if user:  # Check if the user exists
                attendees_list.append(
                    {
                        "_id": user["_id"],
                        "username": user["username"],
                        "attendance_status": attendee["status"],
                    }
                )

        return render_template(
            "trainer/view_attendees.html",
            class_data=class_info,
            attendees=attendees_list,
            booking_date=booking_date,
        )
    else:
        flash(
            "Class not found or no attendees available for the selected date.", "error"
        )
        return redirect(url_for("trainer_dashboard"))


@fitness.route("/view_attendee_details/<user_id>")
def view_attendee_details(user_id):
    user = User.get_by_id(ObjectId(user_id))
    return render_template("trainer/attendee_details.html", user=user)


@fitness.route("/add_class", methods=["GET", "POST"])
def add_class():
    if request.method == "POST":
        try:
            # Extract form data
            start_date = datetime.strptime(request.form["start_date"], "%Y-%m-%d")
            end_date = datetime.strptime(request.form["end_date"], "%Y-%m-%d")
            time_range = request.form["time"]  # Time range (e.g., "07:00-08:00")

            # Prepare class data
            class_data = {
                "name": request.form["name"],
                "category": request.form["category"],
                "capacity": int(request.form["capacity"]),
                "schedule": {
                    "trainer_id": session.get("user_id"),
                    "start_date": start_date,
                    "end_date": end_date,
                    "time": time_range,  # Store the time range as is
                    "venue": request.form["venue"],
                },
            }

            # Create the class
            new_class = Classes.create(class_data)

            # Update trainer's schedule
            schedule = {
                "class_id": new_class.inserted_id,
                "start_date": request.form["start_date"],
                "end_date": request.form["end_date"],
                "time": time_range,  # Store the time range as is
            }
            Trainer.update_schedule(ObjectId(session["user_id"]), schedule)

            return redirect(url_for("trainer_dashboard"))

        except Exception as e:
            # Handle errors
            flash(f"An error occurred: {str(e)}", "error")
            return redirect(url_for("add_class"))

    return render_template("classes/add_class.html")


@fitness.route("/edit_class/<class_id>", methods=["GET", "POST"])
def edit_class(class_id):
    existing_class = Classes.get_by_id(ObjectId(class_id))
    if not existing_class:
        flash("Class not found.", "error")
        return redirect(url_for("trainer_dashboard"))

    if request.method == "POST":
        try:
            # Retrieve and process form data
            start_date_obj = datetime.strptime(request.form["start_date"], "%Y-%m-%d")
            end_date_obj = datetime.strptime(request.form["end_date"], "%Y-%m-%d")

            # Preserve existing attendees
            attendees = existing_class.get("attendees", {})

            # Prepare updated class data
            class_data = {
                "name": request.form["name"],
                "category": request.form["category"],
                "capacity": request.form["capacity"],
                "schedule": {
                    "trainer_id": session.get("user_id"),
                    "start_date": start_date_obj,
                    "end_date": end_date_obj,
                    "time": request.form["time"],
                    "venue": request.form["venue"],
                },
                "attendees": attendees,
            }

            # Update the class in the database
            Classes.update(ObjectId(class_id), class_data)

            # Update the trainer's schedule (if necessary)
            Trainer.update_schedule(session["user_id"], class_data["schedule"])

            flash("Class updated successfully.", "success")
            return redirect(url_for("trainer_dashboard"))
        except Exception as e:
            flash(f"An error occurred while updating the class: {str(e)}", "error")
            return redirect(url_for("edit_class", class_id=class_id))

    return render_template("classes/edit_class.html", class_data=existing_class)


@fitness.route("/delete_class/<class_id>", methods=["POST"])
def delete_class(class_id):
    if request.method == "POST":
        Classes.delete(ObjectId(class_id))
        Trainer.remove_class_from_schedule(session["user_id"], class_id)
        return redirect(url_for("trainer_dashboard"))


@fitness.route("/confirm_booking/<booking_id>", methods=["POST"])
def confirm_booking(booking_id):
    Booking.update_status(ObjectId(booking_id), "Confirmed")
    return redirect(url_for("trainer_dashboard"))
