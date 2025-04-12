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
from fitness.model.payment import Payment

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@fitness.route("/user_signup", methods=("GET", "POST"))
def user_signup():
    if request.method == "POST":
        try:
            username = request.form.get("username").strip()
            email = request.form.get("email").strip()
            password = request.form.get("password").strip()
            confirm_password = request.form.get("confirm_password").strip()
            phone_number = request.form.get("phone_number").strip()
            height = request.form.get("height").strip()
            weight = request.form.get("weight").strip()
            goal_weight = request.form.get("goal_weight").strip()
            previous_health_issues = request.form.get("previous_health_issues").strip()

            # Check if password matches
            if password != confirm_password:
                flash("Passwords do not match.", "error")
                return redirect(url_for("user_signup"))

            if User.exists_by_email(email):
                flash("User already registered", "error")
                return redirect(url_for("login"))

            data = {
                "username": username,
                "email": email,
                "password": password,
                "phone_number": phone_number,
                "height": height,
                "weight": weight,
                "goal_weight": goal_weight,
                "previous_health_issues": previous_health_issues,
            }

            # Create a User record
            User.create(data)
            flash("User registered successfully!", "success")
            return redirect(url_for("login"))
        except Exception as e:
            logger.error(f"Error occured during User registration: {str(e)}")
            return "Internal Server Error", 500

    return render_template("user/signup.html")


@fitness.route("/user_membership")
def get_user_memberships():
    if session.get("user_type") != "user":
        flash("Unauthorized access.", "error")
        return redirect(url_for("login"))

    user_id = session.get("user_id")
    user = User.get_by_id(user_id)

    # Check if user has a membership
    if user is None or not user.get("membership_id"):
        # User is new or has no membership
        flash("You currently do not have an active membership.")
        memberships = (
            Membership.get_all()
        )  # Assuming this method returns all membership options
        return render_template("user/memberships.html", memberships=memberships)

    # Fetch the user's membership
    membership = Membership.get_by_id(str(user["membership_id"]))
    # Fetch the last payment record for this membership
    last_payment = Payment.get_last_payment_by_user(user_id, membership["_id"])

    payment_date = last_payment["payment_date"]
    validity_period_days = (
        membership["validity_period"] * 30
    )  # For example, 1 month = 30 days
    expiration_date = payment_date + timedelta(days=validity_period_days)

    # Check if the membership is active based on its validity period
    if expiration_date >= datetime.now():
        # Membership is active
        dietplan = DietPlan.get_by_id(str(membership.get("diet_plan_id")))
        membership["diet_plan"] = dietplan
        return render_template("user/active_membership.html", membership=membership)

    # If membership is expired or invalid
    flash("Your membership has expired or is inactive.")
    return redirect(
        url_for("user/renew_membership_page.html")
    )  # Redirect to renewal or upgrade page


# @fitness.route("/user_active_bookings")
# def get_user_active_bookings():
#     if session.get("user_type") != "user":
#         flash("Unauthorized access.", "error")
#         return redirect(url_for("login"))

#     user_id = session.get("user_id")

#     # Find an active booking for the user with "Confirmed" status and a future or current date
#     active_bookings = Booking.get_active_by_user_id(user_id)

#     if not active_bookings:
#         # No active booking found, redirect to booking page or info page
#         flash("You do not have any active bookings.")
#         return redirect(url_for("booking_info_page"))

#     # Fetch class details for each active booking
#     bookings_with_class_info = []
#     for booking in active_bookings:
#         class_info = Classes.get_by_id(str(booking["class_id"]))
#         bookings_with_class_info.append({"booking": booking, "class_info": class_info})

#     return render_template(
#         "user/active_bookings.html", bookings=bookings_with_class_info
#     )


# @fitness.route("/user_previous_bookings")
# def get_user_past_bookings():
#     if session.get("user_type") != "user":
#         flash("Unauthorized access.", "error")
#         return redirect(url_for("login"))

#     user_id = session.get("user_id")
#     # Find past bookings for the user (any status) with a date before today
#     past_bookings = Booking.get_past_by_user_id(user_id)

#     # Prepare booking details, including class information
#     bookings_with_class_info = []
#     for booking in past_bookings:
#         class_info = Classes.get_by_id(str(booking["class_id"]))
#         if class_info:
#             bookings_with_class_info.append(
#                 {"booking": booking, "class_info": class_info}
#             )
#         else:
#             bookings_with_class_info.append({"booking": booking, "class_info": None})

#     return render_template("user/past_bookings.html", bookings=bookings_with_class_info)


