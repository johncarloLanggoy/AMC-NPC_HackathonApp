# fix_admin.py
from app import app, db
from models import User

with app.app_context():
    # Check if admin exists
    admin = User.query.filter_by(username='admin').first()
    
    if admin:
        print(f"Admin found: {admin.username}")
        print(f"Email: {admin.email}")
        print(f"Full Name: {admin.full_name}")
        print(f"Is Active: {admin.is_active}")
        
        # Test password
        if admin.check_password('admin123'):
            print("Password 'admin123' is CORRECT!")
        else:
            print("Password 'admin123' is INCORRECT")
            # Reset password
            admin.set_password('admin123')
            db.session.commit()
            print("Password has been RESET to 'admin123'")
    else:
        print("Admin not found! Creating admin...")
        admin = User(
            username='admin',
            email='admin@university.edu',
            full_name='System Administrator',
            role='admin',
            department='Administration',
            is_active=True
        )
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
        print("Admin created with username 'admin' and password 'admin123'")
    
    print("\n" + "="*50)
    print("All users in database:")
    print("="*50)
    for user in User.query.all():
        print(f"  - {user.username} ({user.role}) - Active: {user.is_active}")