# add_program_heads.py
from app import app
from models import db, User, Program, Teacher

def add_program_heads():
    with app.app_context():
        print("=" * 60)
        print("ADDING PROGRAM HEADS FOR ALL DEPARTMENTS")
        print("=" * 60)
        
        # Define program heads for each department
        program_heads_data = [
            {
                'username': 'ph_ccs',
                'email': 'ph.ccs@university.edu',
                'full_name': 'Dr. Maria Santos',
                'role': 'program_head',
                'department': 'Computer Science',
                'password': 'password123'
            },
            {
                'username': 'ph_entrep',
                'email': 'ph.entrep@university.edu',
                'full_name': 'Dr. Jose Reyes',
                'role': 'program_head',
                'department': 'Entrepreneurship',
                'password': 'password123'
            },
            {
                'username': 'ph_fm',
                'email': 'ph.fm@university.edu',
                'full_name': 'Dr. Anna Cruz',
                'role': 'program_head',
                'department': 'Financial Management',
                'password': 'password123'
            }
        ]
        
        created_count = 0
        for ph_data in program_heads_data:
            # Check if user already exists
            existing = User.query.filter_by(username=ph_data['username']).first()
            
            if existing:
                print(f"Program head {ph_data['username']} already exists")
                # Update department if needed
                if existing.department != ph_data['department']:
                    existing.department = ph_data['department']
                    db.session.commit()
                    print(f"  → Updated department to {ph_data['department']}")
            else:
                # Create new program head
                new_ph = User(
                    username=ph_data['username'],
                    email=ph_data['email'],
                    full_name=ph_data['full_name'],
                    role='program_head',
                    department=ph_data['department'],
                    is_active=True
                )
                new_ph.set_password(ph_data['password'])
                db.session.add(new_ph)
                created_count += 1
                print(f"✓ Created program head: {ph_data['username']} ({ph_data['department']})")
        
        db.session.commit()
        
        print("\n" + "=" * 60)
        print(f"✅ Added/Updated {created_count} program heads")
        print("=" * 60)
        
        # Show all program heads
        print("\n📋 PROGRAM HEADS IN SYSTEM:")
        print("-" * 40)
        program_heads = User.query.filter_by(role='program_head').all()
        for ph in program_heads:
            print(f"  {ph.username:15} → {ph.department:25} → {ph.full_name}")
        
        print("\n🔐 LOGIN CREDENTIALS:")
        print("-" * 40)
        for ph_data in program_heads_data:
            print(f"  {ph_data['username']:15} / password123")
        
        print("\n" + "=" * 60)

if __name__ == '__main__':
    add_program_heads()