from flask import render_template, request, redirect, url_for, session, flash
from fitness import fitness
from datetime import datetime, timedelta
from bson.objectid import ObjectId
from flask import jsonify
from fitness.model.classes import Classes
from fitness.model.booking import Booking


@fitness.route("/search_classes", methods=["GET"])
def search_classes():
    # Retrieve search filters from query parameters
    category = request.args.get("category")
    date_str = request.args.get("date")

    query = {}

    # Add category filter if provided
    if category:
        query["category"] = category

    # # Add date filter if provided
    # if date_str:
    #     try:
    #         # Parse the date string into a datetime object
    #         date = datetime.strptime(date_str, "%Y-%m-%d")

    #         # Set a range from the start to the end of the day
    #         start_of_day = date
    #         end_of_day = date + timedelta(days=1)

    #         # Update the query with this range
    #         query["schedule.date"] = {"$gte": start_of_day, "$lt": end_of_day}
    #     except ValueError:
    #         # Handle invalid date format
    #         return render_template(
    #             "error.html", message="Invalid date format. Use YYYY-MM-DD."
    #         )

    # Perform the query on the classes collection and handle if no results are found
    classes = Classes.get_by_query(query)
    if not classes:
        flash("No classes found matching the search criteria.", "info")

    return render_template("classes/search_classes.html", classes=classes)
