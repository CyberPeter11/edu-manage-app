from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import database

app = Flask(__name__)
app.secret_key = 'super_secret_dev_key_for_school_management'

# Initialize database on startup
database.init_db()

# --- Auth Setup ---
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'warning'

class User(UserMixin):
    def __init__(self, user_dict):
        self.id = user_dict['id']
        self.name = user_dict['name']
        self.email = user_dict['email']
        self.role = user_dict['role']
        self.phone = user_dict['phone']
        self.status = user_dict['status']

@login_manager.user_loader
def load_user(user_id):
    user_dict = database.get_user_by_id(user_id)
    if user_dict:
        return User(user_dict)
    return None

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
        
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user_dict = database.get_user_by_email(email)
        if user_dict and database.verify_password(user_dict['password_hash'], password):
            user = User(user_dict)
            login_user(user)
            flash(f'Welcome back, {user.name}!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password', 'error')
            
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'success')
    return redirect(url_for('login'))

@app.context_processor
def inject_unread_count():
    if current_user.is_authenticated:
        count = database.get_unread_count(current_user.id)
        return dict(unread_messages_count=count)
    return dict(unread_messages_count=0)

# --- Main Routes ---
@app.route('/')
@login_required
def dashboard():
    notices = database.get_notices()
    if current_user.role == 'Admin':
        stats = database.get_stats()
        recent_students = database.get_all_users_by_role('Student')[:5]
        return render_template('dashboard.html', stats=stats, recent_students=recent_students, notices=notices)
    elif current_user.role in ['Student', 'Parent']:
        attendance = database.get_student_attendance(current_user.id)
        results = database.get_student_results(current_user.id)
        behavior = database.get_student_behavior(current_user.id)
        rewards = database.get_student_rewards(current_user.id)
        return render_template('dashboard_student.html', attendance=attendance, results=results, behavior=behavior, rewards=rewards, notices=notices)
    else:
        return render_template('dashboard_user.html', role=current_user.role, notices=notices)

@app.route('/students')
@login_required
def students():
    if current_user.role != 'Admin':
        flash('Access denied. Admin only.', 'error')
        return redirect(url_for('dashboard'))
        
    all_students = database.get_all_users_by_role('Student')
    return render_template('students.html', students=all_students)

@app.route('/teachers')
@login_required
def teachers():
    if current_user.role != 'Admin':
        flash('Access denied. Admin only.', 'error')
        return redirect(url_for('dashboard'))
        
    all_teachers = database.get_all_users_by_role('Teacher')
    return render_template('teachers.html', teachers=all_teachers)

@app.route('/students/add', methods=['POST'])
@login_required
def add_student():
    if current_user.role != 'Admin':
        flash('Access denied. Admin only.', 'error')
        return redirect(url_for('dashboard'))

    name = f"{request.form.get('first_name')} {request.form.get('last_name')}"
    email = request.form.get('email')
    phone = request.form.get('phone', '')
    address = request.form.get('address', '')
    grade = request.form.get('grade')
    section = request.form.get('section')
    
    import string
    import random
    password = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
    
    user_id = database.create_user(name, email, password, role='Student', phone=phone, address=address)
    if user_id:
        database.enroll_student(user_id, grade, section)
        flash(f'Student enrolled successfully! Temporary Password: {password}', 'success')
    else:
        flash('Email already exists. Student enrollment failed.', 'error')
        
    return redirect(url_for('students'))

@app.route('/student/<int:id>/safety', methods=['GET', 'POST'])
@login_required
def student_safety(id):
    if current_user.role not in ['Admin', 'Parent', 'Student']:
        flash('Access denied.', 'error')
        return redirect(url_for('dashboard'))
    
    if current_user.role in ['Student', 'Parent'] and current_user.id != id:
        flash('Access denied.', 'error')
        return redirect(url_for('dashboard'))

    student = database.get_user_by_id(id)
    if not student or student['role'] != 'Student':
        flash('Student not found.', 'error')
        return redirect(url_for('dashboard'))

    if request.method == 'POST' and current_user.role == 'Admin':
        allergies = request.form.get('allergies', '')
        meds = request.form.get('medical_conditions', '')
        contact = request.form.get('emergency_contact', '')
        database.update_health_profile(id, allergies, meds, contact)
        
        adult_name = request.form.get('adult_name')
        if adult_name:
            phone = request.form.get('adult_phone', '')
            relation = request.form.get('relation', '')
            database.add_pickup_auth(id, adult_name, phone, relation)
            
        flash('Safety profile updated.', 'success')
        return redirect(url_for('student_safety', id=id))

    health = database.get_health_profile(id)
    pickups = database.get_pickup_auth(id)
    return render_template('safety.html', student=student, health=health, pickups=pickups)

