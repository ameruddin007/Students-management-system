from student import db, Admin, app

# Replace with your desired credentials
username = 'admin'
password = 'admin123'

with app.app_context():
    db.create_all()  # Create tables if they don't exist

    # Check if admin already exists
    existing_admin = Admin.query.filter_by(username=username).first()
    if existing_admin:
        print(f"Admin user '{username}' already exists.")
    else:
        admin = Admin(username=username)
        admin.set_password(password)
        db.session.add(admin)
        db.session.commit()
        print(f"Admin user '{username}' created successfully!")