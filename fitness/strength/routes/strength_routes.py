from flask import render_template, request, redirect, url_for, flash, jsonify, send_file
from fitness.db.db import get_connection
from fitness.utils.helpers import calculate_pace
from fitness.strength import strength_bp
import csv, io
import sqlite3


# -------------------------
# Exercise Types CRUD
# -------------------------
@strength_bp.route('/exercise_types')
def exercise_types():
    conn = get_connection()
    types = conn.execute("SELECT * FROM exercise_types ORDER BY body_part, name").fetchall()
    conn.close()
    return render_template('exercise_types_list.html', types=types)

@strength_bp.route('/exercise_types/add', methods=['GET', 'POST'])
def add_exercise_type():
    if request.method == 'POST':
        name = request.form['name']
        body_part = request.form.get('body_part')
        conn = get_connection()
        try:
            conn.execute("INSERT INTO exercise_types (name, body_part) VALUES (?, ?)", (name, body_part))
            conn.commit()
            flash("Exercise type added.", "success")
        except sqlite3.IntegrityError:
            flash("Exercise type already exists.", "danger")
        conn.close()
        return redirect(url_for('strength_bp.exercise_types'))
    return render_template('exercise_types_form.html', action="Add", exercise_type=None)

@strength_bp.route('/exercise_types/edit/<int:id>', methods=['GET', 'POST'])
def edit_exercise_type(id):
    conn = get_connection()
    et = conn.execute("SELECT * FROM exercise_types WHERE id=?", (id,)).fetchone()
    if request.method == 'POST':
        name = request.form['name']
        body_part = request.form.get('body_part')
        conn.execute("UPDATE exercise_types SET name=?, body_part=? WHERE id=?", (name, body_part, id))
        conn.commit()
        conn.close()
        flash("Exercise type updated.", "info")
        return redirect(url_for('strength_bp.exercise_types'))
    conn.close()
    return render_template('exercise_types_form.html', action="Edit", exercise_type=et)

@strength_bp.route('/exercise_types/delete/<int:id>')
def delete_exercise_type(id):
    conn = get_connection()
    conn.execute("DELETE FROM exercise_types WHERE id=?", (id,))
    conn.commit()
    conn.close()
    flash("Exercise type deleted.", "warning")
    return redirect(url_for('strength_bp.exercise_types'))


# -------------------------
# Workouts CRUD
# -------------------------
@strength_bp.route('/strength')
def strength_list():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM workouts ORDER BY date DESC, time DESC").fetchall()
    conn.close()
    return render_template('strength_list.html', workouts=rows)

@strength_bp.route('/strength/add', methods=['GET', 'POST'])
def strength_add():
    conn = get_connection()
    exercise_types = conn.execute("SELECT * FROM exercise_types ORDER BY body_part, name").fetchall()
    if request.method == 'POST':
        # top-level workout
        date = request.form['date']
        time = request.form.get('time')
        body_part = request.form.get('body_part')
        notes = request.form.get('notes')

        cur = conn.cursor()
        cur.execute("INSERT INTO workouts (date, time, body_part, notes) VALUES (?, ?, ?, ?)",
                    (date, time, body_part, notes))
        workout_id = cur.lastrowid

        # Expect exercises and sets to come as JSON string in hidden field named 'payload'
        # The client JS will build a JSON structure and post it as payload
        import json
        payload = request.form.get('payload')
        if payload:
            try:
                data = json.loads(payload)
                for ex in data.get('exercises', []):
                    ex_name = ex.get('exercise_name')
                    cur.execute("INSERT INTO exercises (workout_id, exercise_name) VALUES (?, ?)",
                                (workout_id, ex_name))
                    ex_id = cur.lastrowid
                    for s in ex.get('sets', []):
                        set_number = s.get('set_number')
                        reps = s.get('reps') or None
                        weight = s.get('weight') or None
                        rest_seconds = s.get('rest') or None
                        cur.execute("""
                            INSERT INTO sets (exercise_id, set_number, reps, weight, rest_seconds)
                            VALUES (?, ?, ?, ?, ?)
                        """, (ex_id, set_number, reps, weight, rest_seconds))
                conn.commit()
                flash("Workout saved.", "success")
            except Exception as e:
                conn.rollback()
                flash(f"Error saving workout: {e}", "danger")
        conn.close()
        return redirect(url_for('strength_bp.strength_list'))

    conn.close()
    return render_template('strength_form.html', action="Add", exercise_types=exercise_types)

@strength_bp.route('/strength/view/<int:id>')
def strength_view(id):
    conn = get_connection()
    workout = conn.execute("SELECT * FROM workouts WHERE id=?", (id,)).fetchone()
    exercises = conn.execute("SELECT * FROM exercises WHERE workout_id=? ORDER BY id", (id,)).fetchall()
    # For each exercise collect sets
    ex_list = []
    for ex in exercises:
        sets = conn.execute("SELECT * FROM sets WHERE exercise_id=? ORDER BY set_number", (ex['id'],)).fetchall()
        ex_list.append({'exercise': ex, 'sets': sets})
    conn.close()
    return render_template('strength_view.html', workout=workout, exercises=ex_list)

