# check_program_head.py
from app import app
from models import db, User

with app.app_context():
    program_heads = User.query.filter_by(role='program_head').all()
    
    print("Program Heads in database:")
    for ph in program_heads:
        print(f"  - Username: {ph.username}")
        print(f"    Department: {ph.department}")
        print(f"    Full Name: {ph.full_name}")
        print(f"    Is Active: {ph.is_active}")
        print()
    
    if not program_heads:
        print("No program heads found! Creating one...")
        ph = User(
            username='ph_cs',
            email='ph.cs@university.edu',
            full_name='Dr. James Wilson',
            role='program_head',
            department='Computer Science',
            is_active=True
        )
        ph.set_password('password123')
        db.session.add(ph)
        db.session.commit()
        print(f"Created program head: ph_cs / password123")