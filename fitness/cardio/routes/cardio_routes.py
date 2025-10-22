# fitness/cardio/routes/cardio_routes.py
from flask import render_template, request, redirect, url_for, flash, jsonify, send_file
from fitness.db.db import get_connection
from fitness.utils.helpers import calculate_pace
from fitness.cardio import cardio_bp
import csv, io


# ---------------------------
# Cardio Workouts CRUD
# ---------------------------
@cardio_bp.route("/")
def cardio_list():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT cw.*, at.name AS activity_name
        FROM cardio_workouts cw
        JOIN activity_types at ON cw.activity_type_id = at.id
        ORDER BY date DESC, time DESC
    """)
    workouts = cur.fetchall()
    conn.close()
    return render_template("cardio_list.html", workouts=workouts)


@cardio_bp.route("/add", methods=["GET", "POST"])
def add_cardio():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM activity_types ORDER BY name")
    activity_types = cur.fetchall()

    if request.method == "POST":
        data = {key: request.form.get(key) for key in request.form}
        distance = float(data["distance_miles"]) if data["distance_miles"] else None
        duration = float(data["duration_minutes"]) if data["duration_minutes"] else None

        cur.execute("SELECT name FROM activity_types WHERE id=?", (data["activity_type_id"],))
        activity_name = cur.fetchone()["name"].lower()
        pace = calculate_pace(distance, duration) if "run" in activity_name or "treadmill" in activity_name else None

        cur.execute("""
            INSERT INTO cardio_workouts (date, time, activity_type_id, distance_miles, duration_minutes,
                pace_min_per_mile, avg_heart_rate, calories_burned, weight_lbs, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (data["date"], data["time"], data["activity_type_id"], distance, duration,
              pace, data["avg_heart_rate"], data["calories_burned"], data["weight_lbs"], data["notes"]))
        conn.commit()
        conn.close()
        flash("Workout added successfully!", "success")
        return redirect(url_for("cardio_bp.cardio_list"))

    conn.close()
    return render_template("cardio_form.html", action="Add", activity_types=activity_types)