@strength_bp.route('/strength/delete/<int:id>')
def strength_delete(id):
    conn = get_connection()
    cur = conn.cursor()
    # delete sets -> exercises -> workout
    ex_ids = [r['id'] for r in cur.execute("SELECT id FROM exercises WHERE workout_id=?", (id,)).fetchall()]
    for ex_id in ex_ids:
        cur.execute("DELETE FROM sets WHERE exercise_id=?", (ex_id,))
    cur.execute("DELETE FROM exercises WHERE workout_id=?", (id,))
    cur.execute("DELETE FROM workouts WHERE id=?", (id,))
    conn.commit()
    conn.close()
    flash("Workout deleted.", "warning")
    return redirect(url_for('strength_bp.strength_list'))


@strength_bp.route('/strength/edit/<int:id>', methods=['GET', 'POST'])
def strength_edit(id):
    conn = get_connection()
    exercise_types = conn.execute("SELECT * FROM exercise_types ORDER BY body_part, name").fetchall()
    if request.method == 'POST':
        # update workout details and replace exercises/sets
        date = request.form['date']
        time = request.form.get('time')
        body_part = request.form.get('body_part')
        notes = request.form.get('notes')

        cur = conn.cursor()
        cur.execute("UPDATE workouts SET date=?, time=?, body_part=?, notes=? WHERE id=?",
                    (date, time, body_part, notes, id))

        # delete old exercises & sets
        ex_ids = [r['id'] for r in cur.execute("SELECT id FROM exercises WHERE workout_id=?", (id,)).fetchall()]
        for ex_id in ex_ids:
            cur.execute("DELETE FROM sets WHERE exercise_id=?", (ex_id,))
        cur.execute("DELETE FROM exercises WHERE workout_id=?", (id,))

        # insert new from payload
        import json
        payload = request.form.get('payload')
        if payload:
            try:
                data = json.loads(payload)
                for ex in data.get('exercises', []):
                    ex_name = ex.get('exercise_name')
                    cur.execute("INSERT INTO exercises (workout_id, exercise_name) VALUES (?, ?)",
                                (id, ex_name))
                    ex_id = cur.lastrowid
                    for s in ex.get('sets', []):
                        set_number = s.get('set_number')
                        reps = s.get('reps') or None
                        weight = s.get('weight') or None
                        rest_seconds = s.get('rest') or None
                        cur.execute("""
                            INSERT INTO sets (exercise_id, set_number, reps, weight, rest_seconds)
                            VALUES (?, ?, ?, ?, ?)
                        """, (ex_id, set_number, reps, weight, rest_seconds))
                conn.commit()
                flash("Workout updated.", "success")
            except Exception as e:
                conn.rollback()
                flash(f"Error updating workout: {e}", "danger")
        conn.close()
        return redirect(url_for('strength_bp.strength_view', id=id))

    # GET: load workout and nested exercises/sets to prepopulate the form
    workout = conn.execute("SELECT * FROM workouts WHERE id=?", (id,)).fetchone()
    exercises = conn.execute("SELECT * FROM exercises WHERE workout_id=? ORDER BY id", (id,)).fetchall()
    ex_list = []
    for ex in exercises:
        sets = conn.execute("SELECT * FROM sets WHERE exercise_id=? ORDER BY set_number", (ex['id'],)).fetchall()
        ex_list.append({'exercise': ex, 'sets': sets})
    conn.close()
    return render_template('strength_form.html', action="Edit", exercise_types=exercise_types,
                           workout=workout, exercises=ex_list)



# -----------------------------
# Strength Dashboard Routes
# -----------------------------


@strength_bp.route('/strength_dashboard')
def strength_dashboard():
    conn = get_connection()
    exercises = conn.execute("SELECT id, exercise_name FROM exercises ORDER BY exercise_name").fetchall()
    conn.close()
    return render_template('strength_dashboard.html', exercises=exercises)

@strength_bp.route('/api/strength_data/<int:exercise_id>')
def get_strength_data(exercise_id):
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # ✅ total volume (weight * reps) per workout date for given exercise
    cur.execute("""
        SELECT w.date, SUM(s.weight * s.reps) AS total_volume
        FROM sets s
        JOIN workouts w ON s.id = w.id
        WHERE s.exercise_id = ?
        GROUP BY w.date
        ORDER BY w.date
    """, (exercise_id,))
    vol_data = cur.fetchall()

    # ✅ PR (heaviest single set weight for this exercise)
    cur.execute("""
        SELECT MAX(weight) AS pr_weight
        FROM sets
        WHERE exercise_id = ?
    """, (exercise_id,))
    pr_data = cur.fetchone()

    conn.close()

    return jsonify({
        "dates": [r["date"] for r in vol_data],
        "volumes": [r["total_volume"] for r in vol_data],
        "pr": pr_data["pr_weight"] if pr_data and pr_data["pr_weight"] else 0
    })




