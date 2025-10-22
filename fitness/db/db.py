import sqlite3
import os

# -------------------------------
# Database Location Setup
# -------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))   # directory of db.py
DB_PATH = os.path.join(BASE_DIR, "fitness.db")          # ensures DB is inside fitness/db

# Make sure the db directory exists (important if running from app.py)
os.makedirs(BASE_DIR, exist_ok=True)


# ---------------------------
# DB Setup
# ---------------------------
def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS activity_types (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        description TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS cardio_workouts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT NOT NULL,
        time TEXT,
        activity_type_id INTEGER NOT NULL,
        distance_miles REAL,
        duration_minutes REAL,
        pace_min_per_mile TEXT,
        avg_heart_rate INTEGER,
        calories_burned INTEGER,
        weight_lbs REAL,
        notes TEXT,
        FOREIGN KEY (activity_type_id) REFERENCES activity_types (id)
    )
    """)

    # Meal Types (lookup)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS meal_types (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE
        )
    """)

    # Food Log
    cur.execute("""
        CREATE TABLE IF NOT EXISTS food_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            time TEXT,
            meal_type_id INTEGER NOT NULL,
            food_item TEXT NOT NULL,
            quantity TEXT,
            calories INTEGER,
            notes TEXT,
            FOREIGN KEY (meal_type_id) REFERENCES meal_types(id)
        )
    """)

    # Prepopulate meal types if empty
    existing = cur.execute("SELECT COUNT(*) FROM meal_types").fetchone()[0]
    if existing == 0:
        cur.executemany("INSERT INTO meal_types (name) VALUES (?)",
                        [("Breakfast",), ("Lunch",), ("Dinner",), ("Snack",)])

    # Health Log
    cur.execute("""
        CREATE TABLE IF NOT EXISTS health_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            time TEXT,
            systolic INTEGER,
            diastolic INTEGER,
            bpm INTEGER,
            weight REAL,
            bmi REAL
        )
    """)

    # --- Strength / Weight Training Tables ---
    cur.execute("""
    CREATE TABLE IF NOT EXISTS exercise_types (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        body_part TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS workouts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT NOT NULL,
        time TEXT,
        body_part TEXT,
        notes TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS exercises (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        workout_id INTEGER NOT NULL,
        exercise_name TEXT NOT NULL,
        FOREIGN KEY (workout_id) REFERENCES workouts(id)
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS sets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        exercise_id INTEGER NOT NULL,
        set_number INTEGER,
        reps INTEGER,
        weight REAL,
        rest_seconds INTEGER,
        FOREIGN KEY (exercise_id) REFERENCES exercises(id)
    )
    """)

    # insert some common exercise types if table empty
    existing = cur.execute("SELECT COUNT(*) FROM exercise_types").fetchone()[0]
    if existing == 0:
        cur.executemany("INSERT INTO exercise_types (name, body_part) VALUES (?, ?)",
                        [
                            ('Barbell Bench Press', 'Chest'),
                            ('Incline Dumbbell Press', 'Chest'),
                            ('Back Squat', 'Legs'),
                            ('Deadlift', 'Legs'),
                            ('Lat Pulldown', 'Back'),
                            ('Face Pull', 'Back'),
                            ('Incline Dumbbell Curl', 'Biceps'),
                            ('Preacher Curl', 'Biceps'),
                            ('Triceps Rope Pressdown', 'Triceps')
                        ])

    conn.commit()
    conn.close()