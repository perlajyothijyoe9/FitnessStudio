from flask import render_template, request, redirect, url_for, session, flash
from fitness import fitness
import logging
from datetime import datetime, timedelta
from bson.objectid import ObjectId
from flask import jsonify
from fitness.model.admin import Admin
from fitness.model.user import User
from fitness.model.trainer import Trainer
from fitness.model.membership import Membership
from fitness.model.dietplan import DietPlan
from fitness.model.payment import Payment
from fitness.model.classes import Classes
from fitness.model.booking import Booking
from werkzeug.security import generate_password_hash, check_password_hash

# generate_password_hash(password)
# if check_password_hash(user['password'], password)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@fitness.route("/admin_signup", methods=["GET"])
def admin_signup():
    try:
        # Hard coded admin data
        email = "admin@admin.com"
        user_name = "Admin"
        phone = "123-345-5678"
        password = "admin"

        # Check if the admin email is already registered
        if Admin.exists_by_email(email):
            flash({"message": "Admin already registered. Check DB for details."}), 200
            return redirect(url_for("login"))

        data = {
            "user_name": user_name,
            "email": email,
            "phone": phone,
            "password": generate_password_hash(password),
        }

        # Create admin record
        Admin.create(data)
        flash({"message": "Admin registered successfully!"}), 201
        return redirect(url_for("login"))
    except Exception as e:
        logger.error(f"Error occured during admin registration: {str(e)}")
        return "Internal Server Error", 500


@fitness.route("/login", methods=["GET", "POST"])
def login():
    next_url = (
        request.args.get("next") or request.form.get("next") or url_for("dashboard")
    )

    if request.method == "POST":
        email = request.form.get("email").strip()
        password = request.form.get("password").strip()
        user_type = request.form.get("user_type").strip()

        print(f"Next URL: {next_url}")

        if user_type == "admin":
            if Admin.exists_by_email(email):
                admin = Admin.get_by_email(email)
                if check_password_hash(admin["password"], password):
                    session["user_id"] = str(admin["_id"])
                    session["user_type"] = "admin"
                    if admin.get("is_admin_created"):
                        return redirect(url_for("update_password"))
                    return redirect(url_for("admin_dashboard"))
                else:
                    flash("Invalid credentials", "error")
            else:
                flash("No such admin", "error")
        elif user_type == "user":
            if User.exists_by_email(email):
                user = User.get_by_email(email)
                print(
                    f"password check -------->{check_password_hash(password, user["password"])}"
                )
                if check_password_hash(user["password"], password):
                    session["user_id"] = str(user["_id"])
                    session["user_type"] = "user"
                    if user.get("is_admin_created"):
                        return redirect(url_for("update_password"))
                    return redirect(url_for("user_dashboard"))
                else:
                    flash("Invalid credentials", "error")
            else:
                flash("No such user", "error")
        elif user_type == "trainer":
            if Trainer.exists_by_email(email):
                trainer = Trainer.get_by_email(email)
                if check_password_hash(trainer["password"], password):
                    session["user_id"] = str(trainer["_id"])
                    session["user_type"] = "trainer"
                    if trainer.get("is_admin_created"):
                        return redirect(url_for("update_password"))
                    return redirect(url_for("trainer_dashboard"))
                else:
                    flash("Invalid credentials", "error")
            else:
                flash("No such trainer", "error")
        else:
            flash("Invalid user type", "error")

        return redirect(url_for("login", next=next_url))

    return render_template("login.html", next=next_url)


@fitness.route("/dashboard")
def dashboard():
    if session.get("user_type") == "admin":
        return redirect(url_for("admin_dashboard"))
    elif session.get("user_type") == "user":
        return redirect(url_for("user_dashboard"))
    elif session.get("user_type") == "trainer":
        return redirect(url_for("trainer_dashboard"))
    else:
        flash("Unauthorized access.", "error")
        return redirect(url_for("login"))


@fitness.route("/admin_dashboard")
def admin_dashboard():
    if session.get("user_type") != "admin":
        flash("Unauthorized access.", "error")
        return redirect(url_for("login"))
    users = User.get_all()
    trainers = Trainer.get_all()
    memberships = Membership.get_all()
    for membership in memberships:
        if membership["diet_plan_included"] == True:
            diet_plan = DietPlan.get_by_id(ObjectId(membership["diet_plan_id"]))
            membership["diet_plan"] = diet_plan

    return render_template(
        "admin/home.html", users=users, trainers=trainers, memberships=memberships
    )


