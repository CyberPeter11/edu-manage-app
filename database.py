import sqlite3
import os
from werkzeug.security import generate_password_hash, check_password_hash

# We will use a new database file for the overhauled schema
DB_PATH = 'school.db'

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    # Enable foreign keys
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    conn = get_db_connection()
    with conn:
        # Users Table (Person base class + Role)
        conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL CHECK(role IN ('Admin', 'Teacher', 'Student', 'Parent')),
                phone TEXT,
                address TEXT,
                status TEXT DEFAULT 'Active'
            )
        ''')
        
        # Classrooms Table
        conn.execute('''
            CREATE TABLE IF NOT EXISTS classrooms (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                grade TEXT NOT NULL,
                section TEXT NOT NULL
            )
        ''')
        
        # Students Specific Info (Extension of Users table)
        conn.execute('''
            CREATE TABLE IF NOT EXISTS student_info (
                user_id INTEGER PRIMARY KEY,
                classroom_id INTEGER,
                parent_id INTEGER,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
                FOREIGN KEY (classroom_id) REFERENCES classrooms (id),
                FOREIGN KEY (parent_id) REFERENCES users (id)
            )
        ''')
        
        # Courses Table
        conn.execute('''
            CREATE TABLE IF NOT EXISTS courses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                teacher_id INTEGER,
                FOREIGN KEY (teacher_id) REFERENCES users (id)
            )
        ''')
        
        # Attendance Table
        conn.execute('''
            CREATE TABLE IF NOT EXISTS attendance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER NOT NULL,
                course_id INTEGER,
                date DATE NOT NULL,
                status TEXT NOT NULL CHECK(status IN ('Present', 'Absent', 'Late')),
                FOREIGN KEY (student_id) REFERENCES users (id),
                FOREIGN KEY (course_id) REFERENCES courses (id)
            )
        ''')
        
        # Exams & Results
        conn.execute('''
            CREATE TABLE IF NOT EXISTS exams (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                date DATE NOT NULL,
                course_id INTEGER NOT NULL,
                FOREIGN KEY (course_id) REFERENCES courses (id)
            )
        ''')
        
        conn.execute('''
            CREATE TABLE IF NOT EXISTS results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                exam_id INTEGER NOT NULL,
                student_id INTEGER NOT NULL,
                marks REAL NOT NULL,
                FOREIGN KEY (exam_id) REFERENCES exams (id),
                FOREIGN KEY (student_id) REFERENCES users (id)
            )
        ''')
        
        # Health Profiles
        conn.execute('''
            CREATE TABLE IF NOT EXISTS health_profiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER NOT NULL UNIQUE,
                allergies TEXT,
                medical_conditions TEXT,
                emergency_contact TEXT,
                FOREIGN KEY (student_id) REFERENCES users (id) ON DELETE CASCADE
            )
        ''')
        
        # Pickup Authorization
        conn.execute('''
            CREATE TABLE IF NOT EXISTS pickup_auth (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER NOT NULL,
                adult_name TEXT NOT NULL,
                phone TEXT NOT NULL,
                relation TEXT,
                FOREIGN KEY (student_id) REFERENCES users (id) ON DELETE CASCADE
            )
        ''')
        
        # Behavior Reports
        conn.execute('''
            CREATE TABLE IF NOT EXISTS behavior_reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER NOT NULL,
                teacher_id INTEGER NOT NULL,
                date DATE NOT NULL,
                teamwork_rating TEXT,
                listening_rating TEXT,
                behavior_rating TEXT,
                comments TEXT,
                FOREIGN KEY (student_id) REFERENCES users (id) ON DELETE CASCADE,
                FOREIGN KEY (teacher_id) REFERENCES users (id)
            )
        ''')
        
        # Rewards
        conn.execute('''
            CREATE TABLE IF NOT EXISTS rewards (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER NOT NULL,
                points INTEGER NOT NULL,
                reason TEXT,
                date DATE NOT NULL,
                FOREIGN KEY (student_id) REFERENCES users (id) ON DELETE CASCADE
            )
        ''')
        
        # Notices
        conn.execute('''
            CREATE TABLE IF NOT EXISTS notices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                teacher_id INTEGER NOT NULL,
                classroom_id INTEGER,
                message TEXT NOT NULL,
                date DATE NOT NULL,
                FOREIGN KEY (teacher_id) REFERENCES users (id),
                FOREIGN KEY (classroom_id) REFERENCES classrooms (id)
            )
        ''')
        
        # Seed an initial Admin user if table is empty
        cursor = conn.execute('SELECT COUNT(*) FROM users WHERE role = "Admin"')
        if cursor.fetchone()[0] == 0:
            default_pw = generate_password_hash('admin123')
            conn.execute('''
                INSERT INTO users (name, email, password_hash, role) 
                VALUES ('Super Admin', 'admin@school.com', ?, 'Admin')
            ''', (default_pw,))
            
        # Seed an initial Teacher user
        cursor = conn.execute("SELECT COUNT(*) FROM users WHERE role = 'Teacher'")
        if cursor.fetchone()[0] == 0:
            teacher_pw = generate_password_hash('teacher123')
            conn.execute('''
                INSERT INTO users (name, email, password_hash, role) 
                VALUES ('Jane Doe', 'teacher@school.com', ?, 'Teacher')
            ''', (teacher_pw,))
            
        # Seed an initial Student user
        cursor = conn.execute("SELECT COUNT(*) FROM users WHERE role = 'Student'")
        if cursor.fetchone()[0] == 0:
            student_pw = generate_password_hash('student123')
            conn.execute('''
                INSERT INTO users (name, email, password_hash, role) 
                VALUES ('Alex Smith', 'student@school.com', ?, 'Student')
            ''', (student_pw,))
            
        # Seed Primary School Courses
        cursor = conn.execute("SELECT COUNT(*) FROM courses")
        if cursor.fetchone()[0] == 0:
            courses = [
                ('Mathematics', 'Basic numeracy and arithmetic'),
                ('English Language Arts', 'Reading, writing, and phonics'),
                ('Science', 'Basic environmental science'),
                ('Social Studies', 'History and geography'),
                ('Physical Education', 'P.E. and sports'),
                ('Art & Design', 'Creative arts and crafts'),
                ('Music', 'Vocal and instrumental music'),
                ('Information Technology', 'Basic computer skills')
            ]
            conn.executemany('INSERT INTO courses (name, description) VALUES (?, ?)', courses)
            
    conn.close()

# --- User Auth Helpers ---
def get_user_by_email(email):
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
    conn.close()
    return dict(user) if user else None

def get_user_by_id(user_id):
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    conn.close()
    return dict(user) if user else None

def verify_password(stored_hash, password):
    return check_password_hash(stored_hash, password)

def create_user(name, email, password, role, phone='', address=''):
    conn = get_db_connection()
    password_hash = generate_password_hash(password)
    try:
        cursor = conn.execute('''
            INSERT INTO users (name, email, password_hash, role, phone, address)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (name, email, password_hash, role, phone, address))
        user_id = cursor.lastrowid
        conn.commit()
        return user_id
    except sqlite3.IntegrityError:
        return None
    finally:
        conn.close()