@fitness.route("/user_bookings")
def get_user_bookings():
    if session.get("user_type") != "user":
        flash("Unauthorized access.", "error")
        return redirect(url_for("login"))

    user_id = session.get("user_id")

    # Get active bookings (Confirmed and Pending for today or future dates)
    active_bookings = Booking.get_active_by_user_id(user_id)
    print(f"active---------->{active_bookings}")
    active_bookings_with_class_info = []
    if active_bookings:
        for booking in active_bookings:
            class_info = Classes.get_by_id(ObjectId(booking["class_id"]))
            booking_date = booking["booking_date"]

            if class_info:
                # Check status from attendees grouped by booking date
                attendees_by_date = class_info.get("attendees", {}).get(
                    booking_date, []
                )
                for attendee in attendees_by_date:
                    booking["status"] = (
                        "Attended"
                        if attendee["user_id"] == user_id
                        and attendee["status"] == "Attended"
                        else booking["status"]
                    )

                active_bookings_with_class_info.append(
                    {"booking": booking, "class_info": class_info}
                )

    # Get past bookings (any status with date in the past)
    past_bookings = Booking.get_past_by_user_id(user_id)
    past_bookings_with_class_info = []
    if past_bookings:
        for booking in past_bookings:
            booking_date = booking["booking_date"]
            class_info = Classes.get_by_id(ObjectId(booking["class_id"]))

            past_bookings_with_class_info.append(
                {"booking": booking, "class_info": class_info if class_info else None}
            )

    return render_template(
        "user/active_past_bookings.html",
        active_bookings=active_bookings_with_class_info,
        past_bookings=past_bookings_with_class_info,
        today=datetime.now().date(),
    )


@fitness.route("/record_attendance", methods=["POST"])
def record_attendance():
    booking_id = request.json.get("booking_id")
    user_id = session.get("user_id")
    booking = Booking.get_by_id(ObjectId(booking_id))
    class_document = Classes.get_by_id(ObjectId(booking["class_id"]))

    # Logic to record attendance for the specific booking date
    try:
        if class_document and booking:
            print("1-------> In line")
            booking_date = booking["booking_date"]
            print(f"bokking_dateeeeeeeeee->>>>>>>{booking_date}")
            attendees_by_date = class_document.get("attendees", {}).get(
                booking_date, []
            )
            print(f"attendeddddsssss->>>>>>>>>>>{attendees_by_date}")

            # Find the attendee with the matching user_id
            attendee_found = False
            for attendee in attendees_by_date:
                print(f"attendee------->{attendee}")
                if attendee.get("user_id") == user_id:
                    attendee["status"] = "Attended"
                    attendee_found = True
                    break

            if not attendee_found:
                print(f"attendee Not found!!")
                return (
                    jsonify(
                        {
                            "status": "error",
                            "message": "No booking found for the specified date",
                        }
                    ),
                    400,
                )

            # Update the attendees for the specific booking date
            Classes.update_attendees_by_date(
                ObjectId(booking["class_id"]), booking_date, attendees_by_date
            )

            return (
                jsonify(
                    {"status": "success", "message": "Attendance recorded successfully"}
                ),
                200,
            )
        else:
            return (
                jsonify({"status": "error", "message": "Booking or class not found"}),
                400,
            )
    except Exception as e:
        print(f"Error recording attendance: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500


@fitness.route("/classes")
def get_classes():
    if session.get("user_type") != "user":
        flash("Unauthorized access.", "error")
        return redirect(url_for("login"))
    upcoming_classes = Classes.get_upcoming_classes()
    return render_template("user/classes.html", classes=upcoming_classes)


@fitness.route("/edit_user/<user_id>", methods=["GET", "POST"])
def edit_user(user_id):
    if request.method == "POST":
        height_feet = request.form.get("height_feet", type=int)
        height_inches = request.form.get("height_inches", type=int)
        updated_data = {
            "firstname": request.form.get("firstname"),
            "lastname": request.form.get("lastname"),
            "email": request.form.get("email"),
            "dob": request.form.get("dob"),  # Date of birth
            "city": request.form.get("city"),
            "zipcode": request.form.get("zipcode"),
            "phone_number": request.form.get("phone_number"),
            "height_feet": height_feet,
            "height_inches": height_inches,
            "weight": request.form.get("weight", type=float),
            "goal_weight": request.form.get("goal_weight", type=float),
            "previous_health_issues": request.form.get("previous_health_issues"),
        }
        User.update(ObjectId(user_id), updated_data)
        flash("User updated successfully", "success")
        return redirect(url_for("admin_dashboard"))
    # Render edit form with existing user data

    user = User.get_by_id(ObjectId(user_id))
    return render_template("user/edit_user.html", user=user)


@fitness.route("/diet-plans")
def get_diet_plans():
    if session.get("user_type") != "user":
        flash("Unauthorized access.", "error")
        return redirect(url_for("login"))
    user_id = session.get("user_id")
    user = User.get_by_id(ObjectId(user_id))
    if (
        user is not None
        and "membership_id" in user
        and user["membership_id"] is not None
    ):
        membership = Membership.get_by_id(ObjectId(user["membership_id"]))
        if membership["diet_plan_included"]:
            dietplan = DietPlan.get_by_id(ObjectId(membership["diet_plan_id"]))
            return render_template("user/diet_plan.html", diet_plan=dietplan)
        flash("No dietplans available")
        return redirect(url_for("user_dashboard"))