@fitness.route("/user_dashboard")
def user_dashboard():
    if session.get("user_type") != "user":
        flash("Unauthorized access.", "error")
        return redirect(url_for("login"))
    user_id = session.get("user_id")
    user = User.get_by_id(ObjectId(user_id))

    # Check membership status and get membership details
    membership_status = "none"
    membership = None
    if (
        user is not None
        and "membership_id" in user
        and user["membership_id"] is not None
    ):
        membership = Membership.get_by_id(ObjectId(user["membership_id"]))
        if membership:
            payment = Payment.get_latest_payment_record(user_id, str(membership["_id"]))
            print(f"-------------------->{payment}")
            created_at = payment[0].get("payment_date")
            validity_period = membership.get("validity_period", 0)
            expiration_date = created_at + timedelta(days=int(validity_period))
            days_difference = (expiration_date - datetime.now()).days
            print(f"-------------------->{expiration_date}")
            membership["expire_days"] = days_difference
            if expiration_date >= datetime.now():
                membership_status = "active"
                if membership["diet_plan_included"] == True:
                    diet_plan = DietPlan.get_by_id(
                        ObjectId(membership.get("diet_plan_id"))
                    )
                    membership["diet_plan"] = diet_plan
            elif membership["auto_renewal"] == True:
                # Create payment record
                payment_data = {
                    "membership_id": str(membership["_id"]),
                    "user_id": user_id,
                    "amount": membership["price"],
                    "payment_date": datetime.now(),
                    "payment_method": "Credit Card",
                    "status": "Completed",
                }
                Payment.create(payment_data)

                # Update user's membership if payment is successful
                User.update_membership_id(user_id, str(membership["_id"]))
                membership_status = "active"
                diet_plan = DietPlan.get_by_id(ObjectId(membership.get("diet_plan_id")))
                membership["diet_plan"] = diet_plan
                membership["expire_days"] = int(membership["validity_period"]) - 1
            else:
                membership_status = "expired"
    payments = Payment.get_all_by_user_id(user_id)
    print(f"------------------->{membership_status}")
    return render_template(
        "user/home.html",
        is_logged_in=True,
        membership_status=membership_status,
        membership=membership,
        payments=payments,
    )


@fitness.route("/add_user", methods=["GET", "POST"])
def add_user():
    if request.method == "POST":
        try:
            # Fetching height in feet and inches as separate values
            height_feet = request.form.get("height_feet", type=int)
            height_inches = request.form.get("height_inches", type=int)

            print(f"Height ------->{height_feet}")

            # Creating the user data dictionary
            user_data = {
                "firstname": request.form.get("firstname"),
                "lastname": request.form.get("lastname"),
                "username": request.form.get("username"),
                "email": request.form.get("email"),
                "password": generate_password_hash(request.form.get("password")),
                "dob": request.form.get("dob"),  # Date of birth
                "city": request.form.get("city"),
                "zipcode": request.form.get("zipcode"),
                "phone_number": request.form.get("phone_number"),
                "height_feet": height_feet,
                "height_inches": height_inches,
                "weight": request.form.get("weight", type=float),
                "goal_weight": request.form.get("goal_weight", type=float),
                "previous_health_issues": request.form.get("previous_health_issues"),
                "is_admin_created": True,
            }

            # Save the user data
            User.create(user_data)
            flash("User added successfully!", "success")
            return redirect(url_for("admin_dashboard"))
        except Exception as e:
            flash(f"An error occurred: {e}", "danger")

    return render_template("user/add_user.html")


@fitness.route("/delete_user/<user_id>", methods=["POST"])
def delete_user(user_id):
    User.delete(ObjectId(user_id))
    flash("User deleted successfully", "success")
    return redirect(url_for("admin_dashboard"))


@fitness.route("/trainer_dashboard")
def trainer_dashboard():
    if session.get("user_type") != "trainer":
        flash("Unauthorized access.", "error")
        return redirect(url_for("login"))
    trainer_id = str(session.get("user_id"))
    classes = Classes.get_by_trainer_id(trainer_id)
    pending_bookings = []
    for individual_class in classes:
        bookings = Booking.get_pending_by_class_id(str(individual_class["_id"]))
        if bookings is not None:
            for booking in bookings:
                booking["class"] = individual_class["name"]
                pending_bookings.append(booking)
    return render_template(
        "trainer/home.html",
        is_logged_in=True,
        classes=classes,
        pending_bookings=pending_bookings,
    )


# Add Trainer
@fitness.route("/add_trainer", methods=["GET", "POST"])
def add_trainer():
    if request.method == "POST":
        try:
            # Fetching form data
            trainer_data = {
                "firstname": request.form.get("firstname"),
                "lastname": request.form.get("lastname"),
                "email": request.form.get("email"),
                "password": generate_password_hash(request.form.get("password")),
                "phone_number": request.form.get("phone_number"),
                "city": request.form.get("city"),
                "zipcode": request.form.get("zipcode"),
                "ssn": request.form.get("ssn"),
                "expertise": request.form.get("expertise"),
                "experience": request.form.get("experience", type=int),
                "is_admin_created": True,  # Indicates the trainer was added by admin
            }

            # Create trainer in the database
            Trainer.create(trainer_data)
            flash("Trainer added successfully!", "success")
            return redirect(url_for("admin_dashboard"))
        except Exception as e:
            flash(f"An error occurred: {e}", "error")
            return redirect(url_for("add_trainer"))

    return render_template("trainer/add_trainer.html")


# Delete Trainer
@fitness.route("/delete_trainer/<trainer_id>", methods=["POST"])
def delete_trainer(trainer_id):
    Trainer.delete(ObjectId(trainer_id))
    flash("Trainer deleted successfully!", "success")
    return redirect(url_for("admin_dashboard"))


# View All Trainers
@fitness.route("/view_trainers")
def view_trainers():
    trainers = Trainer.get_all()
    return render_template("trainer/view_trainers.html", trainers=trainers)


@fitness.route("/logout")
def logout():
    session.clear()
    return render_template("index.html")
