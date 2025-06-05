from student import db, Admin, app

def create_admin(username, password):
    with app.app_context():
        try:
            db.create_all()  # Create tables if they don't exist

            # Check if admin already exists
            existing_admin = Admin.query.filter_by(username=username).first()
            if existing_admin:
                print(f"Admin user '{username}' already exists.")
                return False

            admin = Admin(username=username)
            admin.set_password(password)
            db.session.add(admin)
            db.session.commit()
            print(f"Admin user '{username}' created successfully!")
            return True
        except Exception as e:
            db.session.rollback()
            print(f"Error creating admin: {str(e)}")
            return False

if __name__ == '__main__':
    # Replace with your desired credentials
    username = 'admin'
    password = 'admin123'
    create_admin(username, password)