def enroll_student(user_id, grade, section):
    conn = get_db_connection()
    try:
        cursor = conn.execute('SELECT id FROM classrooms WHERE grade = ? AND section = ?', (grade, section))
        row = cursor.fetchone()
        if row:
            classroom_id = row['id']
        else:
            cursor = conn.execute('INSERT INTO classrooms (grade, section) VALUES (?, ?)', (grade, section))
            classroom_id = cursor.lastrowid
            
        conn.execute('INSERT INTO student_info (user_id, classroom_id) VALUES (?, ?)', (user_id, classroom_id))
        conn.commit()
        return True
    except Exception as e:
        print("Error enrolling student:", e)
        return False
    finally:
        conn.close()

# --- Teacher Helpers ---
def get_teacher_courses(teacher_id):
    conn = get_db_connection()
    courses = conn.execute('SELECT * FROM courses WHERE teacher_id = ?', (teacher_id,)).fetchall()
    conn.close()
    return [dict(c) for c in courses]

def get_students():
    # Return all students to simplify assigning attendance/grades for prototype
    conn = get_db_connection()
    users = conn.execute("SELECT u.*, c.grade, c.section FROM users u LEFT JOIN student_info si ON u.id = si.user_id LEFT JOIN classrooms c ON si.classroom_id = c.id WHERE u.role = 'Student'").fetchall()
    conn.close()
    return [dict(u) for u in users]

def mark_attendance(student_id, course_id, date, status):
    conn = get_db_connection()
    try:
        conn.execute('''
            INSERT INTO attendance (student_id, course_id, date, status) 
            VALUES (?, ?, ?, ?)
        ''', (student_id, course_id, date, status))
        conn.commit()
    finally:
        conn.close()

def record_marks(student_id, exam_id, marks):
    conn = get_db_connection()
    try:
        conn.execute('''
            INSERT INTO results (student_id, exam_id, marks) 
            VALUES (?, ?, ?)
        ''', (student_id, exam_id, marks))
        conn.commit()
    finally:
        conn.close()

