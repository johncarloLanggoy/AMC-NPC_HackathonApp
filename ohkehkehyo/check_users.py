# check_users.py
from app import app, db
from models import User

with app.app_context():
    print("=" * 50)
    print("ALL USERS IN DATABASE")
    print("=" * 50)
    
    users = User.query.all()
    for user in users:
        print(f"Username: {user.username}")
        print(f"  Role: {user.role}")
        print(f"  Full Name: {user.full_name}")
        print(f"  Is Active: {user.is_active}")
        print(f"  Department: {user.department}")
        print("-" * 30)
    
    # Check specific users
    dean = User.query.filter_by(username='dean').first()
    ph_cs = User.query.filter_by(username='ph_cs').first()
    
    print("\n" + "=" * 50)
    print("CHECKING SPECIFIC USERS")
    print("=" * 50)
    
    if dean:
        print(f"✓ Dean found: {dean.username}")
        if dean.check_password('password123'):
            print("  ✓ Password 'password123' is CORRECT")
        else:
            print("  ✗ Password 'password123' is INCORRECT")
            # Reset password
            dean.set_password('password123')
            db.session.commit()
            print("  ✓ Password has been RESET to 'password123'")
    else:
        print("✗ Dean NOT found - creating...")
        dean = User(
            username='dean',
            email='dean@university.edu',
            full_name='Dr. Robert Taylor',
            role='dean',
            department='Academic Affairs',
            is_active=True
        )
        dean.set_password('password123')
        db.session.add(dean)
        db.session.commit()
        print("  ✓ Dean created with username 'dean', password 'password123'")
    
    if ph_cs:
        print(f"✓ Program Head found: {ph_cs.username}")
        if ph_cs.check_password('password123'):
            print("  ✓ Password 'password123' is CORRECT")
        else:
            print("  ✗ Password 'password123' is INCORRECT")
            ph_cs.set_password('password123')
            db.session.commit()
            print("  ✓ Password has been RESET to 'password123'")
    else:
        print("✗ Program Head NOT found - creating...")
        ph_cs = User(
            username='ph_cs',
            email='ph.cs@university.edu',
            full_name='Dr. James Wilson',
            role='program_head',
            department='Computer Science',
            is_active=True
        )
        ph_cs.set_password('password123')
        db.session.add(ph_cs)
        db.session.commit()
        print("  ✓ Program Head created with username 'ph_cs', password 'password123'")
    
    print("\n" + "=" * 50)
    print("LOGIN CREDENTIALS:")
    print("=" * 50)
    print("Admin:        admin / admin123")
    print("Dean:         dean / password123")
    print("Program Head: ph_cs / password123")
    print("Student:      student1 / password123")
    print("BSIT Student: bsit307_student1 / password123")