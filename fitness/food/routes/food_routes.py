from flask import render_template, request, redirect, url_for, flash, jsonify, send_file
from fitness.db.db import get_connection
from fitness.utils.helpers import calculate_pace
from fitness.food import food_bp
import csv, io


# ---------- Food Log CRUD ----------
@food_bp.route('/food')
def food_list():
    conn = get_connection()
    foods = conn.execute("""
        SELECT f.*, mt.name AS meal_name
        FROM food_log f
        JOIN meal_types mt ON f.meal_type_id = mt.id
        ORDER BY date DESC, time DESC
    """).fetchall()
    conn.close()
    return render_template('food_list.html', foods=foods)

@food_bp.route('/food/add', methods=['GET', 'POST'])
def add_food():
    conn = get_connection()
    meal_types = conn.execute("SELECT * FROM meal_types ORDER BY name").fetchall()

    if request.method == 'POST':
        date = request.form['date']
        time = request.form['time']
        meal_type_id = request.form['meal_type_id']
        food_item = request.form['food_item']
        quantity = request.form['quantity']
        calories = request.form.get('calories') or None
        notes = request.form.get('notes') or None

        conn.execute("""
            INSERT INTO food_log (date, time, meal_type_id, food_item, quantity, calories, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (date, time, meal_type_id, food_item, quantity, calories, notes))
        conn.commit()
        conn.close()
        flash("✅ Food entry added!", "success")
        return redirect(url_for('food_bp.food_list'))

    conn.close()
    return render_template('food_form.html', action="Add", meal_types=meal_types)

@food_bp.route('/food/edit/<int:id>', methods=['GET', 'POST'])
def edit_food(id):
    conn = get_connection()
    meal_types = conn.execute("SELECT * FROM meal_types ORDER BY name").fetchall()
    food = conn.execute("SELECT * FROM food_log WHERE id=?", (id,)).fetchone()

    if request.method == 'POST':
        date = request.form['date']
        time = request.form['time']
        meal_type_id = request.form['meal_type_id']
        food_item = request.form['food_item']
        quantity = request.form['quantity']
        calories = request.form.get('calories') or None
        notes = request.form.get('notes') or None

        conn.execute("""
            UPDATE food_log
            SET date=?, time=?, meal_type_id=?, food_item=?, quantity=?, calories=?, notes=?
            WHERE id=?
        """, (date, time, meal_type_id, food_item, quantity, calories, notes, id))
        conn.commit()
        conn.close()
        flash("✏️ Food entry updated!", "info")
        return redirect(url_for('food_bp.food_list'))

    conn.close()
    return render_template('food_form.html', action="Edit", food=food, meal_types=meal_types)

@food_bp.route('/food/delete/<int:id>')
def delete_food(id):
    conn = get_connection()
    conn.execute("DELETE FROM food_log WHERE id=?", (id,))
    conn.commit()
    conn.close()
    flash("🗑️ Food entry deleted!", "danger")
    return redirect(url_for('food_bp.food_list'))

# ---- Export/import food log -----

# --- EXPORT CSV ---
@food_bp.route('/food/export_csv')
def export_food_csv():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT fl.id, fl.date, fl.time, mt.name AS meal_type, fl.food_item, fl.quantity, fl.calories, fl.notes
        FROM food_log fl
        JOIN meal_types mt ON fl.meal_type_id = mt.id
        ORDER BY fl.date DESC, fl.time
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
                     download_name='food_log.csv')

# --- EXPORT JSON ---
@food_bp.route('/food/export_json')
def export_food_json():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT fl.id, fl.date, fl.time, mt.name AS meal_type, fl.food_item, fl.quantity, fl.calories, fl.notes
        FROM food_log fl
        JOIN meal_types mt ON fl.meal_type_id = mt.id
        ORDER BY fl.date DESC, fl.time
    """)
    rows = [dict(zip([col[0] for col in cur.description], row)) for row in cur.fetchall()]
    return jsonify(rows)

# --- IMPORT CSV ---
@food_bp.route('/food/import_csv', methods=['GET', 'POST'])
def import_food_csv():
    if request.method == 'POST':
        file = request.files['file']
        if not file:
            flash('No file uploaded', 'error')
            return redirect(url_for('food_bp.food_log'))
        stream = io.StringIO(file.stream.read().decode("UTF8"), newline=None)
        reader = csv.DictReader(stream)

        conn = get_connection()
        cur = conn.cursor()

        for row in reader:
            # Ensure meal type exists or create it
            meal_type_name = row.get('meal_type') or 'Unknown'
            cur.execute("SELECT id FROM meal_types WHERE name = ?", (meal_type_name,))
            meal_type = cur.fetchone()
            if not meal_type:
                cur.execute("INSERT INTO meal_types (name) VALUES (?)", (meal_type_name,))
                meal_type_id = cur.lastrowid
            else:
                meal_type_id = meal_type[0]

            # Insert food log
            cur.execute("""
                INSERT INTO food_log (date, time, meal_type_id, food_item, quantity, calories, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                row.get('date'),
                row.get('time'),
                meal_type_id,
                row.get('food_item'),
                row.get('quantity'),
                row.get('calories'),
                row.get('notes')
            ))

        conn.commit()
        conn.close()
        flash('Food log imported successfully!', 'success')
        return redirect(url_for('food_bp.food_log'))

    return render_template('import_food.html')