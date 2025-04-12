from flask import render_template, request, redirect, url_for, session, flash
from fitness import fitness
import logging
from datetime import datetime
from bson.objectid import ObjectId
from datetime import timedelta
from fitness.model.user import User
from fitness.model.trainer import Trainer
from werkzeug.security import generate_password_hash, check_password_hash

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@fitness.route("/", methods=["GET", "POST"])
def home():
    is_logged_in = "user_id" in session
    return render_template("index.html", is_logged_in=is_logged_in)

@fitness.route("/forgot_password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        email = request.form.get("email")
        if User.exists_by_email(email):
            flash("Password reset email sent. Please check your inbox.", "success")
            return render_template("update_password.html")
        else:
            flash("No account found with this email.", "error")
            return redirect(url_for("forgot_password"))
    return render_template('forgot_password.html')

@fitness.route('/change_password', methods=['GET'])
def change_password():
    return render_template('change_password.html')


@fitness.route("/update_password", methods=["GET", "POST"])
def update_password():
    if request.method == "POST":
        user_id = session.get("user_id")
        if not user_id:
            flash("Session expired. Please log in again.", "error")
            return redirect(url_for("login"))

        new_password = request.form.get("new_password").strip()
        confirm_password = request.form.get("confirm_password").strip()

        if new_password != confirm_password:
            flash("Passwords do not match. Please try again.", "error")
            return redirect(url_for("update_password"))

        # Update the password in the database
        user_type = session.get("user_type")
        if user_type == "user":
            User.update_password(
                ObjectId(user_id), generate_password_hash(new_password)
            )
            User.update_field(
                ObjectId(user_id), {"is_admin_created": False}
            )  # Set flag to False
        elif user_type == "trainer":
            Trainer.update_password(
                ObjectId(user_id), generate_password_hash(new_password)
            )
            Trainer.update_field(
                ObjectId(user_id), {"is_admin_created": False}
            )  # Set flag to False
        else:
            flash("Invalid user type. Please contact support.", "error")
            return redirect(url_for("login"))

        flash("Password updated successfully! Please log in.", "success")
        return redirect(url_for("login"))

    return render_template("update_password.html")
