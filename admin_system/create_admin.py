"""
Script to create a super admin account
Run this once after deployment to create your first admin user
"""

from app import app, db, Admin
from werkzeug.security import generate_password_hash

def create_admin(email, password):
    with app.app_context():
        # Check if admin already exists
        existing_admin = Admin.query.filter_by(email=email).first()
        if existing_admin:
            print(f"Admin with email {email} already exists!")
            return
        
        # Create new admin
        admin = Admin(
            email=email,
            password_hash=generate_password_hash(password),
            is_super_admin=True
        )
        
        db.session.add(admin)
        db.session.commit()
        
        print(f"✓ Super admin created successfully!")
        print(f"  Email: {email}")
        print(f"  Password: {password}")
        print(f"\nYou can now log in at your Render URL")

if __name__ == '__main__':
    # Default admin credentials
    create_admin('admin@sklgu.gov.ph', 'admin123')
