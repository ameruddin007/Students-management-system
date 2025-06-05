import os
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.exc import IntegrityError

app = Flask(__name__)

# Database configuration - uses PostgreSQL on Render, falls back to SQLite locally
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///college_exam.db').replace("postgres://", "postgresql://", 1)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-123')

# Connection pool settings optimized for Render
app.config.update({
    'SQLALCHEMY_ENGINE_OPTIONS': {
        'pool_size': 5,
        'max_overflow': 10,
        'pool_timeout': 30,
        'pool_recycle': 1800,  # Recycle connections after 30 minutes
        'pool_pre_ping': True   # Test connections for health before use
    },
    'SQLALCHEMY_TRACK_MODIFICATIONS': False
})

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# File upload configuration
UPLOAD_FOLDER = 'static/uploads/'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Database Models
class Student(UserMixin, db.Model):
    __tablename__ = 'students'
    
    student_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    course_name = db.Column(db.String(100), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    profile_image = db.Column(db.String(100), default='default.jpg')
    gender = db.Column(db.String(10), nullable=False)
    father_name = db.Column(db.String(100), nullable=False)
    medium = db.Column(db.String(50), nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256')

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_id(self):
        return str(self.student_id)

class Course(db.Model):
    __tablename__ = 'courses'
    id = db.Column(db.String(100), primary_key=True)
    course_name = db.Column(db.String(100), nullable=False)
    duration = db.Column(db.String(100), nullable=False)

class Exam(db.Model):
    __tablename__ = 'exams'
    id = db.Column(db.Integer, primary_key=True)
    exam_name = db.Column(db.String(100), nullable=False)
    semester = db.Column(db.Integer, nullable=False)
    date = db.Column(db.String(20), nullable=False)

class Result(db.Model):
    __tablename__ = 'results'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.student_id', ondelete='CASCADE'), nullable=False)
    exam_id = db.Column(db.Integer, db.ForeignKey('exams.id', ondelete='CASCADE'), nullable=True)
    marks = db.Column(db.Integer, nullable=False)
    grade = db.Column(db.String(5), nullable=False)

class Admin(UserMixin, db.Model):
    __tablename__ = 'admins'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    # Add any additional admin-specific fields here

    def __init__(self, username):
        self.username = username

    def set_password(self, password):
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256')

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_id(self):
        return str(self.id)

# Session management
@app.teardown_appcontext
def shutdown_session(exception=None):
    db.session.remove()

@login_manager.user_loader
def load_user(user_id):
    try:
        if user_id.isdigit():
            return Admin.query.get(int(user_id)) or Student.query.get(int(user_id))
        return None
    except Exception as e:
        db.session.rollback()
        return None

# Routes
@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    try:
        if request.method == 'POST':
            user_id = request.form['user_id']
            password = request.form['password']
            user_type = request.form['user_type']

            user = None
            if user_type == 'student':
                user = Student.query.filter_by(student_id=user_id).first()
            elif user_type == 'admin':
                user = Admin.query.filter_by(username=user_id).first()
            else:
                flash('Invalid user type', 'danger')
                return redirect(url_for('login'))

            if user:
                if user.check_password(password):
                    login_user(user)
                    flash('Login successful!', 'success')
                    
                    if user_type == 'student':
                        return redirect(url_for('dashboard'))
                    else:
                        return redirect(url_for('admin_dashboard'))
                else:
                    flash('Invalid password', 'danger')
            else:
                flash('User not found', 'danger')

            db.session.rollback()

        return render_template('login.html')
    except Exception as e:
        db.session.rollback()
        flash(f'An error occurred during login: {str(e)}', 'danger')
        return redirect(url_for('login'))

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    try:
        if isinstance(current_user, Student):
            student = current_user
            results = Result.query.filter_by(student_id=student.student_id).all()
            exams = {result.exam_id: Exam.query.get(result.exam_id) for result in results}
            db.session.commit()
            return render_template('dashboard.html', student=student, results=results, exams=exams)
        
        flash('Unauthorized access', 'danger')
        return redirect(url_for('login'))
    except Exception as e:
        db.session.rollback()
        flash('An error occurred', 'danger')
        return redirect(url_for('login'))

@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    if isinstance(current_user, Admin):
        return render_template('admin_dashboard.html', admin=current_user)
    flash('Unauthorized access', 'danger')
    return redirect(url_for('login'))

@app.route('/add_student', methods=['GET', 'POST'])
@login_required
def add_student():
    try:
        if not isinstance(current_user, Admin):
            flash("Unauthorized access", "danger")
            return redirect(url_for('admin_dashboard'))

        if request.method == 'POST':
            name = request.form['name']
            student_id = request.form['student_id']
            course_name = request.form['course_name']
            year = request.form['year']
            gender = request.form['gender']
            father_name = request.form['father_name']
            medium = request.form['medium']
            password = request.form['password']
            file = request.files['profile_image']

            filename = 'default.jpg'
            if file and file.filename != '':
                file_ext = file.filename.rsplit('.', 1)[1].lower()
                filename = f"{student_id}.{file_ext}"
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)

            new_student = Student(
                name=name,
                student_id=student_id,
                course_name=course_name,
                year=year,
                profile_image=filename,
                gender=gender,
                father_name=father_name,
                medium=medium
            )
            new_student.set_password(password)

            db.session.add(new_student)
            db.session.commit()
            flash("Student added successfully!", "success")
            return redirect(url_for('admin_dashboard'))
        return render_template('add_student.html')
    except IntegrityError:
        db.session.rollback()
        flash("Student ID already exists!", "danger")
        return render_template('add_student.html')
    except Exception as e:
        db.session.rollback()
        flash("An error occurred while adding student", "danger")
        return redirect(url_for('admin_dashboard'))


@app.route('/add_exam', methods=['GET', 'POST'])
@login_required
def add_exam():
    try:
        if not isinstance(current_user, Admin):
            flash("Unauthorized access", "danger")
            return redirect(url_for('admin_dashboard'))

        if request.method == 'POST':
            exam_name = request.form.get('exam_name')
            exam_date = request.form.get('exam_date')
            semester = request.form.get('semester')

            if not all([exam_name, exam_date, semester]):
                flash("All fields are required", "danger")
                return redirect(url_for('add_exam'))

            try:
                semester = int(semester)
            except ValueError:
                flash("Semester must be a number", "danger")
                return redirect(url_for('add_exam'))

            new_exam = Exam(
                exam_name=exam_name,
                date=exam_date,
                semester=semester
            )

            db.session.add(new_exam)
            db.session.commit()
            flash("Exam added successfully!", "success")
            return redirect(url_for('admin_dashboard'))
        
        return render_template('add_exam.html')
    
    except IntegrityError:
        db.session.rollback()
        flash("An exam with these details already exists!", "danger")
        return redirect(url_for('add_exam'))
    except Exception as e:
        db.session.rollback()
        flash(f"An error occurred while adding exam: {str(e)}", "danger")
        return redirect(url_for('admin_dashboard'))

@app.route('/add_result', methods=['GET', 'POST'])
@login_required
def add_result():
    try:
        if not isinstance(current_user, Admin):
            flash("Unauthorized access", "danger")
            return redirect(url_for('admin_dashboard'))

        students = Student.query.order_by(Student.name).all()
        exams = Exam.query.order_by(Exam.date.desc()).all()

        if request.method == 'POST':
            student_id = request.form.get('student_id')
            exam_id = request.form.get('exam_id')
            marks = request.form.get('marks')

            if not all([student_id, exam_id, marks]):
                flash("All fields are required", "danger")
                return redirect(url_for('add_result'))

            try:
                marks = int(marks)
                if marks < 0 or marks > 100:
                    flash("Marks must be between 0 and 100", "danger")
                    return redirect(url_for('add_result'))
            except ValueError:
                flash("Marks must be a number", "danger")
                return redirect(url_for('add_result'))

            # Check if result already exists
            existing_result = Result.query.filter_by(
                student_id=student_id,
                exam_id=exam_id
            ).first()

            if existing_result:
                flash("This student already has a result for this exam", "warning")
                return redirect(url_for('add_result'))

            grade = calculate_grade(marks)
            new_result = Result(
                student_id=student_id,
                exam_id=exam_id,
                marks=marks,
                grade=grade
            )

            db.session.add(new_result)
            db.session.commit()
            flash("Result added successfully!", "success")
            return redirect(url_for('admin_dashboard'))

        return render_template('add_result.html', students=students, exams=exams)
    
    except IntegrityError as e:
        db.session.rollback()
        flash("Database error occurred while adding result", "danger")
        return redirect(url_for('add_result'))
    except Exception as e:
        db.session.rollback()
        flash(f"An error occurred while adding result: {str(e)}", "danger")
        return redirect(url_for('admin_dashboard'))
    
def calculate_grade(marks):
    return 'O' if marks >= 90 else 'A' if marks >= 80 else 'B' if marks >= 70 else 'C' if marks >= 60 else 'D' if marks >= 50 else 'F'

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=os.environ.get('FLASK_DEBUG', 'False') == 'True')