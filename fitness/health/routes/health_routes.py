from flask import render_template, request, redirect, url_for, flash, jsonify, send_file
from fitness.db.db import get_connection
from fitness.utils.helpers import calculate_pace
from fitness.health import health_bp
import csv, io
import sqlite3


# =========================
# Health
# =========================

@health_bp.route('/health')
def health_list():
    conn = get_connection()
    cur = conn.cursor()
    rows = cur.execute("SELECT * FROM health_log ORDER BY date DESC, time DESC").fetchall()
    conn.close()
    return render_template('health_list.html', records=rows)


@health_bp.route('/health/add', methods=['GET', 'POST'])
def health_add():
    if request.method == 'POST':
        date = request.form['date']
        time = request.form['time']
        systolic = request.form.get('systolic')
        diastolic = request.form.get('diastolic')
        bpm = request.form.get('bpm')
        weight = request.form.get('weight')

        # Calculate BMI (height = 65 inches)
        bmi = None
        if weight:
            bmi = round(float(weight) * 703 / (65 * 65), 1)

        conn = get_connection()
        conn.execute("""
            INSERT INTO health_log (date, time, systolic, diastolic, bpm, weight, bmi)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (date, time, systolic, diastolic, bpm, weight, bmi))
        conn.commit()
        conn.close()
        return redirect(url_for('health_bp.health_list'))

    return render_template('health_form.html')

@health_bp.route('/health/edit/<int:id>', methods=['GET', 'POST'])
def health_edit(id):
    conn = get_connection()
    cur = conn.cursor()


    if request.method == 'POST':
        date = request.form['date']
        time = request.form['time']
        systolic = request.form.get('systolic')
        diastolic = request.form.get('diastolic')
        bpm = request.form.get('bpm')
        weight = request.form.get('weight')

        bmi = None
        if weight:
            bmi = round(float(weight) * 703 / (65 * 65), 1)

        cur.execute("""
            UPDATE health_log
            SET date=?, time=?, systolic=?, diastolic=?, bpm=?, weight=?, bmi=?
            WHERE id=?
        """, (date, time, systolic, diastolic, bpm, weight, bmi, id))
        conn.commit()
        conn.close()
        return redirect(url_for('health_bp.health_list'))

    record = cur.execute("SELECT * FROM health_log WHERE id=?", (id,)).fetchone()
    conn.close()
    return render_template('health_form.html', record=record)


@health_bp.route('/health/delete/<int:id>')
def health_delete(id):
    conn = get_connection()
    conn.execute("DELETE FROM health_log WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('health_bp.health_list'))

@health_bp.route('/health/dashboard')
def health_dashboard():
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    records = conn.execute("SELECT date, systolic, diastolic, bpm, weight, bmi FROM health_log ORDER BY date").fetchall()
    conn.close()

    dates = [r['date'] for r in records]
    systolic = [r['systolic'] for r in records]
    diastolic = [r['diastolic'] for r in records]
    bpm = [r['bpm'] for r in records]
    weight = [r['weight'] for r in records]
    bmi = [r['bmi'] for r in records]

    return render_template(
        'health_dashboard.html',
        dates=dates,
        systolic=systolic,
        diastolic=diastolic,
        bpm=bpm,
        weight=weight,
        bmi=bmi
    )


@health_bp.route('/health/import', methods=['GET', 'POST'])
def health_import():
    if request.method == 'POST':
        file = request.files.get('file')
        if not file or file.filename == '':
            return "No file selected", 400

        conn = get_connection()
        cur = conn.cursor()

        stream = StringIO(file.stream.read().decode('utf-8'))
        reader = csv.reader(stream)
        
        # Optionally skip header if first cell contains "Date"
        first_row = next(reader)
        if "date" not in first_row[0].lower():
            stream.seek(0)
            reader = csv.reader(stream)
        
        for row in reader:
            if not row or len(row) < 6:
                continue
            date_str, time_str, systolic, diastolic, bpm, weight = [c.strip() for c in row]
            
            # Normalize date (MM/DD/YYYY → YYYY-MM-DD)
            try:
                date = datetime.strptime(date_str, "%m/%d/%Y").strftime("%Y-%m-%d")
            except ValueError:
                date = date_str  # if already in correct format

            weight = float(weight) if weight else None
            systolic = int(systolic) if systolic else None
            diastolic = int(diastolic) if diastolic else None
            bpm = int(bpm) if bpm else None

            bmi = None
            if weight:
                bmi = round(weight * 703 / (65 * 65), 1)  # 5'5" = 65 inches

            cur.execute("""
                INSERT INTO health_log (date, time, systolic, diastolic, bpm, weight, bmi)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (date, time_str, systolic, diastolic, bpm, weight, bmi))
        
        conn.commit()
        conn.close()

        return redirect(url_for('health_bp.health_list'))


    return render_template('health_import.html')


@health_bp.route('/health/export')
def health_export():
    conn = get_connection()
    records = conn.execute("""
        SELECT date, time, systolic, diastolic, bpm, weight, bmi
        FROM health_log
        ORDER BY date
    """).fetchall()
    conn.close()

    # Build CSV content
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(["Date", "Time", "Systolic", "Diastolic", "BPM", "Weight (lbs)", "BMI"])

    for r in records:
        writer.writerow([
            r["date"],
            r["time"],
            r["systolic"],
            r["diastolic"],
            r["bpm"],
            r["weight"],
            r["bmi"]
        ])

    response = Response(output.getvalue(), mimetype="text/csv")
    response.headers["Content-Disposition"] = "attachment; filename=health_log.csv"
    return response