# ---------- EXPORT WORKOUTS ----------
@strength_bp.route('/export_strength/<string:fmt>')
def export_strength(fmt):
    conn = get_connection()
    cur = conn.cursor()

    # Join all relevant data
    cur.execute("""
        SELECT w.id as workout_id, w.date, w.body_part, w.notes,
               e.id as exercise_id, e.exercise_name,
               s.set_number, s.reps, s.weight, s.rest_seconds
        FROM workouts w
        JOIN exercises e ON w.id = e.workout_id
        JOIN sets s ON e.id = s.exercise_id
        ORDER BY w.date, w.id, e.id, s.set_number
    """)
    rows = cur.fetchall()
    conn.close()

    if fmt == 'csv':
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            'workout_id','date','body_part','notes',
            'exercise_name','set_number','reps','weight','rest_seconds'
        ])
        for r in rows:
            writer.writerow([
                r['workout_id'], r['date'], r['body_part'], r['notes'],
                r['exercise_name'], r['set_number'], r['reps'], r['weight'], r['rest_seconds']
            ])
        output.seek(0)
        return send_file(
            io.BytesIO(output.getvalue().encode('utf-8')),
            mimetype='text/csv',
            as_attachment=True,
            download_name='strength_workouts.csv'
        )

    elif fmt == 'json':
        data = [dict(r) for r in rows]
        return jsonify(data)

    else:
        return "Unsupported format", 400


# ---------- IMPORT WORKOUTS ----------
@strength_bp.route('/import_strength', methods=['GET', 'POST'])
def import_strength():
    if request.method == 'POST':
        file = request.files.get('file')
        fmt = request.form.get('format')

        if not file:
            return "No file uploaded", 400

        conn = get_connection()
        cur = conn.cursor()

        if fmt == 'csv':
            stream = io.StringIO(file.stream.read().decode('utf-8'))
            reader = csv.DictReader(stream)
            for row in reader:
                date = row['date']
                body_part = row['body_part']
                notes = row['notes']
                exercise_name = row['exercise_name']
                set_number = int(row['set_number'])
                reps = int(row['reps'])
                weight = float(row['weight']) if row['weight'] else None
                rest_seconds = int(row['rest_seconds']) if row['rest_seconds'] else None

                # Insert workout (if not exists)
                cur.execute("SELECT id FROM workouts WHERE date=? AND body_part=? AND notes=?", 
                            (date, body_part, notes))
                w = cur.fetchone()
                if w: workout_id = w['id']
                else:
                    cur.execute("INSERT INTO workouts (date, body_part, notes) VALUES (?, ?, ?)",
                                (date, body_part, notes))
                    workout_id = cur.lastrowid

                # Insert exercise (if not exists)
                cur.execute("SELECT id FROM exercises WHERE workout_id=? AND exercise_name=?",
                            (workout_id, exercise_name))
                e = cur.fetchone()
                if e: exercise_id = e['id']
                else:
                    cur.execute("INSERT INTO exercises (workout_id, exercise_name) VALUES (?, ?)",
                                (workout_id, exercise_name))
                    exercise_id = cur.lastrowid

                # Insert set
                cur.execute("""
                    INSERT INTO sets (exercise_id, set_number, reps, weight, rest_seconds)
                    VALUES (?, ?, ?, ?, ?)
                """, (exercise_id, set_number, reps, weight, rest_seconds))

            conn.commit()
            conn.close()
            return "CSV data imported successfully!"

        elif fmt == 'json':
            data = json.load(file)
            for r in data:
                date = r['date']
                body_part = r['body_part']
                notes = r.get('notes', '')
                exercise_name = r['exercise_name']
                set_number = r['set_number']
                reps = r['reps']
                weight = r.get('weight')
                rest_seconds = r.get('rest_seconds')

                cur.execute("SELECT id FROM workouts WHERE date=? AND body_part=? AND notes=?", 
                            (date, body_part, notes))
                w = cur.fetchone()
                if w: workout_id = w['id']
                else:
                    cur.execute("INSERT INTO workouts (date, body_part, notes) VALUES (?, ?, ?)",
                                (date, body_part, notes))
                    workout_id = cur.lastrowid

                cur.execute("SELECT id FROM exercises WHERE workout_id=? AND exercise_name=?",
                            (workout_id, exercise_name))
                e = cur.fetchone()
                if e: exercise_id = e['id']
                else:
                    cur.execute("INSERT INTO exercises (workout_id, exercise_name) VALUES (?, ?)",
                                (workout_id, exercise_name))
                    exercise_id = cur.lastrowid

                cur.execute("""
                    INSERT INTO sets (exercise_id, set_number, reps, weight, rest_seconds)
                    VALUES (?, ?, ?, ?, ?)
                """, (exercise_id, set_number, reps, weight, rest_seconds))

            conn.commit()
            conn.close()
            return "JSON data imported successfully!"

        else:
            return "Unsupported format", 400

    return render_template('import_strength.html')