@app.route('/teacher/attendance', methods=['GET', 'POST'])
@login_required
def attendance():
    if current_user.role != 'Teacher':
        flash('Access denied. Teacher only.', 'error')
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        student_id = request.form.get('student_id')
        course_id = request.form.get('course_id') 
        status = request.form.get('status')
        from datetime import date
        today = date.today().isoformat()
        database.mark_attendance(student_id, course_id, today, status)
        flash('Attendance recorded successfully!', 'success')
        return redirect(url_for('attendance'))

    students = database.get_students()
    courses = database.get_teacher_courses(current_user.id)
    return render_template('attendance.html', students=students, courses=courses)

@app.route('/teacher/results', methods=['GET', 'POST'])
@login_required
def results():
    if current_user.role != 'Teacher':
        flash('Access denied. Teacher only.', 'error')
        return redirect(url_for('dashboard'))
        
    if request.method == 'POST':
        student_id = request.form.get('student_id')
        exam_id = request.form.get('exam_id')
        marks = request.form.get('marks')
        database.record_marks(student_id, exam_id, marks)
        flash('Result recorded successfully!', 'success')
        return redirect(url_for('results'))

    students = database.get_students()
    courses = database.get_teacher_courses(current_user.id)
    conn = database.get_db_connection()
    exams = conn.execute('SELECT * FROM exams').fetchall()
    conn.close()
    
    return render_template('results.html', students=students, courses=courses, exams=exams)

@app.route('/teacher/behavior', methods=['GET', 'POST'])
@login_required
def teacher_behavior():
    if current_user.role != 'Teacher':
        flash('Access denied. Teacher only.', 'error')
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        student_id = request.form.get('student_id')
        teamwork = request.form.get('teamwork')
        listening = request.form.get('listening')
        behavior = request.form.get('behavior')
        comments = request.form.get('comments')
        
        from datetime import date
        today = date.today().isoformat()
        
        database.record_behavior(student_id, current_user.id, today, teamwork, listening, behavior, comments)
        flash('Behavior report submitted!', 'success')
        return redirect(url_for('teacher_behavior'))
        
    students = database.get_students()
    return render_template('behavior.html', students=students)

@app.route('/teacher/rewards', methods=['GET', 'POST'])
@login_required
def teacher_rewards():
    if current_user.role != 'Teacher':
        flash('Access denied. Teacher only.', 'error')
        return redirect(url_for('dashboard'))
        
    if request.method == 'POST':
        student_id = request.form.get('student_id')
        points = request.form.get('points')
        reason = request.form.get('reason')
        
        from datetime import date
        today = date.today().isoformat()
        
        database.award_reward(student_id, points, reason, today)
        flash(f'Awarded {points} stars!', 'success')
        return redirect(url_for('teacher_rewards'))
        
    students = database.get_students()
    return render_template('rewards.html', students=students)

@app.route('/teacher/notice', methods=['POST'])
@login_required
def post_notice():
    if current_user.role != 'Teacher':
        flash('Access denied. Teacher only.', 'error')
        return redirect(url_for('dashboard'))
        
    message = request.form.get('message')
    
    from datetime import date
    today = date.today().isoformat()
    
    database.add_notice(current_user.id, None, message, today)
    flash('Notice posted to the board!', 'success')
    return redirect(url_for('dashboard'))

# --- Messaging Routes (Phase 4) ---
@app.route('/messages', methods=['GET'])
@login_required
def messages():
    inbox = database.get_inbox(current_user.id)
    users = database.get_all_users_for_messaging()
    return render_template('messages.html', inbox=inbox, users=users)

@app.route('/messages/send', methods=['POST'])
@login_required
def send_message():
    receiver_id = request.form.get('receiver_id')
    subject = request.form.get('subject')
    body = request.form.get('body')
    database.send_message(current_user.id, receiver_id, subject, body)
    flash('Message sent successfully!', 'success')
    return redirect(url_for('messages'))

@app.route('/messages/read/<int:id>')
@login_required
def read_message(id):
    database.mark_message_read(id, current_user.id)
    return redirect(url_for('messages'))

# --- Report Card Route (Phase 4) ---
@app.route('/student/<int:id>/report')
@login_required
def student_report(id):
    if current_user.role not in ['Admin', 'Teacher', 'Parent', 'Student']:
        flash('Access denied.', 'error')
        return redirect(url_for('dashboard'))
        
    if current_user.role in ['Student', 'Parent'] and current_user.id != id:
        flash('Access denied.', 'error')
        return redirect(url_for('dashboard'))

    student = database.get_user_by_id(id)
    if not student or student['role'] != 'Student':
        flash('Student not found.', 'error')
        return redirect(url_for('dashboard'))

    attendance = database.get_student_attendance(id)
    results = database.get_student_results(id)
    behavior = database.get_student_behavior(id)
    rewards = database.get_student_rewards(id)
    
    return render_template('report_card.html', student=student, attendance=attendance, results=results, behavior=behavior, rewards=rewards)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