def record_behavior(student_id, teacher_id, date, teamwork, listening, behavior, comments):
    conn = get_db_connection()
    try:
        conn.execute('''
            INSERT INTO behavior_reports (student_id, teacher_id, date, teamwork_rating, listening_rating, behavior_rating, comments)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (student_id, teacher_id, date, teamwork, listening, behavior, comments))
        conn.commit()
    finally:
        conn.close()

def award_reward(student_id, points, reason, date):
    conn = get_db_connection()
    try:
        conn.execute('''
            INSERT INTO rewards (student_id, points, reason, date)
            VALUES (?, ?, ?, ?)
        ''', (student_id, points, reason, date))
        conn.commit()
    finally:
        conn.close()

# --- Student/Parent Helpers ---
def get_student_attendance(student_id):
    conn = get_db_connection()
    query = '''
        SELECT a.date, a.status, c.name as course_name 
        FROM attendance a
        LEFT JOIN courses c ON a.course_id = c.id
        WHERE a.student_id = ?
        ORDER BY a.date DESC
    '''
    records = conn.execute(query, (student_id,)).fetchall()
    conn.close()
    return [dict(r) for r in records]

def get_student_results(student_id):
    conn = get_db_connection()
    query = '''
        SELECT r.marks, e.name as exam_name, e.date as exam_date
        FROM results r
        JOIN exams e ON r.exam_id = e.id
        WHERE r.student_id = ?
        ORDER BY e.date DESC
    '''
    records = conn.execute(query, (student_id,)).fetchall()
    conn.close()
    return [dict(r) for r in records]

def get_student_behavior(student_id):
    conn = get_db_connection()
    query = '''
        SELECT b.*, u.name as teacher_name
        FROM behavior_reports b
        JOIN users u ON b.teacher_id = u.id
        WHERE b.student_id = ?
        ORDER BY b.date DESC
    '''
    records = conn.execute(query, (student_id,)).fetchall()
    conn.close()
    return [dict(r) for r in records]

def get_student_rewards(student_id):
    conn = get_db_connection()
    query = 'SELECT * FROM rewards WHERE student_id = ? ORDER BY date DESC'
    records = conn.execute(query, (student_id,)).fetchall()
    conn.close()
    return [dict(r) for r in records]

# --- Health & Safety Helpers ---
def get_health_profile(student_id):
    conn = get_db_connection()
    profile = conn.execute('SELECT * FROM health_profiles WHERE student_id = ?', (student_id,)).fetchone()
    conn.close()
    return dict(profile) if profile else None

def update_health_profile(student_id, allergies, medical_conditions, emergency_contact):
    conn = get_db_connection()
    try:
        conn.execute('''
            INSERT INTO health_profiles (student_id, allergies, medical_conditions, emergency_contact)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(student_id) DO UPDATE SET
                allergies=excluded.allergies,
                medical_conditions=excluded.medical_conditions,
                emergency_contact=excluded.emergency_contact
        ''', (student_id, allergies, medical_conditions, emergency_contact))
        conn.commit()
    finally:
        conn.close()

def get_pickup_auth(student_id):
    conn = get_db_connection()
    auths = conn.execute('SELECT * FROM pickup_auth WHERE student_id = ?', (student_id,)).fetchall()
    conn.close()
    return [dict(a) for a in auths]

def add_pickup_auth(student_id, adult_name, phone, relation):
    conn = get_db_connection()
    try:
        conn.execute('''
            INSERT INTO pickup_auth (student_id, adult_name, phone, relation)
            VALUES (?, ?, ?, ?)
        ''', (student_id, adult_name, phone, relation))
        conn.commit()
    finally:
        conn.close()

# --- Admin Helpers ---
def get_all_users_by_role(role):
    conn = get_db_connection()
    if role == 'Student':
        query = '''
            SELECT u.*, c.grade, c.section 
            FROM users u
            LEFT JOIN student_info si ON u.id = si.user_id
            LEFT JOIN classrooms c ON si.classroom_id = c.id
            WHERE u.role = 'Student'
            ORDER BY u.id DESC
        '''
        users = conn.execute(query).fetchall()
    else:
        users = conn.execute('SELECT * FROM users WHERE role = ? ORDER BY id DESC', (role,)).fetchall()
    conn.close()
    return [dict(u) for u in users]

def get_stats():
    conn = get_db_connection()
    students = conn.execute("SELECT COUNT(*) FROM users WHERE role = 'Student'").fetchone()[0]
    teachers = conn.execute("SELECT COUNT(*) FROM users WHERE role = 'Teacher'").fetchone()[0]
    courses = conn.execute("SELECT COUNT(*) FROM courses").fetchone()[0]
    conn.close()
    return {
        'total_students': students,
        'total_teachers': teachers,
        'total_courses': courses
    }

# --- Notice Board Helpers ---
def add_notice(teacher_id, classroom_id, message, date):
    conn = get_db_connection()
    try:
        conn.execute('''
            INSERT INTO notices (teacher_id, classroom_id, message, date)
            VALUES (?, ?, ?, ?)
        ''', (teacher_id, classroom_id, message, date))
        conn.commit()
    finally:
        conn.close()

def get_notices():
    conn = get_db_connection()
    query = '''
        SELECT n.*, u.name as teacher_name, c.grade, c.section
        FROM notices n
        JOIN users u ON n.teacher_id = u.id
        LEFT JOIN classrooms c ON n.classroom_id = c.id
        ORDER BY n.date DESC LIMIT 10
    '''
    records = conn.execute(query).fetchall()
    conn.close()
    return [dict(r) for r in records]

if __name__ == '__main__':
    init_db()
    print("School database initialized successfully.")
