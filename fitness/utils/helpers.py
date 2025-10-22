# fitness/utils/helpers.py

from datetime import datetime

def format_date(date_str):
    """Convert various date formats (e.g. 7/30/2025) into YYYY-MM-DD."""
    try:
        parsed_date = datetime.strptime(date_str.strip(), "%m/%d/%Y")
        return parsed_date.strftime("%Y-%m-%d")
    except Exception:
        return date_str  # If already ISO or invalid

def format_time(time_str):
    """Normalize time strings like '9:30 AM' -> '09:30'."""
    try:
        parsed_time = datetime.strptime(time_str.strip(), "%I:%M %p")
        return parsed_time.strftime("%H:%M")
    except Exception:
        return time_str
    
def calculate_pace(distance, duration):
    if distance and duration and distance > 0:
        pace = duration / distance
        minutes = int(pace)
        seconds = int((pace - minutes) * 60)
        return f"{minutes}:{seconds:02d}"
    return None

def calculate_bmi(weight_lbs, height_inches=65):
    """Calculate BMI given weight in lbs and height in inches (default: 5'5" = 65 inches)."""
    try:
        weight_kg = float(weight_lbs) * 0.453592
        height_m = float(height_inches) * 0.0254
        return round(weight_kg / (height_m ** 2), 1)
    except Exception:
        return None

def to_dict(row, cursor):
    """Convert a SQLite row + cursor into a dictionary."""
    columns = [desc[0] for desc in cursor.description]
    return {columns[i]: row[i] for i in range(len(columns))}

def rows_to_dicts(rows, cursor):
    """Convert multiple SQLite rows into a list of dictionaries."""
    columns = [desc[0] for desc in cursor.description]
    return [dict(zip(columns, row)) for row in rows]

def safe_get(d, key, default=None):
    """Helper for safely getting dict values."""
    return d[key] if key in d and d[key] not in (None, "") else default
