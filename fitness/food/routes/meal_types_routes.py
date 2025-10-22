from flask import render_template, request, redirect, url_for, flash, jsonify, send_file
from fitness.db.db import get_connection
from fitness.utils.helpers import calculate_pace
from fitness.food import food_bp
import csv, io

# ---------- Meal Types CRUD ----------


@food_bp.route('/meal_types')
def meal_types():
    conn = get_connection()
    meal_types = conn.execute("SELECT * FROM meal_types ORDER BY name").fetchall()
    conn.close()
    return render_template('meal_types_list.html', meal_types=meal_types)

@food_bp.route('/meal_types/add', methods=['GET', 'POST'])
def add_meal_type():
    if request.method == 'POST':
        name = request.form['name']
        conn = get_connection()
        conn.execute("INSERT INTO meal_types (name) VALUES (?)", (name,))
        conn.commit()
        conn.close()
        flash("✅ Meal type added successfully!", "success")
        return redirect(url_for('food_bp.meal_types'))
    return render_template('meal_types_form.html', action="Add", type_data=None)

@food_bp.route('/meal_types/edit/<int:id>', methods=['GET', 'POST'])
def edit_meal_type(id):
    conn = get_connection()
    type_data = conn.execute("SELECT * FROM meal_types WHERE id=?", (id,)).fetchone()
    if request.method == 'POST':
        name = request.form['name']
        conn.execute("UPDATE meal_types SET name=? WHERE id=?", (name, id))
        conn.commit()
        conn.close()
        flash("✏️ Meal type updated!", "info")
        return redirect(url_for('food_bp.meal_types'))
    conn.close()
    return render_template('meal_types_form.html', action="Edit", type_data=type_data)

@food_bp.route('/meal_types/delete/<int:id>')
def delete_meal_type(id):
    conn = get_connection()
    conn.execute("DELETE FROM meal_types WHERE id=?", (id,))
    conn.commit()
    conn.close()
    flash("🗑️ Meal type deleted!", "danger")
    return redirect(url_for('food_bp.meal_types'))