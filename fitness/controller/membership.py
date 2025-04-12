from flask import render_template, request, redirect, url_for, session, flash
from fitness import fitness
import logging
from datetime import datetime, timedelta
from bson.objectid import ObjectId
from flask import jsonify
from fitness.model.membership import Membership
from fitness.model.dietplan import DietPlan

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@fitness.route("/memberships")
def get_all_memberships():
    if session.get("user_type") != "user":
        flash("Unauthorized access.", "error")
        return redirect(url_for("login"))
    memberships = Membership.get_all()
    return render_template("user/memberships.html", memberships=memberships)


@fitness.route("/edit_membership/<membership_id>", methods=["GET", "POST"])
def edit_membership(membership_id):
    membership = Membership.get_by_id(ObjectId(membership_id))
    diet_plan_id = membership["diet_plan_id"] if "diet_plan_id" in membership else ""

    if request.method == "POST":
        # Update Membership details
        updated_membership_data = {
            "name": request.form["name"],
            "price": float(request.form["price"]),
            "validity_period": request.form["validity_period"],
            "features": request.form.getlist("features"),
            "diet_plan_included": "diet_plan_included" in request.form,
            "auto_renewal": "auto_renewal" in request.form,
            "created_at": datetime.now(),
        }

        # Check if a diet plan is included
        if updated_membership_data["diet_plan_included"]:
            # Prepare diet plan data based on form inputs
            diet_plan_data = {
                "name": request.form["diet_name"],
                "description": request.form["diet_description"],
                "meal_schedule": {
                    "breakfast": request.form["meal_schedule[breakfast]"],
                    "lunch": request.form["meal_schedule[lunch]"],
                    "dinner": request.form["meal_schedule[dinner]"],
                },
                "start_date": datetime.strptime(request.form["start_date"], "%Y-%m-%d"),
                "end_date": datetime.strptime(request.form["end_date"], "%Y-%m-%d"),
            }

            # Check if a diet plan already exists and update or create it
            if diet_plan_id != "":
                DietPlan.update(ObjectId(diet_plan_id), diet_plan_data)
                flash("Diet plan updated successfully", "success")
            else:
                result = DietPlan.create(diet_plan_data)
                flash("Diet plan created and linked to membership", "success")
                updated_membership_data["diet_plan_id"] = result.inserted_id
                diet_plan_id = result.inserted_id
        else:
            # If diet plan is not included, remove any existing diet plan ID from the membership
            if "diet_plan_id" in membership:
                updated_membership_data["diet_plan_id"] = None
                if diet_plan_id:
                    DietPlan.delete(ObjectId(diet_plan_id))
                    flash("Diet plan removed from membership", "info")

        # Update the membership with new data
        Membership.update(ObjectId(membership_id), updated_membership_data)
        flash("Membership updated successfully", "success")
        return redirect(url_for("admin_dashboard"))

    # Fetch existing diet plan data if it exists
    existing_diet_plan = (
        DietPlan.get_by_id(ObjectId(diet_plan_id)) if diet_plan_id else None
    )

    return render_template(
        "membership/edit_membership.html",
        membership=membership,
        diet_plan=existing_diet_plan,
    )


@fitness.route("/delete_membership/<membership_id>", methods=["POST"])
def delete_membership(membership_id):
    membership = Membership.get_by_id(ObjectId(membership_id))
    Membership.delete(ObjectId(membership_id))
    DietPlan.delete(ObjectId(membership["diet_plan_id"]))
    flash("Membership deleted successfully", "success")
    return redirect(url_for("admin_dashboard"))


@fitness.route("/add_membership", methods=["GET", "POST"])
def add_membership():
    if request.method == "POST":
        try:
            features = request.form.get("features", "").split(",")
            membership_data = {
                "name": request.form.get("name"),
                "price": request.form.get("price", type=float),
                "validity_period": request.form.get("validity_period"),
                "features": [feature.strip() for feature in features],
                "diet_plan_included": bool(request.form.get("diet_plan_included")),
                "auto_renewal": bool(request.form.get("auto_renewal")),
                "created_at": datetime.now(),
            }
            if membership_data["diet_plan_included"]:
                # Prepare diet plan data based on form inputs
                diet_plan_data = {
                    "name": request.form["diet_name"],
                    "description": request.form["diet_description"],
                    "meal_schedule": {
                        "breakfast": request.form["meal_schedule[breakfast]"],
                        "lunch": request.form["meal_schedule[lunch]"],
                        "dinner": request.form["meal_schedule[dinner]"],
                    },
                    "start_date": datetime.strptime(
                        request.form["start_date"], "%Y-%m-%d"
                    ),
                    "end_date": datetime.strptime(request.form["end_date"], "%Y-%m-%d"),
                }
                result = DietPlan.create(diet_plan_data)
                membership_data["diet_plan_id"] = result.inserted_id
            Membership.create(membership_data)
            flash("Membership added successfully!", "success")
            return redirect(url_for("admin_dashboard"))
        except Exception as e:
            print(f"error {e}")
    return render_template("membership/add_membership.html")
