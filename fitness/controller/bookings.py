from flask import render_template, request, redirect, url_for, session, flash
from fitness import fitness
from datetime import datetime
from bson.objectid import ObjectId
from flask import jsonify
from fitness.model.classes import Classes
from fitness.model.booking import Booking


@fitness.route("/book_class/<class_id>", methods=["POST"])
def book_class(class_id):
    if request.method == "POST":
        if session.get("user_type") != "user":
            flash("Unauthorized access.", "error")
            return redirect(url_for("login"))

        user_id = session.get("user_id")

        # Retrieve the class details
        class_details = Classes.get_by_id(ObjectId(class_id))
        if not class_details:
            flash("Class not found.", "error")
            return redirect(url_for("get_classes"))

        # Get the booking date from the form
        booking_date = request.form.get("booking_date")
        if not booking_date:
            flash("Please select a booking date.", "error")
            return redirect(url_for("get_classes"))

        # Validate the booking date within class start and end dates
        start_date = class_details["schedule"][
            "start_date"
        ]  # Already a datetime object
        end_date = class_details["schedule"]["end_date"]  # Already a datetime object
        selected_date = datetime.strptime(
            booking_date, "%Y-%m-%d"
        )  # Convert string input to datetime

        if selected_date < start_date or selected_date > end_date:
            flash(
                "Invalid booking date. Please choose a valid date within the class schedule.",
                "error",
            )
            return redirect(url_for("get_classes"))

        # Check if the class on the selected date has reached capacity
        attendees_by_date = class_details.get("attendees", {}).get(booking_date, [])
        if len(attendees_by_date) >= int(class_details["capacity"]):
            flash(
                "Class capacity reached for the selected date. No more bookings allowed.",
                "error",
            )
            return redirect(url_for("get_classes"))

        try:
            # Proceed with creating the booking
            booking_data = {
                "user_id": user_id,
                "class_id": class_id,
                "booking_date": booking_date,
                "status": "Pending",
                "special_requests": request.form.get("special_requests", ""),
                "created_at": datetime.now(),
            }
            new_booking_id = Booking.create(booking_data)

            # Update the class attendees for the specific booking date
            attendee_entry = {"user_id": user_id, "status": "Pending"}
            Classes.add_attendee(ObjectId(class_id), booking_date, attendee_entry)

            flash("Booking request sent!", "success")
            return redirect(url_for("user_dashboard"))

        except Exception as e:
            flash(f"An error occurred: {str(e)}", "error")
            return redirect(url_for("get_classes"))


@fitness.route("/cancel_booking/<booking_id>", methods=["POST"])
def cancel_booking(booking_id):
    if session.get("user_type") != "user":
        flash("Unauthorized access.", "error")
        return redirect(url_for("login"))

    user_id = session.get("user_id")

    # Retrieve booking details
    booking = Booking.get_by_id(ObjectId(booking_id))
    if not booking or booking["user_id"] != user_id:
        flash("Booking not found or unauthorized access.", "error")
        return redirect(url_for("get_user_bookings"))

    # Retrieve class details
    class_details = Classes.get_by_id(ObjectId(booking["class_id"]))
    if not class_details:
        flash("Class not found.", "error")
        return redirect(url_for("get_user_bookings"))

    booking_date = booking["booking_date"]

    # Check if the booking date has passed
    selected_date = datetime.strptime(booking_date, "%Y-%m-%d")
    if datetime.now().date() > selected_date.date():
        flash("Cannot cancel booking for past dates.", "error")
        return redirect(url_for("get_user_bookings"))

    try:
        # Update the booking status to 'Cancelled'
        Booking.update_status(ObjectId(booking_id), "Cancelled")

        # Remove the user from the class's attendees list for the specific booking date
        attendees_by_date = class_details.get("attendees", {}).get(booking_date, [])
        updated_attendees = [
            attendee for attendee in attendees_by_date if attendee["user_id"] != user_id
        ]
        Classes.update_attendees_by_date(
            ObjectId(booking["class_id"]), booking_date, updated_attendees
        )

        flash("Booking successfully cancelled.", "success")
        return redirect(url_for("get_user_bookings"))

    except Exception as e:
        flash(f"An error occurred while cancelling the booking: {str(e)}", "error")
        return redirect(url_for("get_user_bookings"))
