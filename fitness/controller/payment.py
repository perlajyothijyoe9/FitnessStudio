from flask import render_template, request, redirect, url_for, session, flash
from fitness import fitness
import logging
from datetime import datetime, timedelta
from bson.objectid import ObjectId
from flask import jsonify
from fitness.model.user import User
from fitness.model.payment import Payment

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@fitness.route("/initiate_payment", methods=["POST"])
def initiate_payment():
    if session.get("user_type") != "user":
        flash("Unauthorized access.", "error")
        return redirect(url_for("login"))

    data = request.get_json()
    user_id = session.get("user_id")
    membership_id = data.get("membership_id")
    amount = data.get("amount")

    # Create payment record
    try:
        payment_data = {
            "membership_id": membership_id,
            "user_id": user_id,
            "amount": amount,
            "payment_date": datetime.now(),
            "payment_method": "Credit Card",
            "status": "Completed",
        }
        Payment.create(payment_data)

        # Update user's membership if payment is successful
        User.update_membership_id(user_id, membership_id)
        return jsonify({"status": "success", "message": "Membership purchased"}), 200

    except Exception as e:
        logger.error(f"Payment error: {str(e)}")
        print(f"eroor-.{e}")
        return jsonify({"status": "error", "message": "Payment processing failed"}), 500
