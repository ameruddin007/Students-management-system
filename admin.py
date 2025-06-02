# import os
# from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
# from flask_sqlalchemy import SQLAlchemy
# from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
# from werkzeug.security import generate_password_hash, check_password_hash

# app = Flask(__name__)
# app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(os.path.abspath(os.path.dirname(__file__)), 'college_exam.db')
# app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your_secret_key')
# db = SQLAlchemy(app)
# login_manager = LoginManager(app)
# login_manager.login_view = 'login'

# # Database Models
# class Student(UserMixin, db.Model):
#     __tablename__ = 'students'
#     id = db.Column(db.Integer, primary_key=True)
#     roll_number = db.Column(db.String(20), unique=True, nullable=False)
#     name = db.Column(db.String(100), nullable=False)
#     course_name = db.Column(db.String(100), nullable=False)
#     year = db.Column(db.Integer, nullable=False)
#     profile_image = db.Column(db.String(100), default='default.jpg')
#     password_hash = db.Column(db.String(200), nullable=False)

#     def set_password(self, password):
#         self.password_hash = generate_password_hash(password, method='pbkdf2:sha256')
    
#     def check_password(self, password):
#         return check_password_hash(self.password_hash, password)

# class Course(db.Model):
#     __tablename__ = 'courses'
#     id = db.Column(db.String(100), primary_key=True)
#     course_name = db.Column(db.String(100), nullable=False)
#     duration = db.Column(db.String(100), nullable=False)

# class Exam(db.Model):
#     __tablename__ = 'exams'
#     id = db.Column(db.Integer, primary_key=True)
#     exam_name = db.Column(db.String(100), nullable=False)
#     semester = db.Column(db.Integer, nullable=False)
#     date = db.Column(db.String(20), nullable=False)

# class Result(db.Model):
#     __tablename__ = 'results'
#     id = db.Column(db.Integer, primary_key=True)
#     student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
#     exam_id = db.Column(db.Integer, db.ForeignKey('exams.id'), nullable=False)
#     marks = db.Column(db.Integer, nullable=False)
#     grade = db.Column(db.String(5), nullable=False)

# class Admin(UserMixin, db.Model):
#     __tablename__ = 'admins'
#     id = db.Column(db.Integer, primary_key=True)
#     username = db.Column(db.String(80), unique=True, nullable=False)
#     password_hash = db.Column(db.String(128), nullable=False)

#     def set_password(self, password):
#         self.password_hash = generate_password_hash(password)

#     def check_password(self, password):
#         return check_password_hash(self.password_hash, password)

# @login_manager.user_loader
# def load_user(user_id):
#     # Corrected to check Admin first, then Student
#     user = Admin.query.get(int(user_id)) or Student.query.get(int(user_id))
#     return user

# @app.route('/login', methods=['GET', 'POST'])
# def login():
#     if request.method == 'POST':
#         username = request.form['username']
#         password = request.form['password']
#         user_type = request.form['user_type']

#         if user_type == 'student':
#             user = Student.query.filter_by(roll_number=username).first()
#         elif user_type == 'admin':
#             user = Admin.query.filter_by(username=username).first()
#         else:
#             flash('Invalid user type', 'danger')
#             return redirect(url_for('login'))

#         if user and user.check_password(password):
#             login_user(user)
#             return redirect(url_for('dashboard') if user_type == 'student' else url_for('admin_dashboard'))
#         else:
#             flash('Invalid credentials', 'danger')
#     return render_template('login.html')

# @app.route('/logout')
# @login_required
# def logout():
#     logout_user()
#     return redirect(url_for('login'))

# @app.route('/dashboard')
# @login_required
# def dashboard():
#     # Corrected to use class name for type checking
#     if current_user.__class__.__name__ == 'Student':
#         results = Result.query.filter_by(student_id=current_user.id).all()
#         return render_template('dashboard.html', student=current_user, results=results)
#     else:
#         flash('Unauthorized access', 'danger')
#         return redirect(url_for('login'))

# @app.route('/admin/dashboard')
# @login_required
# def admin_dashboard():
#     # Corrected to use class name for type checking
#     if current_user.__class__.__name__ == 'Admin':
#         return render_template('admin_dashboard.html', admin=current_user)
#     else:
#         flash('Unauthorized access', 'danger')
#         return redirect(url_for('login'))

# @app.route('/add_student', methods=['GET', 'POST'])
# @login_required
# def add_student():
#     if current_user.__class__.__name__ != 'Admin':  # Corrected type check
#         flash("Unauthorized access", "danger")
#         return redirect(url_for('admin_dashboard'))

#     if request.method == 'POST':
#         name = request.form['name']
#         roll_number = request.form['roll_number']
#         course_name = request.form['course_name']
#         year = request.form['year']
#         password = request.form['password']

#         new_student = Student(
#             name=name,
#             roll_number=roll_number,
#             course_name=course_name,
#             year=year
#         )
#         new_student.set_password(password)

#         db.session.add(new_student)
#         db.session.commit()
#         flash("Student added successfully!", "success")
#         return redirect(url_for('admin_dashboard'))

#     return render_template('add_student.html')

# @app.route('/add_exam', methods=['GET', 'POST'])
# @login_required  # Added login requirement for exam addition

# def add_exam():
#     if current_user.__class__.__name__ != 'Admin':  # Ensured only admins can add exams
#         flash("Unauthorized access", "danger")
#         return redirect(url_for('admin_dashboard'))

#     if request.method == 'POST':
#         exam_name = request.form.get('exam_name')
#         exam_date = request.form.get('exam_date')

#         # Add logic to save exam details to the database

#         return redirect(url_for('admin_dashboard'))  # Redirect after adding exam
    
#     return render_template('add_exam.html')  # Render the form for GET request

# # API to add results with grade calculation
# @app.route('/add_result', methods=['POST'])
# @login_required
# def add_result():
#     if current_user.__class__.__name__ != 'Admin':  # Corrected type check
#         return jsonify({"message": "Unauthorized"}), 403

#     data = request.get_json()
#     student_id = data.get('student_id')
#     exam_id = data.get('exam_id')
#     marks = data.get('marks')

#     total_marks = sum(marks)  # Sum all subject marks
#     grade = calculate_grade(total_marks)  # Determine grade

#     new_result = Result(student_id=student_id, exam_id=exam_id, marks=total_marks, grade=grade)
#     db.session.add(new_result)
#     db.session.commit()

#     return jsonify({"message": "Result added successfully", "total_marks": total_marks, "grade": grade}), 201

# # Function to calculate grades
# def calculate_grade(total_marks):
#     if total_marks >= 90:
#         return 'O'
#     elif total_marks >= 80:
#         return 'A'
#     elif total_marks >= 70:
#         return 'B'
#     elif total_marks >= 60:
#         return 'C'
#     elif total_marks >= 50:
#         return 'D'
#     else:
#         return 'F'

# # Ensure database tables are created
# with app.app_context():
#     db.create_all()
    
#     # Pre-save admin login details
#     default_admin_username = "admin"
#     default_admin_password = "admin123"

#     existing_admin = Admin.query.filter_by(username=default_admin_username).first()  # Check if the specific admin exists
#     if not existing_admin:
#         new_admin = Admin(username=default_admin_username)
#         new_admin.set_password(default_admin_password)  # Hash the password
#         db.session.add(new_admin)
#         db.session.commit()
#         print("Default admin account created. Username: admin, Password: admin123")
#     else:
#         print("Admin account already exists.")

# if __name__ == '__main__':
#     app.run(debug=True)  # Corrected debug parameter to boolean