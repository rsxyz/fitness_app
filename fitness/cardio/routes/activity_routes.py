from flask import render_template, request, redirect, url_for, flash
from fitness.db.db import get_connection
from fitness.cardio import cardio_bp

# ---------------------------
# Activity Types CRUD
# ---------------------------
@cardio_bp.route("/activity-types")
def activity_types():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM activity_types ORDER BY name")
    types = cur.fetchall()
    conn.close()
    return render_template("activity_types_list.html", types=types)


@cardio_bp.route("/activity-types/add", methods=["GET", "POST"])
def add_activity_type():
    if request.method == "POST":
        name = request.form["name"]
        description = request.form["description"]
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("INSERT INTO activity_types (name, description) VALUES (?, ?)", (name, description))
        conn.commit()
        conn.close()
        flash("Activity type added successfully!", "success")
        return redirect(url_for("cardio_bp.activity_types"))
    return render_template("activity_types_form.html", action="Add")


@cardio_bp.route("/activity-types/edit/<int:id>", methods=["GET", "POST"])
def edit_activity_type(id):
    conn = get_connection()
    cur = conn.cursor()
    if request.method == "POST":
        name = request.form["name"]
        description = request.form["description"]
        cur.execute("UPDATE activity_types SET name=?, description=? WHERE id=?", (name, description, id))
        conn.commit()
        conn.close()
        flash("Activity type updated successfully!", "success")
        return redirect(url_for("cardio_bp.activity_types"))

    cur.execute("SELECT * FROM activity_types WHERE id=?", (id,))
    type_data = cur.fetchone()
    conn.close()
    return render_template("activity_types_form.html", action="Edit", type_data=type_data)


@cardio_bp.route("/activity-types/delete/<int:id>")
def delete_activity_type(id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM activity_types WHERE id=?", (id,))
    conn.commit()
    conn.close()
    flash("Activity type deleted.", "warning")
    return redirect(url_for("cardio_bp.activity_types"))