@cardio_bp.route("/edit/<int:id>", methods=["GET", "POST"])
def edit_cardio(id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM activity_types ORDER BY name")
    activity_types = cur.fetchall()

    if request.method == "POST":
        data = {key: request.form.get(key) for key in request.form}
        distance = float(data["distance_miles"]) if data["distance_miles"] else None
        duration = float(data["duration_minutes"]) if data["duration_minutes"] else None

        cur.execute("SELECT name FROM activity_types WHERE id=?", (data["activity_type_id"],))
        activity_name = cur.fetchone()["name"].lower()
        pace = calculate_pace(distance, duration) if "run" in activity_name or "treadmill" in activity_name else None

        cur.execute("""
            UPDATE cardio_workouts
            SET date=?, time=?, activity_type_id=?, distance_miles=?, duration_minutes=?,
                pace_min_per_mile=?, avg_heart_rate=?, calories_burned=?, weight_lbs=?, notes=?
            WHERE id=?
        """, (data["date"], data["time"], data["activity_type_id"], distance, duration,
              pace, data["avg_heart_rate"], data["calories_burned"], data["weight_lbs"], data["notes"], id))
        conn.commit()
        conn.close()
        flash("Workout updated successfully!", "success")
        return redirect(url_for("cardio_bp.cardio_list"))

    cur.execute("SELECT * FROM cardio_workouts WHERE id=?", (id,))
    workout = cur.fetchone()
    conn.close()
    return render_template("cardio_form.html", action="Edit", activity_types=activity_types, workout=workout)


@cardio_bp.route("/delete/<int:id>")
def delete_cardio(id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM cardio_workouts WHERE id=?", (id,))
    conn.commit()
    conn.close()
    flash("Workout deleted.", "warning")
    return redirect(url_for("cardio_bp.cardio_list"))


# ---------------------------
# Dashboard
# ---------------------------
@cardio_bp.route("/dashboard")
def dashboard():
    conn = get_connection()
    data = conn.execute("""
        SELECT
            strftime('%Y-%W', date) AS week,
            SUM(distance_miles) AS total_distance,
            SUM(calories_burned) AS total_calories,
            AVG(duration_minutes / NULLIF(distance_miles, 0)) AS avg_pace_min_per_mile
        FROM cardio_workouts
        GROUP BY week
        ORDER BY week
    """).fetchall()
    conn.close()

    weeks = [d['week'] for d in data]
    distances = [round(d['total_distance'] or 0, 2) for d in data]
    calories = [int(d['total_calories'] or 0) for d in data]
    pace_decimal = []
    for d in data:
        if d['avg_pace_min_per_mile']:
            total_sec = d['avg_pace_min_per_mile'] * 60
            pace_decimal.append(round(total_sec / 60, 2))
        else:
            pace_decimal.append(None)

    return render_template('dashboard.html',
                           weeks=weeks, distances=distances,
                           calories=calories, pace_decimal=pace_decimal)


# ---------------------------
# Export / Import
# ---------------------------
@cardio_bp.route('/export_csv')
def export_cardio_csv():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT cw.id, cw.date, cw.time, at.name AS activity_type, cw.distance_miles,
               cw.duration_minutes, cw.pace_min_per_mile, cw.avg_heart_rate,
               cw.calories_burned, cw.weight_lbs, cw.notes
        FROM cardio_workouts cw
        JOIN activity_types at ON cw.activity_type_id = at.id
        ORDER BY cw.date DESC
    """)
    rows = cur.fetchall()
    headers = [desc[0] for desc in cur.description]

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(headers)
    writer.writerows(rows)
    output.seek(0)

    return send_file(io.BytesIO(output.getvalue().encode('utf-8')),
                     mimetype='text/csv',
                     as_attachment=True,
                     download_name='cardio_workouts.csv')


@cardio_bp.route('/export_json')
def export_cardio_json():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT cw.id, cw.date, cw.time, at.name AS activity_type, cw.distance_miles,
               cw.duration_minutes, cw.pace_min_per_mile, cw.avg_heart_rate,
               cw.calories_burned, cw.weight_lbs, cw.notes
        FROM cardio_workouts cw
        JOIN activity_types at ON cw.activity_type_id = at.id
        ORDER BY cw.date DESC
    """)
    rows = [dict(zip([col[0] for col in cur.description], row)) for row in cur.fetchall()]
    return jsonify(rows)


@cardio_bp.route('/import_csv', methods=['GET', 'POST'])
def import_cardio_csv():
    if request.method == 'POST':
        file = request.files['file']
        if not file:
            flash('No file uploaded', 'error')
            return redirect(url_for('cardio.cardio_list'))

        stream = io.StringIO(file.stream.read().decode("UTF8"), newline=None)
        reader = csv.DictReader(stream)

        conn = get_connection()
        cur = conn.cursor()
        for row in reader:
            cur.execute("SELECT id FROM activity_types WHERE name = ?", (row['activity_type'],))
            activity_type = cur.fetchone()
            if not activity_type:
                cur.execute("INSERT INTO activity_types (name) VALUES (?)", (row['activity_type'],))
                activity_type_id = cur.lastrowid
            else:
                activity_type_id = activity_type[0]

            cur.execute("""
                INSERT INTO cardio_workouts (date, time, activity_type_id, distance_miles,
                                             duration_minutes, pace_min_per_mile,
                                             avg_heart_rate, calories_burned, weight_lbs, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                row['date'], row.get('time'), activity_type_id,
                row.get('distance_miles'), row.get('duration_minutes'),
                row.get('pace_min_per_mile'), row.get('avg_heart_rate'),
                row.get('calories_burned'), row.get('weight_lbs'), row.get('notes')
            ))
        conn.commit()
        conn.close()
        flash('Cardio workouts imported successfully!', 'success')
        return redirect(url_for('cardio.cardio_list'))

    return render_template('import_cardio.html')
