# check_ph_only.py
from app import app, db
from models import User

with app.app_context():
    print("Program Heads in database:")
    ph_users = User.query.filter_by(role='program_head').all()
    if ph_users:
        for ph in ph_users:
            print(f"  - {ph.username} ({ph.department})")
    else:
        print("  No program heads found")
    
    print(f"\nTotal program heads: {len(ph_users)}")